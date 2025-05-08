import os
# Force Matplotlib to use a writable cache dir **before** it’s imported
os.environ["MPLCONFIGDIR"] = "/tmp/.matplotlib"

import pickle
import json
import re
from datetime import datetime
import pandas as pd
from dateutil.relativedelta import relativedelta
from flask import Flask, jsonify, request, make_response
from flask_cors import cross_origin
from flask_cors import CORS
from asgiref.wsgi import WsgiToAsgi
from mangum import Mangum
from db_config import get_connection

app = Flask(__name__)
CORS(app, 
     resources={r"/api/*": {"origins": ["https://fims.store"]}},
     supports_credentials=True)
     

MODELS = {}
TRENDS = {}

def load_models_and_trends():
    model_dir = os.path.join(os.getcwd(), "models")
    for fn in os.listdir(model_dir):
        if fn.endswith(".pkl"):
            key = fn[:-4].lower()
            if key not in MODELS:
                with open(os.path.join(model_dir, fn), "rb") as f:
                    MODELS[key] = pickle.load(f)
    trends_path = os.path.join(model_dir, "trends.json")
    if os.path.exists(trends_path) and not TRENDS:
        with open(trends_path) as f:
            TRENDS.update(json.load(f))

def get_top_trends(month_idx, top_n=3):
    scores = [(fab, data.get(str(month_idx), 1.0)) for fab, data in TRENDS.items()]
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
    try:
        load_models_and_trends()

        # 1) aggregate inventory by fabric_type
        conn = get_connection()
        cur  = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT
              LOWER(fabric_type) AS fabric_type,
              SUM(quantity)          AS quantity,
              MAX(restock_threshold) AS restock_threshold
            FROM fabric_inventory
            GROUP BY LOWER(fabric_type)
        """)
        agg = cur.fetchall()
        conn.close()

        now       = datetime.utcnow()
        month_idx = now.month
        mon_name  = now.strftime("%B")

        # if no inventory at all, fall back to pure trend tips
        if not agg:
            top = get_top_trends(month_idx)
            return jsonify([
                f"It’s {mon_name}: interest in {fab} is "
                f"{abs(int((factor-1)*100))}% "
                f"{'above' if factor>1 else 'below'} average. "
                "Consider adding stock."
                for fab, factor in top
            ])

        out = []
        for row in agg:
            ft  = row["fabric_type"]
            qty = row["quantity"]
            thr = row["restock_threshold"]

            # Forecast for the **current** month:
            # e.g. if today is May 12, we forecast for 1st of May
            forecast_month = now.replace(day=1)
            future         = pd.DataFrame({"ds": [forecast_month]})
            model          = MODELS.get(ft)
            yhat           = None
            if model:
                fc = model.predict(future)
                yhat = int(fc.loc[0, "yhat"])

            # build up any alerts
            parts = []
            if qty < thr:
                parts.append(f"⚠️ Below restock threshold ({thr}).")
            if yhat is not None and yhat > qty:
                parts.append(f"🔮 Forecast {yhat} > stock {qty}.")
            # strong seasonal spike
            factor = TRENDS.get(ft, {}).get(str(month_idx), 1.0)
            if factor > 1.2:
                parts.append(f"📈 Searches {int((factor-1)*100)}% above avg.")
            elif factor < 0.8:
                parts.append(f"📉 Searches {int((1-factor)*100)}% below avg.")

            if parts:
                # format one message per fabric
                msg = (
                    f"{ft.title()} for {mon_name}: you have {qty} yards"
                    + (f", forecast ~{yhat} yards." if yhat is not None else ".")
                    + " " + " ".join(parts)
                )
                out.append(msg)

        return jsonify(out)

    except Exception:
        app.logger.exception("FIMAI error")
        return jsonify([
            "Unable to fetch suggestions; please check the backend.",
            "Demo tip: always keep your stock above restock threshold!"
        ]), 500
       
@app.route("/api/fimai/chat", methods=["POST"])
@cross_origin(origins="https://fims.store", supports_credentials=True)
def chat():
    try:
        load_models_and_trends()
        payload = request.get_json(silent=True) or {}
        q = payload.get("message", "").lower()
        fabrics = get_all_fabrics()

        if not fabrics:
            return jsonify(response="No fabrics yet; add some SKUs first.")

        # Handle quantity inquiries
        if re.search(r"\bhow many\b", q) or "quantity" in q:
            for ft in fabrics:
                if ft in q:
                    conn = get_connection()
                    cur  = conn.cursor()
                    cur.execute(
                        "SELECT quantity FROM fabric_inventory WHERE LOWER(fabric_type)=%s",
                        (ft,)
                    )
                    row = cur.fetchone()
                    conn.close()
                    qty = row[0] if row else 0
                    return jsonify(response=f"You have {qty} yards of {ft}.")

        # Handle forecast inquiries
        if any(k in q for k in ["sell", "forecast"]):
            for ft in fabrics:
                if ft in q and ft in MODELS:
                    model = MODELS[ft]
                    last_date = model.history["ds"].max()
                    next_date = last_date + relativedelta(months=1)
                    future    = pd.DataFrame({"ds": [next_date]})
                    pred      = model.predict(future).iloc[0]
                    yhat      = int(pred["yhat"])
                    mon       = next_date.strftime("%B")
                    return jsonify(response=f"In {mon}, you’ll sell ~{yhat} yards of {ft}.")

        conn = get_connection()
        cur  = conn.cursor()

        # Handle total SKUs inquiry
        if "total items" in q or ("how many" in q and "items" in q):
            cur.execute("SELECT COUNT(*) FROM fabric_inventory")
            cnt = cur.fetchone()[0]
            conn.close()
            return jsonify(response=f"You have {cnt} SKUs.")

        # Handle low stock inquiry
        if "low stock" in q or "restock" in q:
            cur.execute(
                "SELECT fabric_type FROM fabric_inventory WHERE quantity < restock_threshold"
            )
            low = [r[0] for r in cur.fetchall()]
            conn.close()
            if low:
                return jsonify(response="Low stock: " + ", ".join(low))
            return jsonify(response="All SKUs above threshold.")

        # Handle recent usage inquiry
        if "usage" in q or "sold" in q:
            cur.execute(
                "SELECT SUM(quantity_changed) FROM stock_transactions "
                "WHERE transaction_type='Removal' "
                "  AND transaction_date >= DATE_SUB(NOW(), INTERVAL 30 DAY)"
            )
            total = cur.fetchone()[0] or 0
            conn.close()
            return jsonify(response=f"Sold {total} yards in last 30 days.")

        return jsonify(response="Sorry, I didn’t understand that.")

    except Exception:
        app.logger.exception("CHAT error")
        return jsonify(response="Chat temporarily unavailable; try again."), 500

# Wrap and export
asgi_app = WsgiToAsgi(app)
handler  = Mangum(asgi_app, lifespan="off")
