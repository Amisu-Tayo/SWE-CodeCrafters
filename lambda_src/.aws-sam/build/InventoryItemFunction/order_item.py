import json
import logging
from db_config import get_connection

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

CORS_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "https://fims.store",
    "Access-Control-Allow-Methods": "OPTIONS,PUT,DELETE",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    "Access-Control-Allow-Credentials": "true"
}

def handler(event, context):
    logger.debug("OrderItem event: %s", event)
    method = event.get("httpMethod")

    if method == "OPTIONS":
        return {"statusCode": 200, "headers": CORS_HEADERS, "body": ""}

    conn = None
    try:
        conn = get_connection()
        cur  = conn.cursor()
        oid  = int(event["pathParameters"]["oid"])

        if method == "PUT":
            data = json.loads(event.get("body") or "{}")
            cur.execute(
                "UPDATE orders SET status=%s WHERE order_id=%s",
                (data.get("status"), oid)
            )
            conn.commit()
            body = { "ok": True }

        elif method == "DELETE":
            cur.execute(
                "DELETE FROM orders WHERE order_id=%s",
                (oid,)
            )
            conn.commit()
            body = { "ok": True }

        else:
            return {
                "statusCode": 405,
                "headers": CORS_HEADERS,
                "body": json.dumps({ "error": "Method not allowed" })
            }

        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": json.dumps(body)
        }

    except Exception as e:
        logger.exception("OrderItem handler failed")
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({ "error": str(e) })
        }

    finally:
        if conn:
            conn.close()