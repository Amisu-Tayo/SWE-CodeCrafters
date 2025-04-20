import os
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from flask import Flask, request, jsonify
from api.db_config import get_connection

app = Flask(__name__)
app.secret_key = os.environ["FLASK_SECRET_KEY"]
serializer = URLSafeTimedSerializer(os.environ["FLASK_SECRET_KEY"])

@app.route("/api/confirm_account", methods=["POST"])
def confirm_account():
    data = request.get_json() or {}
    token = data.get("token")

    if not token:
        return jsonify({"success": False, "message": "Missing token"}), 400

    try:
        # Verify the token and get the email
        email = serializer.loads(token, salt="email-confirm-salt", max_age=3600)  # Token expires after 1 hour
    except SignatureExpired:
        return jsonify({"success": False, "message": "Token expired"}), 400
    except BadSignature:
        return jsonify({"success": False, "message": "Invalid token"}), 400

    # Now, update the user's account status to confirmed
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404
    
    # Update the is_confirmed flag
    cursor.execute("UPDATE users SET is_confirmed = 1 WHERE email = %s", (email,))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "Account confirmed! You can now log in."}), 200