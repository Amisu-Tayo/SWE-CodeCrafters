# backend/login.py
import os
from flask import Flask, request, jsonify, make_response
from werkzeug.security import check_password_hash
from api.db_config import get_connection

app = Flask(__name__)

@app.route("/", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return make_response("Missing email or password", 400)

    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        "SELECT password_hash, is_confirmed FROM users WHERE email = %s",
        (email,)
    )
    user = cur.fetchone()
    conn.close()

    if not user:
        return make_response("User not found", 404)
    if not user["is_confirmed"]:
        return make_response("Please confirm your email first", 403)
    if not check_password_hash(user["password_hash"], password):
        return make_response("Invalid credentials", 401)

    return jsonify(message="Login successful"), 200