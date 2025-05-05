import json
import logging
import decimal
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

def _decimal_default(obj):
    if isinstance(obj, decimal.Decimal):
        n = float(obj)
        return int(n) if obj % 1 == 0 else n
    raise TypeError

def handler(event, context):
    logger.debug("Inventory event: %s", event)
    method = event.get("httpMethod")

    if method == "OPTIONS":
        return {"statusCode": 200, "headers": CORS_HEADERS, "body": ""}

    conn = None
    try:
        conn = get_connection()
        cur  = conn.cursor(dictionary=True)

        if method == "GET":
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
            body = json.dumps(rows, default=_decimal_default)
            status = 200

        elif method == "POST":
            data = json.loads(event.get("body") or "{}")
            cur.execute(
                """
                INSERT INTO fabric_inventory
                  (fabric_type, color, quantity, price_per_unit, restock_threshold)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    data["fabric_type"],
                    data["color"],
                    data["quantity"],
                    data["price_per_unit"],
                    data["restock_threshold"]
                )
            )
            conn.commit()
            body = json.dumps({ "fabric_id": cur.lastrowid })
            status = 201

        else:
            return {
                "statusCode": 405,
                "headers": CORS_HEADERS,
                "body": json.dumps({ "error": "Method not allowed" })
            }

        return {"statusCode": status, "headers": CORS_HEADERS, "body": body}

    except Exception as e:
        logger.exception("Inventory handler failed")
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({ "error": str(e) })
        }

    finally:
        if conn:
            conn.close()