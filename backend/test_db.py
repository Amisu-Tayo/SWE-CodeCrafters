from db_config import get_connection

def handler(request):
    try:
        conn = get_connection()
        conn.ping(reconnect=True)
        conn.close()
        return {
            "statusCode": 200,
            "body": "OK"
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": f"DB error: {e}"
        }
