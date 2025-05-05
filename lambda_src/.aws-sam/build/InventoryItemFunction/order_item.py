import json
import logging
from db_config import get_connection

# Set up logging so we see errors in CloudWatch
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def handler(event, context):
    logger.debug("OrderItem event: %s", event)
    conn = None
    try:
        conn = get_connection()
        cur  = conn.cursor()
        oid  = int(event["pathParameters"]["oid"])

        if event["httpMethod"] == "PUT":
            data = json.loads(event.get("body") or "{}")
            # usually only status is updated
            cur.execute(
                "UPDATE orders SET status=%s WHERE order_id=%s",
                (data.get("status"), oid)
            )
            conn.commit()
            body = { "ok": True }

        elif event["httpMethod"] == "DELETE":
            cur.execute(
                "DELETE FROM orders WHERE order_id=%s",
                (oid,)
            )
            conn.commit()
            body = { "ok": True }

        else:
            return {
                "statusCode": 405,
                "headers": { "Content-Type": "application/json" },
                "body": json.dumps({ "error": "Method not allowed" })
            }

        return {
            "statusCode": 200,
            "headers": { "Content-Type": "application/json" },
            "body": json.dumps(body)
        }

    except Exception as e:
        logger.exception("OrderItem handler failed")
        return {
            "statusCode": 500,
            "headers": { "Content-Type": "application/json" },
            "body": json.dumps({ "error": str(e) })
        }

    finally:
        if conn:
            conn.close()
