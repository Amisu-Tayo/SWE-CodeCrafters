import os
import json
import boto3
from itsdangerous import URLSafeTimedSerializer
from backend.db_config import get_connection

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

    # Verify user exists
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE email = %s", (email,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return {"statusCode": 404, "body": "User not found"}

    # Generate reset token
    token = serializer.dumps(email, salt="password-reset-salt")
    reset_url = f"https://fims.vercel.app/reset.html?token={token}"

    # Send email
    ses.send_email(
        Source=SENDER,
        Destination={"ToAddresses": [email]},
        Message={
            "Subject": {"Data": "Password reset"},
            "Body": {
                "Html": {
                    "Data": (
                        f"Click <a href='{reset_url}'>here</a> "
                        "to reset your password."
                    )
                }
            }
        }
    )

    return {"statusCode": 200, "body": "Reset email sent"}
