import os, boto3
from flask import Flask, request, jsonify
from itsdangerous import URLSafeTimedSerializer
from api.db_config import get_connection

app = Flask(__name__)
app.secret_key = os.environ["FLASK_SECRET_KEY"]
serializer = URLSafeTimedSerializer(app.secret_key)

ses = boto3.client(
  "ses",
  aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
  aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
  region_name=os.environ["AWS_REGION"]
)
SENDER = os.environ["SES_SENDER_EMAIL"]

@app.route("/api/forgot_password", methods=["POST"])
def forgot_password():
    data = request.get_json() or {}
    email = data.get("email")
    if not email:
        return jsonify(success=False, message="Email is required"), 400

    conn = get_connection()
    cur = conn.cursor()
   
    cur.execute("SELECT user_id FROM users WHERE email = %s", (email,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return jsonify(success=False, message="User not found"), 404

    if row:
        token = serializer.dumps(email, salt="password-reset-salt")
        link = f"https://fims.store/ResetPassword.html?token={token}"
        ses.send_email(
          Source=SENDER,
          Destination={"ToAddresses": [email]},
          Message={
            "Subject": {"Data": "Your FIMS reset link"},
            "Body": {"Html": {"Data": f"<p>Reset <a href='{link}'>here</a>.</p>"}}
          }
        )
    # always 200 so we don’t leak
    return jsonify(success=True,
                   message="A reset link has been sent! Check your email"), 200