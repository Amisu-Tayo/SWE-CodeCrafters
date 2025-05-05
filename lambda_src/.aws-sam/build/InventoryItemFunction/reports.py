import json
import logging
import decimal
import datetime
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

def _default(obj):
    if isinstance(obj, decimal.Decimal):
        n = float(obj)
        return int(n) if obj % 1 == 0 else n
    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def handler(event, context):
    logger.debug("Reports event: %s", event)
    method = event.get("httpMethod")

    if method == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": ""
        }

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

        # stringify the JSON column so the front‑end can JSON.parse it
        for r in rows:
            rd = r.get("report_data")
            if not isinstance(rd, str):
                r["report_data"] = json.dumps(rd, default=_default)

        body = json.dumps(rows, default=_default)
        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": body
        }

    except Exception as e:
        logger.exception("Reports handler failed")
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({ "error": str(e) })
        }

    finally:
        if conn:
            conn.close()
