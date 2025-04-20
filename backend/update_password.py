import os
import json
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from werkzeug.security import generate_password_hash
from db_config import get_connection

serializer = URLSafeTimedSerializer(os.environ["FLASK_SECRET_KEY"])

def handler(request):
    data = request.get_json()
    token = data.get("token")
    new_password = data.get("new_password")

    try:
        email = serializer.loads(token, salt="password-reset-salt", max_age=3600)
    except SignatureExpired:
        return {"statusCode": 400, "body": "Token expired"}
    except BadSignature:
        return {"statusCode": 400, "body": "Invalid token"}

    # Update in DB
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET password_hash = %s WHERE email = %s",
        (generate_password_hash(new_password), email)
    )
    conn.commit()
    conn.close()

    return {"statusCode": 200, "body": "Password updated"}
