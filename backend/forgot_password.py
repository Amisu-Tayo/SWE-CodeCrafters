import os
from flask import Flask, request, make_response
import boto3
from itsdangerous import URLSafeTimedSerializer
from backend.db_config import get_connection

app = Flask(__name__)
app.secret_key = os.environ["FLASK_SECRET_KEY"]

# Initialize SES client
ses = boto3.client(
    "ses",
    aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
    region_name=os.environ["AWS_REGION"]
)

# Serializer for tokens
serializer = URLSafeTimedSerializer(os.environ["FLASK_SECRET_KEY"])
SENDER = os.environ["SES_SENDER_EMAIL"]

@app.route("/", methods=["POST"])
def forgot_password():
    data = request.get_json() or {}
    email = data.get("email")
    if not email:
        return make_response("Missing 'email' field", 400)

    # Verify user exists
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE email = %s", (email,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return make_response("User not found", 404)

    # Generate reset token & URL
    token = serializer.dumps(email, salt="password-reset-salt")
    reset_url = f"https://fims.store/reset.html?token={token}"

    # Send reset email via SES
    try:
        ses.send_email(
            Source=SENDER,
            Destination={"ToAddresses": [email]},
            Message={
                "Subject": {"Data": "Password reset"},
                "Body": {
                    "Html": {
                        "Data": f"Click <a href='{reset_url}'>here</a> to reset your password."
                    }
                }
            }
        )
    except Exception as e:
        return make_response(f"Email send failed: {e}", 500)

    return make_response("Reset email sent", 200)