import json
import logging
from db_config import get_connection

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

CORS_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "https://fims.store",
    "Access-Control-Allow-Methods": "OPTIONS,GET,POST",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    "Access-Control-Allow-Credentials": "true"
}

def handler(event, context):
    logger.debug("Orders event: %s", event)
    method = event.get("httpMethod")

    if method == "OPTIONS":
        return {"statusCode": 200, "headers": CORS_HEADERS, "body": ""}

    conn = None
    try:
        conn = get_connection()
        cur  = conn.cursor(dictionary=True)

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
            for r in rows:
                od = r.get("order_date")
                if hasattr(od, "isoformat"):
                    r["order_date"] = od.isoformat()
            body   = json.dumps(rows)
            status = 200

        elif method == "POST":
            data = json.loads(event.get("body") or "{}")
            cur.execute(
                "INSERT INTO orders (supplier_id, fabric_id, quantity) VALUES (%s, %s, %s)",
                (data["supplier_id"], data["fabric_id"], data["quantity"])
            )
            conn.commit()
            body   = json.dumps({ "order_id": cur.lastrowid })
            status = 201

        else:
            return {
                "statusCode": 405,
                "headers": CORS_HEADERS,
                "body": json.dumps({ "error": "Method not allowed" })
            }

        return {"statusCode": status, "headers": CORS_HEADERS, "body": body}

    except Exception as e:
        logger.exception("Orders handler failed")
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({ "error": str(e) })
        }

    finally:
        if conn:
            conn.close()