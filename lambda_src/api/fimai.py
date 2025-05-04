import os
import pickle
from flask import Flask, jsonify, request
import awsgi                       # AWS WSGI adapter for Lambda
from api.db_config import get_connection

app = Flask(__name__)

# Lazy-load Prophet models
MODELS = {}

def load_models():
    """Load all .pkl Prophet model files to MODELS dict."""
    model_dir = os.path.join(os.getcwd(), "models")
    for fn in os.listdir(model_dir):
        if fn.endswith(".pkl"):
            key = fn[:-4].strip().lower()
            try:
                with open(os.path.join(model_dir, fn), "rb") as f:
                    MODELS[key] = pickle.load(f)
            except Exception as e:
                print(f"Error loading {fn}: {e}")

@app.route("/api/fimai", methods=["GET"])
def fimai():
    if not MODELS:
        load_models()

    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT fabric_type, quantity, restock_threshold FROM fabric_inventory")
    inv = cur.fetchall()
    conn.close()

    out = []
    for row in inv:
        ft = row['fabric_type'].strip().lower()
        qty, thr = row['quantity'], row['restock_threshold']
        model = MODELS.get(ft)
        if model:
            future = model.make_future_dataframe(periods=12, freq='M')
            forecast = model.predict(future).iloc[-12:]
            peak = forecast.loc[forecast['yhat'].idxmax()]
            peak_month = peak['ds'].strftime('%B')
            peak_val = int(peak['yhat'])

            if qty < thr:
                advice = f"Below restock threshold ({thr}); reorder before {peak_month}."
            elif qty > peak_val:
                advice = f"Stock ({qty}) exceeds peak forecast ({peak_val}); consider reducing restock."
            else:
                advice = f"Stock should hold until around {peak_month}."

            msg = f"{ft.title()} peaks in {peak_month}. You have {qty} yards. {advice}"
        else:
            msg = f"No model for {ft}. Monitor this SKU closely."
        out.append(msg)

    return jsonify(out)

@app.route("/api/fimai/chat", methods=["POST"])
def chat():
    if not MODELS:
        load_models()

    q = (request.get_json() or {}).get('message', '').lower()

    # 1) Quantity check
    if 'how many' in q:
        for ft in MODELS:
            if ft in q:
                conn = get_connection(); cur = conn.cursor()
                cur.execute("SELECT quantity FROM fabric_inventory WHERE LOWER(fabric_type)=%s", (ft,))
                row = cur.fetchone(); conn.close()
                if row:
                    return jsonify({'response': f"You have {row[0]} yards of {ft}."})
                return jsonify({'response': f"No record for {ft}."})

    # 2) Forecast check
    for ft in MODELS:
        if ft in q:
            model = MODELS[ft]
            fut = model.make_future_dataframe(periods=1, freq='M')
            yhat = int(model.predict(fut).iloc[-1]['yhat'])
            month = model.predict(fut).iloc[-1]['ds'].strftime('%B')
            conn = get_connection(); cur = conn.cursor()
            cur.execute("SELECT quantity FROM fabric_inventory WHERE LOWER(fabric_type)=%s", (ft,))
            row = cur.fetchone(); conn.close()
            qty = row[0] if row else 0
            resp = f"In {month}, ~{yhat} yards of {ft}. " + ("Reorder." if yhat>qty else "Stock holds.")
            return jsonify({'response': resp})

    conn = get_connection(); cur = conn.cursor()
    if 'total items' in q or ('how many' in q and 'items' in q):
        cur.execute("SELECT COUNT(*) FROM fabric_inventory"); cnt = cur.fetchone()[0]; answer = f"You have {cnt} items."
    elif 'low stock' in q or 'restock' in q:
        cur.execute("SELECT fabric_type FROM fabric_inventory WHERE quantity < restock_threshold")
        low = [r[0] for r in cur.fetchall()]; answer = low and f"Low stock: {', '.join(low)}." or "All above."
    elif 'usage' in q or 'sold' in q:
        cur.execute(
            "SELECT SUM(quantity_changed) FROM stock_transactions WHERE transaction_type='Removal' AND transaction_date >= DATE_SUB(NOW(), INTERVAL 30 DAY)"
        )
        total = cur.fetchone()[0] or 0; answer = f"Sold {total} yards in last 30 days."
    else:
        answer = "Sorry, I don't understand."
    conn.close(); return jsonify({'response': answer})

# Lambda entry point

def handler(event, context):
    return awsgi.response(app, event, context)




