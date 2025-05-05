import json
import logging
import decimal
import datetime
from db_config import get_connection

# Set up logging so we see errors in CloudWatch
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def _default(obj):
    if isinstance(obj, decimal.Decimal):
        # convert to int if whole number, else float
        n = float(obj)
        return int(n) if obj % 1 == 0 else n
    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def handler(event, context):
    logger.debug("Reports event: %s", event)
    conn = None
    try:
        conn = get_connection()
        cur  = conn.cursor(dictionary=True)

        cur.execute("""
          SELECT report_id,
                 generated_by,
                 report_date,
                 report_data
            FROM sales_reports
           ORDER BY report_date DESC
        """)
        rows = cur.fetchall()

        return {
            "statusCode": 200,
            "headers": { "Content-Type": "application/json" },
            "body": json.dumps(rows, default=_default)
        }

    except Exception as e:
        logger.exception("Reports handler failed")
        return {
            "statusCode": 500,
            "headers": { "Content-Type": "application/json" },
            "body": json.dumps({ "error": str(e) })
        }

    finally:
        if conn:
            conn.close()
