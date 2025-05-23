import os
import traceback
import sys
from flask import Flask, request, jsonify, make_response, session
from werkzeug.security import check_password_hash
from api.db_config import get_connection

app = Flask(__name__)
# Ensure the secret key is set for session support
app.secret_key = os.environ.get("FLASK_SECRET_KEY")

@app.route("/api/login", methods=["POST"])
def login():
    try:
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
        session.permanent = True  # Make the session permanent
        session['logged_in'] = True

        return jsonify({"success": True, "message": "Login successful"}), 200

    except Exception as e:
        tb = traceback.format_exc()
        print(tb, file=sys.stderr)  # logs full traceback to console or Vercel logs
        return jsonify({"error": str(e), "trace": tb}), 500

if __name__ == "__main__":
    # Run with debug enabled for local testing
    app.run(debug=True)
