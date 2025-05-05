import json
from db_config import get_connection

def handler(event, context):
    conn = get_connection()
    cur  = conn.cursor(dictionary=True)
    try:
        if event["httpMethod"] == "GET":
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
            return {
                "statusCode": 200,
                "headers": { "Content-Type": "application/json" },
                "body": json.dumps(rows)
            }

        elif event["httpMethod"] == "POST":
            data = json.loads(event.get("body") or "{}")
            sql = """
              INSERT INTO orders (supplier_id, fabric_id, quantity)
              VALUES (%s, %s, %s)
            """
            params = (
                data["supplier_id"],
                data["fabric_id"],
                data["quantity"]
            )
            cur.execute(sql, params)
            conn.commit()
            new_id = cur.lastrowid
            return {
                "statusCode": 201,
                "headers": { "Content-Type": "application/json" },
                "body": json.dumps({ "order_id": new_id })
            }

        else:
            return { "statusCode": 405, "body": "" }

    finally:
        conn.close()