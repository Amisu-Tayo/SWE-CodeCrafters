import os
import json
import uuid
import boto3
from itsdangerous import URLSafeTimedSerializer
from backend.db_config import get_connection

# Prepare SES client & token serializer
ses = boto3.client(
    "ses",
    aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
    region_name=os.environ["AWS_REGION"]
)
serializer = URLSafeTimedSerializer(os.environ["FLASK_SECRET_KEY"])
SENDER = os.environ["SES_SENDER_EMAIL"]

def handler(request):
    data = request.get_json()
    email = data.get("email")
    password_hash = data.get("password_hash")

    # 1) Insert new user (unconfirmed)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (email, password_hash, is_confirmed) VALUES (%s, %s, 0)",
        (email, password_hash)
    )
    user_id = cur.lastrowid
    conn.commit()
    conn.close()

    # 2) Generate confirmation token & URL
    token = serializer.dumps(email, salt="email-confirm-salt")
    confirm_url = (
        f"https://fims.vercel.app/confirm.html?token={token}"
    )

    # 3) Send email via SES
    ses.send_email(
        Source=SENDER,
        Destination={"ToAddresses": [email]},
        Message={
            "Subject": {"Data": "Confirm your account"},
            "Body": {
                "Html": {
                    "Data": (
                        f"Welcome! Please confirm your account by "
                        f"<a href='{confirm_url}'>clicking here</a>."
                    )
                }
            }
        }
    )

    return {
        "statusCode": 201,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"user_id": user_id})
    }
