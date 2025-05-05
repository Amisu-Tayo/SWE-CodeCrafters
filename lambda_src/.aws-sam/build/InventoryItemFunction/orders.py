import json
import logging
from db_config import get_connection

# Set up logging so we see errors in CloudWatch
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def handler(event, context):
    logger.debug("Orders event: %s", event)
    conn = None
    try:
        conn = get_connection()
        cur  = conn.cursor(dictionary=True)
        method = event.get("httpMethod")

        if method == "GET":
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
            status_code = 200
            body = rows

        elif method == "POST":
            data = json.loads(event.get("body") or "{}")
            cur.execute(
                "INSERT INTO orders (supplier_id, fabric_id, quantity) VALUES (%s, %s, %s)",
                (data["supplier_id"], data["fabric_id"], data["quantity"])
            )
            conn.commit()
            new_id = cur.lastrowid
            status_code = 201
            body = {"order_id": new_id}

        else:
            return {
                "statusCode": 405,
                "headers": { "Content-Type": "application/json" },
                "body": json.dumps({ "error": "Method not allowed" })
            }

        return {
            "statusCode": status_code,
            "headers": { "Content-Type": "application/json" },
            "body": json.dumps(body, default=str)
        }

    except Exception as e:
        logger.exception("Orders handler failed")
        return {
            "statusCode": 500,
            "headers": { "Content-Type": "application/json" },
            "body": json.dumps({ "error": str(e) })
        }

    finally:
        if conn:
            conn.close()
