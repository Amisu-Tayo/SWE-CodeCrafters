import os
import pickle
import json
import re
from datetime import datetime
from flask import Flask, jsonify, request
import awsgi
from api.db_config import get_connection

app = Flask(__name__)

# —————————————————————————————————————
# GLOBAL STATE
# —————————————————————————————————————
MODELS = {}
TRENDS = {}

def load_models_and_trends():
    """Load Prophet .pkl models and trends.json exactly once."""
    model_dir = os.path.join(os.getcwd(), "models")

    # Load .pkl Prophet models
    for fn in os.listdir(model_dir):
        if fn.endswith(".pkl"):
            key = fn[:-4].strip().lower()
            if key not in MODELS:
                try:
                    with open(os.path.join(model_dir, fn), "rb") as f:
                        MODELS[key] = pickle.load(f)
                except Exception as e:
                    print(f"Error loading {fn}: {e}")

    # Load trend factors
    trends_path = os.path.join(model_dir, "trends.json")
    if os.path.exists(trends_path) and not TRENDS:
        try:
            with open(trends_path) as f:
                TRENDS.update(json.load(f))
        except Exception as e:
            print(f"Error loading trends.json: {e}")

def get_top_trends(month_idx, top_n=3):
    """Return top_n fabrics sorted by trend factor for given month."""
    scores = [
        (fabric, data.get(str(month_idx), 1.0))
        for fabric, data in TRENDS.items()
    ]
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:top_n]

def get_all_fabrics():
    """Fetch all fabric_type values (lowercased) from DB."""
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT DISTINCT fabric_type FROM fabric_inventory")
    fabrics = [r[0].strip().lower() for r in cur.fetchall()]
    conn.close()
    return fabrics

# —————————————————————————————————————
# 1) FORECAST + SEASONAL TIPS
# —————————————————————————————————————
@app.route("/api/fimai", methods=["GET"])
def fimai():
    load_models_and_trends()

    # fetch inventory
    conn = get_connection()
    cur  = conn.cursor(dictionary=True)
    cur.execute("""
      SELECT fabric_type, quantity, restock_threshold
        FROM fabric_inventory
    """)
    inv = cur.fetchall()
    conn.close()

    # determine month
    now        = datetime.utcnow()
    month_idx  = now.month
    month_name = now.strftime("%B")

    # no inventory → top trends
    if not inv:
        top = get_top_trends(month_idx, top_n=3)
        msgs = [
            (f"It’s {month_name}: interest in {fab} is "
             f"{abs(int((factor-1)*100))}% "
             f"{'above' if factor>1 else 'below'} your average. "
             "Consider adding stock to capitalize on this trend.")
            for fab, factor in top
        ]
        return jsonify(msgs)

    # have inventory → forecasts + tips
    out = []
    for row in inv:
        ft  = row["fabric_type"].strip().lower()
        qty = row["quantity"]
        thr = row["restock_threshold"]
        model = MODELS.get(ft)

        if model:
            # forecast next month
            future   = model.make_future_dataframe(periods=1, freq="M")
            forecast = model.predict(future)
            yhat     = int(forecast.iloc[-1]["yhat"])
            next_mon = forecast.iloc[-1]["ds"].strftime("%B")

            # basic advice
            if qty < thr:
                advice = f"Below restock threshold ({thr}); reorder before {next_mon}."
            elif qty > yhat:
                advice = f"Stock ({qty}) exceeds forecast ({yhat}); consider delaying restock."
            else:
                advice = f"Stock should cover through {next_mon}."

            msg = f"{ft.title()} forecast for {next_mon}: ~{yhat} yards. You have {qty}. {advice}"
        else:
            msg = f"No model for {ft}. Monitor this SKU closely."

        # append seasonal tip
        factor = TRENDS.get(ft, {}).get(str(month_idx), 1.0)
        if factor != 1.0:
            pct = abs(int((factor - 1) * 100))
            rel = "above" if factor > 1 else "below"
            msg += f" Tip: {ft.title()} searches are {pct}% {rel} average in {month_name}."

        out.append(msg)

    return jsonify(out)

# —————————————————————————————————————
# 2) CHAT ENDPOINT
# —————————————————————————————————————
@app.route("/api/fimai/chat", methods=["POST"])
def chat():
    load_models_and_trends()

    q = (request.get_json() or {}).get("message", "").lower()
    fabrics = get_all_fabrics()

    # If inventory empty, prompt onboarding
    if not fabrics:
        return jsonify(response=(
            "I don’t see any fabrics yet. Add some SKUs in Inventory—"
            "then I can forecast or tell you stock levels!"
        ))

    # 1) Quantity inquiries
    if re.search(r"\bhow many\b", q) or "quantity" in q:
        for ft in fabrics:
            if ft in q:
                conn = get_connection()
                cur  = conn.cursor()
                cur.execute(
                    "SELECT quantity FROM fabric_inventory WHERE LOWER(fabric_type)=%s",
                    (ft,)
                )
                row = cur.fetchone(); conn.close()
                qty = row[0] if row else 0
                return jsonify(response=f"You have {qty} yards of {ft}.")

    # 2) Forecast inquiries
    if any(kw in q for kw in ["sell", "forecast", "forecasting"]):
        for ft in fabrics:
            if ft in q and ft in MODELS:
                model = MODELS[ft]
                future = model.make_future_dataframe(periods=1, freq="M")
                pred   = model.predict(future).iloc[-1]
                yhat   = int(pred["yhat"])
                mon    = pred["ds"].strftime("%B")
                return jsonify(response=f"In {mon}, you’ll sell ~{yhat} yards of {ft}.")

    # 3) General stats
    conn = get_connection()
    cur  = conn.cursor()

    if "total items" in q or ("how many" in q and "items" in q):
        cur.execute("SELECT COUNT(*) FROM fabric_inventory")
        cnt = cur.fetchone()[0]
        conn.close()
        return jsonify(response=f"You have {cnt} SKUs in inventory.")

    if "low stock" in q or "restock" in q:
        cur.execute(
            "SELECT fabric_type FROM fabric_inventory WHERE quantity < restock_threshold"
        )
        low = [r[0] for r in cur.fetchall()]
        conn.close()
        if low:
            return jsonify(response="Low stock: " + ", ".join(low))
        return jsonify(response="All SKUs are above their restock thresholds.")

    if "usage" in q or "sold" in q:
        cur.execute(
            "SELECT SUM(quantity_changed) "
            "FROM stock_transactions "
            "WHERE transaction_type='Removal' "
            "  AND transaction_date >= DATE_SUB(NOW(), INTERVAL 30 DAY)"
        )
        total = cur.fetchone()[0] or 0
        conn.close()
        return jsonify(response=f"Sold {total} yards in the last 30 days.")

    # 4) Fallback
    conn.close()
    return jsonify(response=(
        "Sorry, I didn’t understand that. Ask me how many yards you have of a fabric, "
        "or to forecast sales, or general stats like total items or low stock."
    ))

# —————————————————————————————————————
# 3) LAMBDA ENTRYPOINT via awsgi
# —————————————————————————————————————
def handler(event, context):
    return awsgi.response(app, event, context)