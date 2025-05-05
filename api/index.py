import os
from flask import Flask, jsonify, request
from api.db_config import get_connection

app = Flask(__name__)
app.secret_key = os.getenv("SESSION_SECRET", "dev-secret")


from flask import session

@app.route("/api/check_session", methods=["GET"])
def check_session():
    return jsonify({ "logged_in": session.get("_logged_in", False) })

# ── Inventory ───────────────────────────────────────────────────────

@app.route("/api/inventory", methods=["GET", "POST"])
def handle_inventory():
    conn = get_connection()
    cur  = conn.cursor(dictionary=True)

    if request.method == "GET":
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

    # POST → create a new inventory item
    data = request.get_json()
    sql = """
      INSERT INTO fabric_inventory
        (fabric_type, color, quantity, price_per_unit, restock_threshold)
      VALUES (%s, %s, %s, %s, %s)
    """
    params = (
      data["fabric_type"],
      data["color"],
      data["quantity"],
      data["price_per_unit"],
      data["restock_threshold"]
    )
    cur.execute(sql, params)
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return jsonify({ "fabric_id": new_id }), 201


@app.route("/api/inventory/<int:fid>", methods=["PUT", "DELETE"])
def handle_single_inventory(fid):
    conn = get_connection()
    cur  = conn.cursor()

    if request.method == "PUT":
        data = request.get_json()
        sql = """
          UPDATE fabric_inventory
             SET fabric_type=%s,
                 color=%s,
                 quantity=%s,
                 price_per_unit=%s,
                 restock_threshold=%s
           WHERE fabric_id=%s
        """
        params = (
          data["fabric_type"],
          data["color"],
          data["quantity"],
          data["price_per_unit"],
          data["restock_threshold"],
          fid
        )
        cur.execute(sql, params)
        conn.commit()
        conn.close()
        return jsonify({ "ok": True })

    # DELETE
    cur.execute("DELETE FROM fabric_inventory WHERE fabric_id=%s", (fid,))
    conn.commit()
    conn.close()
    return jsonify({ "ok": True })


# ── Orders ──────────────────────────────────────────────────────────

@app.route("/api/orders", methods=["GET", "POST"])
def handle_orders():
    conn = get_connection()
    cur  = conn.cursor(dictionary=True)

    if request.method == "GET":
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

    # POST → create a new order
    data = request.get_json()
    sql = """
      INSERT INTO orders (supplier_id, fabric_id, quantity)
      VALUES (%s, %s, %s)
    """
    params = (data["supplier_id"], data["fabric_id"], data["quantity"])
    cur.execute(sql, params)
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return jsonify({ "order_id": new_id }), 201


@app.route("/api/orders/<int:oid>", methods=["PUT", "DELETE"])
def handle_single_order(oid):
    conn = get_connection()
    cur  = conn.cursor()

    if request.method == "PUT":
        data = request.get_json()
        # typically allow updating status only
        cur.execute("UPDATE orders SET status=%s WHERE order_id=%s",
                    (data["status"], oid))
        conn.commit()
        conn.close()
        return jsonify({ "ok": True })

    # DELETE
    cur.execute("DELETE FROM orders WHERE order_id=%s", (oid,))
    conn.commit()
    conn.close()
    return jsonify({ "ok": True })


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

if __name__ == "__main__":
    # for local dev
    app.run(debug=True)