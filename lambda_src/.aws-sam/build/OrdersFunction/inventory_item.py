import json
import logging
from db_config import get_connection

# Set up logging so we see errors in CloudWatch
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def handler(event, context):
    logger.debug("InventoryItem event: %s", event)
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        fid = int(event["pathParameters"]["fid"])
        method = event.get("httpMethod")

        if method == "PUT":
            data = json.loads(event.get("body") or "{}")
            cur.execute(
                """
                UPDATE fabric_inventory
                   SET fabric_type=%s,
                       color=%s,
                       quantity=%s,
                       price_per_unit=%s,
                       restock_threshold=%s
                 WHERE fabric_id=%s
                """,
                (
                    data.get("fabric_type"),
                    data.get("color"),
                    data.get("quantity"),
                    data.get("price_per_unit"),
                    data.get("restock_threshold"),
                    fid
                )
            )
            conn.commit()
            status_code = 200
            body = {"ok": True}

        elif method == "DELETE":
            cur.execute(
                "DELETE FROM fabric_inventory WHERE fabric_id=%s",
                (fid,)
            )
            conn.commit()
            status_code = 200
            body = {"ok": True}

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
        logger.exception("InventoryItem handler failed")
        return {
            "statusCode": 500,
            "headers": { "Content-Type": "application/json" },
            "body": json.dumps({ "error": str(e) })
        }

    finally:
        if conn:
            conn.close()