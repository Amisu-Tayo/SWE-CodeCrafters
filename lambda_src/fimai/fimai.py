import os
import pickle
import json
import re
from datetime import datetime
from flask import Flask, jsonify, request, make_response
import awsgi
from db_config import get_connection

app = Flask(__name__)

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "https://fims.store",
    "Access-Control-Allow-Methods": "OPTIONS,GET,POST",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    "Access-Control-Allow-Credentials": "true"
}

@app.after_request
def add_cors(response):
    for k, v in CORS_HEADERS.items():
        response.headers[k] = v
    return response

@app.route("/api/fimai", methods=["OPTIONS"])
@app.route("/api/fimai/chat", methods=["OPTIONS"])
def options():
    return make_response(("", 200, CORS_HEADERS))

MODELS = {}
TRENDS = {}

def load_models_and_trends():
    model_dir = os.path.join(os.getcwd(), "models")
    for fn in os.listdir(model_dir):
        if fn.endswith(".pkl"):
            key = fn[:-4].strip().lower()
            if key not in MODELS:
                with open(os.path.join(model_dir, fn), "rb") as f:
                    MODELS[key] = pickle.load(f)
    trends_path = os.path.join(model_dir, "trends.json")
    if os.path.exists(trends_path) and not TRENDS:
        with open(trends_path) as f:
            TRENDS.update(json.load(f))

def get_top_trends(month_idx, top_n=3):
    scores = [(fabric, data.get(str(month_idx), 1.0)) for fabric, data in TRENDS.items()]
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:top_n]

def get_all_fabrics():
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT DISTINCT fabric_type FROM fabric_inventory")
    fabrics = [r[0].strip().lower() for r in cur.fetchall()]
    conn.close()
    return fabrics

@app.route("/api/fimai", methods=["GET"])
def fimai():
    load_models_and_trends()
    conn = get_connection()
    cur  = conn.cursor(dictionary=True)
    cur.execute("SELECT fabric_type, quantity, restock_threshold FROM fabric_inventory")
    inv = cur.fetchall()
    conn.close()
    now        = datetime.utcnow()
    month_idx  = now.month
    month_name = now.strftime("%B")
    if not inv:
        top = get_top_trends(month_idx, top_n=3)
        msgs = [
            f"It’s {month_name}: interest in {fab} is {abs(int((factor-1)*100))}% {'above' if factor>1 else 'below'} your average. Consider adding stock to capitalize on this trend."
            for fab, factor in top
        ]
        return jsonify(msgs)
    out = []
    for row in inv:
        ft  = row["fabric_type"].strip().lower()
        qty = row["quantity"]
        thr = row["restock_threshold"]
        model = MODELS.get(ft)
        if model:
            future   = model.make_future_dataframe(periods=1, freq="M")
            forecast = model.predict(future)
            yhat     = int(forecast.iloc[-1]["yhat"])
            next_mon = forecast.iloc[-1]["ds"].strftime("%B")
            if qty < thr:
                advice = f"Below restock threshold ({thr}); reorder before {next_mon}."
            elif qty > yhat:
                advice = f"Stock ({qty}) exceeds forecast ({yhat}); consider delaying restock."
            else:
                advice = f"Stock should cover through {next_mon}."
            msg = f"{ft.title()} forecast for {next_mon}: ~{yhat} yards. You have {qty}. {advice}"
        else:
            msg = f"No model for {ft}. Monitor this SKU closely."
        factor = TRENDS.get(ft, {}).get(str(month_idx), 1.0)
        if factor != 1.0:
            pct = abs(int((factor - 1) * 100))
            rel = "above" if factor > 1 else "below"
            msg += f" Tip: {ft.title()} searches are {pct}% {rel} average in {month_name}."
        out.append(msg)
    return jsonify(out)

@app.route("/api/fimai/chat", methods=["POST"])
def chat():
    load_models_and_trends()
    q = (request.get_json() or {}).get("message", "").lower()
    fabrics = get_all_fabrics()
    if not fabrics:
        return jsonify(response="I don’t see any fabrics yet. Add some SKUs in Inventory—then I can forecast or tell you stock levels!")
    if re.search(r"\bhow many\b", q) or "quantity" in q:
        for ft in fabrics:
            if ft in q:
                conn = get_connection()
                cur  = conn.cursor()
                cur.execute("SELECT quantity FROM fabric_inventory WHERE LOWER(fabric_type)=%s", (ft,))
                row = cur.fetchone(); conn.close()
                qty = row[0] if row else 0
                return jsonify(response=f"You have {qty} yards of {ft}.")
    if any(kw in q for kw in ["sell", "forecast", "forecasting"]):
        for ft in fabrics:
            if ft in q and ft in MODELS:
                model = MODELS[ft]
                future = model.make_future_dataframe(periods=1, freq="M")
                pred   = model.predict(future).iloc[-1]
                yhat   = int(pred["yhat"])
                mon    = pred["ds"].strftime("%B")
                return jsonify(response=f"In {mon}, you’ll sell ~{yhat} yards of {ft}.")
    conn = get_connection()
    cur  = conn.cursor()
    if "total items" in q or ("how many" in q and "items" in q):
        cur.execute("SELECT COUNT(*) FROM fabric_inventory")
        cnt = cur.fetchone()[0]; conn.close()
        return jsonify(response=f"You have {cnt} SKUs in inventory.")
    if "low stock" in q or "restock" in q:
        cur.execute("SELECT fabric_type FROM fabric_inventory WHERE quantity < restock_threshold")
        low = [r[0] for r in cur.fetchall()]; conn.close()
        if low:
            return jsonify(response="Low stock: " + ", ".join(low))
        return jsonify(response="All SKUs are above their restock thresholds.")
    if "usage" in q or "sold" in q:
        cur.execute("SELECT SUM(quantity_changed) FROM stock_transactions WHERE transaction_type='Removal' AND transaction_date >= DATE_SUB(NOW(), INTERVAL 30 DAY)")
        total = cur.fetchone()[0] or 0; conn.close()
        return jsonify(response=f"Sold {total} yards in the last 30 days.")
    conn.close()
    return jsonify(response="Sorry, I didn’t understand that. Ask me how many yards you have of a fabric, or to forecast sales, or general stats like total items or low stock.")

def handler(event, context):
    return awsgi.response(app, event, context)