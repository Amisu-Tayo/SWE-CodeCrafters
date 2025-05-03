# lambda_src/api/fimai.py

import os
import pickle
from flask import Flask, jsonify, request
from mangum import Mangum
from api.db_config import get_connection

app = Flask(__name__)

# Load all your Prophet models once at cold-start
MODELS = {}
model_dir = os.path.join(os.getcwd(), "models")
for fn in os.listdir(model_dir):
    if fn.endswith(".pkl"):
        key = fn[:-4]  # e.g. "cotton"
        with open(os.path.join(model_dir, fn), "rb") as f:
            MODELS[key] = pickle.load(f)

@app.route("/api/fimai", methods=["GET"])
def fimai():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        "SELECT fabric_type, quantity, restock_threshold FROM fabric_inventory"
    )
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
            # Consider only the last 12 forecast points
            next_year = forecast.iloc[-12:]
            # Find the peak month
            peak_idx = next_year['yhat'].idxmax()
            peak_row = next_year.loc[peak_idx]
            peak_month = peak_row['ds'].strftime('%B')
            peak_val = int(peak_row['yhat'])

            # Generate dynamic advice
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
    data = request.get_json() or {}
    question = data.get("message", "").lower()

    conn = get_connection()
    cur = conn.cursor()

    # Simple keyword-based query handling
    if "total skus" in question or "how many skus" in question:
        cur.execute("SELECT COUNT(*) FROM fabric_inventory")
        count = cur.fetchone()[0]
        answer = f"You have {count} SKUs in inventory."
    elif "low stock" in question or "restock" in question:
        cur.execute(
            "SELECT fabric_type FROM fabric_inventory WHERE quantity < restock_threshold"
        )
        low = [r[0] for r in cur.fetchall()]
        if low:
            answer = f"Low stock for: {', '.join(low)}."
        else:
            answer = "All items are above their restock thresholds."
    else:
        answer = "Sorry, I don't know how to answer that yet."

    conn.close()
    return jsonify({"response": answer})

# Mangum adapter
handler = Mangum(app)
