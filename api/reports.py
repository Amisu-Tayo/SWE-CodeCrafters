# api/reports.py

from api.db_config import get_connection

def handler(request, response):
    """
    GET /api/reports
    Returns JSON array of all saved sales reports:
      [
        {
          "report_id": 1,
          "generated_by": 2,
          "report_date": "2025-05-04T15:20:30",
          "report_data": "{\"cotton\":50,\"silk\":20}"
        },
        ...
      ]
    """
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
    conn.close()

    return response.json(rows)