# api/usage.py

import json
from api.db_config import get_connection

def handler(request, response):
    """
    GET /api/usage
    Returns a JSON object with one key, `monthly_usage`, the sum of all
    'Removal' transactions in the last 30 days, e.g.:
      { "monthly_usage": 275 }
    """
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
      SELECT SUM(quantity_changed) AS monthly_usage
        FROM stock_transactions
       WHERE transaction_type = 'Removal'
         AND transaction_date >= DATE_SUB(NOW(), INTERVAL 30 DAY)
    """)
    row = cur.fetchone()
    conn.close()

    # row might be a tuple or a dict, depending on your cursor type
    usage = (row['monthly_usage'] if isinstance(row, dict) else row[0]) or 0
    return response.json({ "monthly_usage": usage })