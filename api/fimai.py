
import os
import pickle
from flask import Flask, jsonify
from api.db_config import get_connection

app = Flask(__name__)

# 1) At startup, load all models into memory
MODELS = {}
models_dir = os.path.join(os.getcwd(), "models")
for fname in os.listdir(models_dir):
    if fname.endswith(".pkl"):
        fabric = fname.replace(".pkl", "")
        path   = os.path.join(models_dir, fname)
        with open(path, "rb") as f:
            MODELS[fabric] = pickle.load(f)

@app.route("/api/fimai", methods=["GET"])
def fimai():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT fabric_type, quantity, restock_threshold
          FROM fabric_inventory
    """)
    inventory = cursor.fetchall()
    conn.close()

    suggestions = []
    for row in inventory:
        ftype = row["fabric_type"].strip().lower()
        qty   = row["quantity"]
        thresh = row["restock_threshold"]
        model = MODELS.get(ftype)

        if model:
            # Forecast one period ahead
            future = model.make_future_dataframe(periods=1, freq="M")
            forecast = model.predict(future)
            yhat = int(forecast.iloc[-1]["yhat"])

            msg = (
                f"In {forecast.iloc[-1]['ds'].strftime('%B')}, "
                f"you’re forecasted to sell ~{yhat} yards of {ftype}. "
                f"You currently have {qty} in stock."
            )
            if yhat > qty:
                msg += " Consider reordering soon."
        else:
            msg = (
                f"No model for {ftype}. In general, plan for seasonality "
                "and monitor stock levels closely."
            )

        suggestions.append(msg)

    return jsonify(suggestions)