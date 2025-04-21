import os
from flask import Flask, request, jsonify, make_response, session
from werkzeug.security import check_password_hash
from api.db_config import get_connection

app = Flask(__name__)

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return make_response("Missing username or password", 400)

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    conn.close()

    # Check if user exists
    if not user:
        return make_response("User not found", 404)

    # Check if user is confirmed (if you have email confirmation)
    if not user.get("is_confirmed", False):
        return make_response("Please confirm your email first", 403)

    # Check password hash
    if not check_password_hash(user["password_hash"], password):
        return make_response("Invalid credentials", 401)

    # Set the session for the logged-in user
    session['logged_in'] = True

    return jsonify({"success": True, "message": "Login successful"}), 200

    if __name__ == "__main__":
        app.secret_key = os.environ["FLASK_SECRET_KEY"]
        app.run(debug=True)   # ← enables traceback in the response