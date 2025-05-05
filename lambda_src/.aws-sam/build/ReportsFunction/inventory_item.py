import json
from api.db_config import get_connection

def handler(event, context):
    conn = get_connection()
    cur  = conn.cursor()
    fid  = int(event["pathParameters"]["fid"])
    try:
        if event["httpMethod"] == "PUT":
            data = json.loads(event.get("body") or "{}")
            sql = """
              UPDATE fabric_inventory
                 SET fabric_type=%s,
                     color=%s,
                     quantity=%s,
                     price_per_unit=%s,
                     restock_threshold=%s
               WHERE fabric_id=%s
            """
            params = (
                data["fabric_type"],
                data["color"],
                data["quantity"],
                data["price_per_unit"],
                data["restock_threshold"],
                fid
            )
            cur.execute(sql, params)
            conn.commit()
            return {
                "statusCode": 200,
                "headers": { "Content-Type": "application/json" },
                "body": json.dumps({ "ok": True })
            }

        elif event["httpMethod"] == "DELETE":
            cur.execute(
                "DELETE FROM fabric_inventory WHERE fabric_id=%s",
                (fid,)
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