import json
import logging
from db_config import get_connection

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

CORS_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "https://fims.store",
    "Access-Control-Allow-Methods": "OPTIONS,GET",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    "Access-Control-Allow-Credentials": "true"
}

def handler(event, context):
    logger.debug("Usage event: %s", event)
    method = event.get("httpMethod")

    if method == "OPTIONS":
        return {"statusCode": 200, "headers": CORS_HEADERS, "body": ""}

    conn = None
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute("""
          SELECT SUM(quantity_changed) AS monthly_usage
            FROM stock_transactions
           WHERE transaction_type = 'Removal'
             AND transaction_date >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        """)
        row   = cur.fetchone()
        usage = row[0] or 0
        body  = json.dumps({ "monthly_usage": usage })
        return {"statusCode": 200, "headers": CORS_HEADERS, "body": body}

    except Exception as e:
        logger.exception("Usage handler failed")
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({ "error": str(e) })
        }

    finally:
        if conn:
            conn.close()