import os
from flask import Flask, request, make_response
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from werkzeug.security import generate_password_hash
from backend.db_config import get_connection

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ["FLASK_SECRET_KEY"]

# Token serializer
serializer = URLSafeTimedSerializer(os.environ["FLASK_SECRET_KEY"])

@app.route("/", methods=["POST"])
def reset_password():
    data = request.get_json() or {}
    token = data.get("token")
    new_password = data.get("new_password")

    if not token or not new_password:
        return make_response("Missing token or new_password", 400)

    # Verify token
    try:
        email = serializer.loads(
            token,
            salt="password-reset-salt",
            max_age=3600
        )
    except SignatureExpired:
        return make_response("Token expired", 400)
    except BadSignature:
        return make_response("Invalid token", 400)

    # Update the password in the database
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET password_hash = %s WHERE email = %s",
        (generate_password_hash(new_password), email)
    )
    conn.commit()
    conn.close()

    return make_response("Password updated", 200)