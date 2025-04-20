import os
import json
from werkzeug.security import check_password_hash
from db_config import get_connection

def handler(request):
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        "SELECT password_hash, is_confirmed FROM users WHERE email = %s",
        (email,)
    )
    user = cur.fetchone()
    conn.close()

    if not user:
        return {"statusCode": 404, "body": "User not found"}

    if not user["is_confirmed"]:
        return {"statusCode": 403, "body": "Please confirm your email first"}

    if not check_password_hash(user["password_hash"], password):
        return {"statusCode": 401, "body": "Invalid credentials"}

    # On success: return minimal JSON (you can issue your own JWT here)
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"message": "Login successful"})
    }
