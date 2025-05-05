import json
import logging
from db_config import get_connection

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

CORS_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "https://fims.store",
    "Access-Control-Allow-Methods": "OPTIONS,GET,PUT,DELETE",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    "Access-Control-Allow-Credentials": "true"
}

def handler(event, context):
    logger.debug("InventoryItem event: %s", event)
    method = event.get("httpMethod")

    if method == "OPTIONS":
        return {"statusCode": 200, "headers": CORS_HEADERS, "body": ""}

    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        fid = int(event["pathParameters"]["fid"])

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
            status = 200
            body   = { "ok": True }

        elif method == "DELETE":
            cur.execute(
                "DELETE FROM fabric_inventory WHERE fabric_id=%s",
                (fid,)
            )
            conn.commit()
            status = 200
            body   = { "ok": True }

        else:
            return {
                "statusCode": 405,
                "headers": CORS_HEADERS,
                "body": json.dumps({ "error": "Method not allowed" })
            }

        return {
            "statusCode": status,
            "headers": CORS_HEADERS,
            "body": json.dumps(body)
        }

    except Exception as e:
        logger.exception("InventoryItem handler failed")
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({ "error": str(e) })
        }

    finally:
        if conn:
            conn.close()