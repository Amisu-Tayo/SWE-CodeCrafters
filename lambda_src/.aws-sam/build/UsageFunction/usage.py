import json
from db_config import get_connection

def handler(event, context):
    conn = get_connection()
    cur  = conn.cursor(dictionary=True)
    try:
        cur.execute("""
          SELECT SUM(quantity_changed) AS monthly_usage
            FROM stock_transactions
           WHERE transaction_type = 'Removal'
             AND transaction_date >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        """)
        row = cur.fetchone()
        usage = (row["monthly_usage"] or 0)
        return {
            "statusCode": 200,
            "headers": { "Content-Type": "application/json" },
            "body": json.dumps({ "monthly_usage": usage })
        }
    finally:
        conn.close()