# api/orders.py

import json
from api.db_config import get_connection

def handler(request, response):
    """
    GET /api/orders
    Returns a JSON array of orders:
      [
        {
          "order_id": 12,
          "supplier_id": 3,
          "fabric_id": 1,
          "quantity": 100,
          "order_date": "2025-05-04T14:32:10",
          "status": "Pending"
        },
        ...
      ]
    """
    conn = get_connection()
    cur  = conn.cursor(dictionary=True)
    cur.execute("""
      SELECT order_id,
             supplier_id,
             fabric_id,
             quantity,
             order_date,
             status
      FROM orders
    """)
    rows = cur.fetchall()
    conn.close()

    return response.json(rows)