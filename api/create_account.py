import os
import json
import boto3
from itsdangerous import URLSafeTimedSerializer
from flask import Flask, request, jsonify, make_response
from werkzeug.security import generate_password_hash
from api.db_config import get_connection

app = Flask(__name__)
app.secret_key = os.environ["FLASK_SECRET_KEY"]

# SES client
ses = boto3.client(
    "ses",
    aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
    region_name=os.environ["AWS_REGION"]
)
serializer = URLSafeTimedSerializer(os.environ["FLASK_SECRET_KEY"])
SENDER = os.environ["SES_SENDER_EMAIL"]

@app.route("/api/create_account", methods=["POST"])  # Define the correct route for the API
def create_account():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")
    username = data.get("username")

    if not email or not password or not username:
        return make_response("Missing email, password, or username", 400)  # Check if any required field is missing

    # Check if the username already exists in the database
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = %s", (username,))
    existing_user = cur.fetchone()

    if existing_user:
        conn.close()
        return make_response("Username already exists", 400)

    # Check if the email already exists in the database
    cur.execute("SELECT * FROM users WHERE email = %s", (email,))
    existing_email = cur.fetchone()

    if existing_email:
        conn.close()
        return make_response("Email already registered. Please log in", 400)

    # Generate the password hash here
    password_hash = generate_password_hash(password, method='scrypt')  # Hash password on backend

    # 1) Insert user as unconfirmed
    cur.execute(
        "INSERT INTO users (username, email, password_hash, is_confirmed) VALUES (%s, %s, %s, 0)",
        (username, email, password_hash)
    )
    user_id = cur.lastrowid
    conn.commit()
    conn.close()

    # 2) Send confirmation email
    token = serializer.dumps(email, salt="email-confirm-salt")
    confirm_url = f"https://fims.store/confirm.html?token={token}"

    try:
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
    except Exception as e:
        return make_response(f"Email send failed: {e}", 500)

    return jsonify(user_id=user_id), 201

if __name__ == "__main__":
    app.run(debug=True)