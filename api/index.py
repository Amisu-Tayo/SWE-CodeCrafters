# api/index.py

import os
from flask import Flask, jsonify
from api.db_config import get_connection

app = Flask(__name__)
app.secret_key = os.getenv("SESSION_SECRET", "dev-secret")  # only needed if you use sessions here

# ── Inventory ───────────────────────────────────────────────────────
@app.route("/api/inventory", methods=["GET"])
def get_inventory():
    conn = get_connection()
    cur  = conn.cursor(dictionary=True)
    cur.execute("""
      SELECT fabric_id,
             fabric_type,
             color,
             quantity,
             price_per_unit,
             restock_threshold
        FROM fabric_inventory
    """)
    rows = cur.fetchall()
    conn.close()
    return jsonify(rows)

# ── Orders ──────────────────────────────────────────────────────────
@app.route("/api/orders", methods=["GET"])
def get_orders():
    conn = get_connection()
    cur  = conn.cursor(dictionary=True)
    cur.execute("""
      SELECT order_id,
             supplier_id,
             fabric_id,
             quantity,
             order_date,
             status
        FROM orders
    """)
    rows = cur.fetchall()
    conn.close()
    return jsonify(rows)

# ── Usage ───────────────────────────────────────────────────────────
@app.route("/api/usage", methods=["GET"])
def get_usage():
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
      SELECT SUM(quantity_changed) AS monthly_usage
        FROM stock_transactions
       WHERE transaction_type = 'Removal'
         AND transaction_date >= DATE_SUB(NOW(), INTERVAL 30 DAY)
    """)
    result = cur.fetchone()
    conn.close()
    usage = (result['monthly_usage'] if isinstance(result, dict) else result[0]) or 0
    return jsonify(monthly_usage=usage)

# ── Reports ─────────────────────────────────────────────────────────
@app.route("/api/reports", methods=["GET"])
def get_reports():
    conn = get_connection()
    cur  = conn.cursor(dictionary=True)
    cur.execute("""
      SELECT report_id,
             generated_by,
             report_date,
             report_data
        FROM sales_reports
       ORDER BY report_date DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return jsonify(rows)

# ── Entry Point ─────────────────────────────────────────────────────
# Vercel’s Python builder will detect `app` and deploy it as a single function.
if __name__ == "__main__":
    app.run()