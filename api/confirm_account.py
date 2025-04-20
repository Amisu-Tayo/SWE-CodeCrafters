import os
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from flask import Flask, request, make_response
from api.db_config import get_connection

app = Flask(__name__)
app.secret_key = os.environ["FLASK_SECRET_KEY"]
serializer = URLSafeTimedSerializer(os.environ["FLASK_SECRET_KEY"])

@app.route("/", methods=["GET"])
def confirm_account():
    token = request.args.get("token")
    if not token:
        return make_response("Missing token", 400)

    try:
        email = serializer.loads(token, salt="email-confirm-salt", max_age=3600)
    except SignatureExpired:
        return make_response("Token expired", 400)
    except BadSignature:
        return make_response("Invalid token", 400)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET is_confirmed = 1 WHERE email = %s",
        (email,)
    )
    conn.commit()
    conn.close()

    return make_response("Account confirmed! You can now log in.", 200)