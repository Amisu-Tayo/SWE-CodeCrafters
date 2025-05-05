import json
import logging
import decimal
from db_config import get_connection

# Set up logging so we see errors in CloudWatch
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# helper for json.dumps to serialize Decimal → int/float
def _decimal_default(obj):
    if isinstance(obj, decimal.Decimal):
        # use int if no fractional part, else float
        n = float(obj)
        return int(n) if obj % 1 == 0 else n
    raise TypeError(f"Object of type {type(obj)} not serializable")

def handler(event, context):
    logger.debug("Inventory event: %s", event)
    conn = None
    try:
        conn = get_connection()
        cur  = conn.cursor(dictionary=True)

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
                "body": json.dumps(rows, default=_decimal_default)
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
            return {
                "statusCode": 405,
                "headers": { "Content-Type": "application/json" },
                "body": json.dumps({ "error": "Method not allowed" })
            }

    except Exception as e:
        # Log full stack trace
        logger.exception("Inventory handler failed")
        # Return the error in the body for quick debugging
        return {
            "statusCode": 500,
            "headers": { "Content-Type": "application/json" },
            "body": json.dumps({ "error": str(e) })
        }

    finally:
        if conn:
            conn.close()