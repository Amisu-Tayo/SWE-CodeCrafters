# api/inventory.py

import json
from api.db_config import get_connection

def handler(request, response):
    """
    GET /api/inventory
    Returns a JSON array of all inventory items:
      [
        {
          "fabric_id": 1,
          "fabric_type": "cotton",
          "color": "blue",
          "quantity": 50,
          "price_per_unit": 3.25,
          "restock_threshold": 20
        },
        ...
      ]
    """
    conn = get_connection()
    cur  = conn.cursor(dictionary=True)
    cur.execute("""
      SELECT fabric_id,
             fabric_type,
             color,
             quantity,
             price_per_unit,
             restock_threshold
      FROM fabric_inventory
    """)
    rows = cur.fetchall()
    conn.close()

    return response.json(rows)