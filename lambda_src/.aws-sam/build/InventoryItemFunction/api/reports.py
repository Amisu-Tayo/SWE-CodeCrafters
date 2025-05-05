import json
from api.db_config import get_connection

def handler(event, context):
    conn = get_connection()
    cur  = conn.cursor(dictionary=True)
    try:
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
            "body": json.dumps(rows)
        }
    finally:
        conn.close()