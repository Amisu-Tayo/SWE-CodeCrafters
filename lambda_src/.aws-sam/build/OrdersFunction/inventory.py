import json
from api.db_config import get_connection

def handler(event, context):
    conn = get_connection()
    cur  = conn.cursor(dictionary=True)
    try:
        if event["httpMethod"] == "GET":
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
            return {
                "statusCode": 200,
                "headers": { "Content-Type": "application/json" },
                "body": json.dumps(rows)
            }

        elif event["httpMethod"] == "POST":
            data = json.loads(event.get("body") or "{}")
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
            return {
                "statusCode": 201,
                "headers": { "Content-Type": "application/json" },
                "body": json.dumps({ "fabric_id": new_id })
            }

        else:
            return { "statusCode": 405, "body": "" }

    finally:
        conn.close()