import os
import pickle
from flask import Flask, jsonify, request
import aws_serverless_wsgi
from api.db_config import get_connection

app = Flask(__name__)

# Lazy load Prophet models to avoid long cold-start times
MODELS = {}

def load_models():
    """
    Load all .pkl Prophet model files into the global MODELS dict.
    Called on first request to defer expensive I/O.
    """
    model_dir = os.path.join(os.getcwd(), "models")
    for fn in os.listdir(model_dir):
        if fn.endswith(".pkl"):
            key = fn[:-4].strip().lower()
            path = os.path.join(model_dir, fn)
            try:
                with open(path, "rb") as f:
                    MODELS[key] = pickle.load(f)
            except Exception as e:
                print(f"Error loading model {fn}: {e}")

@app.route("/api/fimai", methods=["GET"])
def fimai():
    # Load models on first invocation
    if not MODELS:
        load_models()

    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT fabric_type, quantity, restock_threshold FROM fabric_inventory")
    inv = cur.fetchall()
    conn.close()

    out = []
    for row in inv:
        ft = row["fabric_type"].strip().lower()
        qty, thr = row["quantity"], row["restock_threshold"]
        model = MODELS.get(ft)
        if model:
            # Forecast next 12 months
            future = model.make_future_dataframe(periods=12, freq="M")
            forecast = model.predict(future)
            next_year = forecast.iloc[-12:]
            peak_idx = next_year['yhat'].idxmax()
            peak_row = next_year.loc[peak_idx]
            peak_month = peak_row['ds'].strftime('%B')
            peak_val = int(peak_row['yhat'])

            # Tailored advice
            if qty < thr:
                advice = (
                    f"You're below your restock threshold ({thr}). "
                    f"Consider reordering before {peak_month}."
                )
            elif qty > peak_val:
                advice = (
                    f"You have more stock ({qty}) than the forecasted peak ({peak_val}). "
                    "You could cancel or reduce upcoming restock."
                )
            else:
                advice = f"Your stock should hold until around {peak_month}."

            msg = (
                f"{ft.title()} typically peaks in {peak_month}. "
                f"You currently have {qty} yards. {advice}"
            )
        else:
            msg = f"No model for {ft}. Monitor this SKU closely."
        out.append(msg)

    return jsonify(out)

@app.route("/api/fimai/chat", methods=["POST"])
def chat():
    # Ensure models loaded for forecast queries
    if not MODELS:
        load_models()

    data = request.get_json() or {}
    question = data.get("message", "").lower()

    # 1) Quantity lookup: "how many ... <fabric>"
    if "how many" in question:
        for fabric in MODELS.keys():
            if fabric in question:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute(
                    "SELECT quantity FROM fabric_inventory WHERE LOWER(fabric_type)=%s",
                    (fabric,)  
                )
                row = cur.fetchone()
                conn.close()
                if row:
                    qty = row[0]
                    return jsonify({"response": f"You have {qty} yards of {fabric} in stock."})
                else:
                    return jsonify({"response": f"I don't see any record for {fabric}."})

    # 2) Forecast request: "when should I reorder <fabric>?"
    for fabric in MODELS.keys():
        if fabric in question:
            model = MODELS[fabric]
            future = model.make_future_dataframe(periods=1, freq="M")
            forecast = model.predict(future)
            yhat = int(forecast.iloc[-1]["yhat"])
            month = forecast.iloc[-1]["ds"].strftime("%B")

            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                "SELECT quantity FROM fabric_inventory WHERE LOWER(fabric_type)=%s",
                (fabric,)
            )
            row = cur.fetchone()
            conn.close()
            qty = row[0] or 0

            msg = f"In {month}, you'll sell ~{yhat} yards of {fabric}. "
            msg += "Consider reordering." if yhat > qty else "Stock should hold."

            return jsonify({"response": msg})

    conn = get_connection()
    cur = conn.cursor()

    # 3) Total items
    if "total items" in question or ("how many" in question and "items" in question):
        cur.execute("SELECT COUNT(*) FROM fabric_inventory")
        count = cur.fetchone()[0]
        answer = f"You have {count} items in inventory."

    # 4) Low stock
    elif "low stock" in question or "restock" in question:
        cur.execute(
            "SELECT fabric_type FROM fabric_inventory WHERE quantity < restock_threshold"
        )
        low = [r[0] for r in cur.fetchall()]
        answer = low and f"Low stock for: {', '.join(low)}." or "All items above threshold."

    # 5) Monthly usage / sales
    elif "usage" in question or "sold" in question:
        cur.execute(
            """
            SELECT SUM(quantity_changed) FROM stock_transactions
            WHERE transaction_type='Removal'
              AND transaction_date >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            """
        )
        total = cur.fetchone()[0] or 0
        answer = f"You sold {total} yards in the last 30 days."

    else:
        answer = "Sorry, I don't know how to answer that yet."

    conn.close()
    return jsonify({"response": answer})

# Mangum adapter
def handler(event, context):
    # Set the environment variable for the AWS region
    #os.environ["AWS_REGION"] = os.getenv("AWS_REGION", "us-east-1")
    return aws_serverless_wsgi.handle_request(app, event, context)

