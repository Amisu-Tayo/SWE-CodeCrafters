import os
import json
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from db_config import get_connection

serializer = URLSafeTimedSerializer(os.environ["FLASK_SECRET_KEY"])

def handler(request):
    token = request.query.get("token")
    try:
        email = serializer.loads(
            token,
            salt="email-confirm-salt",
            max_age=3600
        )
    except SignatureExpired:
        return {"statusCode": 400, "body": "Token expired"}
    except BadSignature:
        return {"statusCode": 400, "body": "Invalid token"}

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET is_confirmed = 1 WHERE email = %s",
        (email,)
    )
    conn.commit()
    conn.close()

    return {
        "statusCode": 200,
        "body": "Account confirmed! You can now log in."
    }
