import json
from db_config import get_connection

def handler(event, context):
    conn = get_connection()
    cur  = conn.cursor()
    oid  = int(event["pathParameters"]["oid"])
    try:
        if event["httpMethod"] == "PUT":
            data = json.loads(event.get("body") or "{}")
            # usually only status is updated
            cur.execute(
                "UPDATE orders SET status=%s WHERE order_id=%s",
                (data.get("status"), oid)
            )
            conn.commit()
            return {
                "statusCode": 200,
                "headers": { "Content-Type": "application/json" },
                "body": json.dumps({ "ok": True })
            }

        elif event["httpMethod"] == "DELETE":
            cur.execute(
                "DELETE FROM orders WHERE order_id=%s",
                (oid,)
            )
            conn.commit()
            return {
                "statusCode": 200,
                "headers": { "Content-Type": "application/json" },
                "body": json.dumps({ "ok": True })
            }

        else:
            return { "statusCode": 405, "body": "" }

    finally:
        conn.close()