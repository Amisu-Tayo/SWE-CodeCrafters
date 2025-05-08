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
        return {"statusCode": 200, "headers": CORS_HEADERS, "body": ""}

    conn = None
    try:
        conn = get_connection()
        cur  = conn.cursor(dictionary=True)

        # Inventory panel
        if event["path"].endswith("/inventory"):
            cur.execute("""
              SELECT fabric_type,
                     SUM(quantity) AS qty
                FROM fabric_inventory
               GROUP BY fabric_type
            """)
            rows = cur.fetchall()
            body, status = json.dumps(rows, default=_default), 200

        # Sales panel
        elif event["path"].endswith("/sales"):
            cur.execute("""
              SELECT fi.fabric_type,
                     SUM(st.quantity_changed) AS sold
                FROM stock_transactions st
                JOIN fabric_inventory fi ON st.fabric_id=fi.fabric_id
               WHERE st.transaction_type='Removal'
                 AND st.transaction_date >= DATE_SUB(NOW(), INTERVAL 30 DAY)
               GROUP BY fi.fabric_type
            """)
            rows = cur.fetchall()
            body, status = json.dumps(rows, default=_default), 200

        # Pending orders panel
        elif event["path"].endswith("/pending-orders"):
            cur.execute("""
              SELECT fi.fabric_type,
                     COUNT(*) AS pending
                FROM orders o
                JOIN fabric_inventory fi ON o.fabric_id=fi.fabric_id
               WHERE o.status='Pending'
               GROUP BY fi.fabric_type
            """)
            rows = cur.fetchall()
            body, status = json.dumps(rows), 200

        # Usage trend panel
        elif event["path"].endswith("/usage-trend"):
            cur.execute("""
              SELECT DATE_FORMAT(transaction_date, '%Y-%m') AS month,
                     SUM(quantity_changed) AS used
                FROM stock_transactions
               WHERE transaction_type='Removal'
                 AND transaction_date >= DATE_SUB(NOW(), INTERVAL 6 MONTH)
               GROUP BY month
               ORDER BY month
            """)
            rows = cur.fetchall()
            body, status = json.dumps(rows), 200

        # Restock alerts panel
        elif event["path"].endswith("/restock-alerts"):
            cur.execute("""
              SELECT COUNT(*) AS pending_alerts
                FROM restock_alerts
               WHERE status='Pending'
            """)
            pending = cur.fetchone()[0] or 0
            body, status = json.dumps({"pending_alerts": pending}), 200

        else:
            body, status = json.dumps({"error": "Unknown report"}), 404

        return {"statusCode": status, "headers": CORS_HEADERS, "body": body}

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