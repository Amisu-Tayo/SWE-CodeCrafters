import os
from flask import Flask, request, jsonify
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from werkzeug.security import generate_password_hash
from api.db_config import get_connection

app = Flask(__name__)
app.secret_key = os.environ["FLASK_SECRET_KEY"]
serializer = URLSafeTimedSerializer(app.secret_key)

@app.route("/api/reset_password", methods=["POST"])  # <-- corrected path
def reset_password():
    data = request.get_json() or {}
    token = data.get("token")
    pw = data.get("password")
    if not token or not pw:
        return jsonify(success=False,
                       message="Token and new password are required"), 400

    try:
        email = serializer.loads(token, salt="password-reset-salt", max_age=3600)
    except SignatureExpired:
        return jsonify(success=False, message="Reset link expired"), 400
    except BadSignature:
        return jsonify(success=False, message="Invalid reset token"), 400

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
      "UPDATE users SET password_hash = %s WHERE email = %s",
      (generate_password_hash(pw), email)
    )
    conn.commit()
    conn.close()

    return jsonify(success=True, message="Password updated"), 200