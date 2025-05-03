# api/fimai.py
import os, pickle
from flask import Flask, jsonify
from mangum import Mangum
from api.db_config import get_connection

app = Flask(__name__)

# Load all your pickles once at cold-start
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
    cur.execute("SELECT fabric_type, quantity, restock_threshold FROM fabric_inventory")
    inv = cur.fetchall()
    conn.close()

    out = []
    for row in inv:
        ft = row["fabric_type"].strip().lower()
        qty, thr = row["quantity"], row["restock_threshold"]
        model = MODELS.get(ft)
        if model:
            future  = model.make_future_dataframe(periods=1, freq="M")
            forecast= model.predict(future)
            yhat    = int(forecast.iloc[-1]["yhat"])
            msg     = (f"In {forecast.iloc[-1]['ds'].strftime('%B')}, "
                       f"you’ll sell ~{yhat} yards of {ft}. "
                       f"You have {qty} now.")
            if yhat > qty:
                msg += " Consider reordering."
        else:
            msg = f"No model for {ft}. Monitor this sku closely."
        out.append(msg)
    return jsonify(out)

# Mangum adapter
handler = Mangum(app)