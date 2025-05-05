import json
import logging
from db_config import get_connection

# Set up logging so we can see errors in CloudWatch
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def handler(event, context):
    logger.debug("Usage event: %s", event)
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT SUM(quantity_changed) AS monthly_usage
              FROM stock_transactions
             WHERE transaction_type = 'Removal'
               AND transaction_date >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        """)
        row = cur.fetchone()
        # Convert to an int to avoid Decimal serialization issues
        usage = int(row[0] or 0)

        return {
            "statusCode": 200,
            "headers": { "Content-Type": "application/json" },
            "body": json.dumps({ "monthly_usage": usage })
        }

    except Exception as e:
        logger.exception("Usage handler failed")
        return {
            "statusCode": 500,
            "headers": { "Content-Type": "application/json" },
            "body": json.dumps({ "error": str(e) })
        }

    finally:
        if conn:
            conn.close()