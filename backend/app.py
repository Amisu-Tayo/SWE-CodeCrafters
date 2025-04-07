import os
from functools import wraps
import mysql.connector
from dotenv import load_dotenv
load_dotenv()
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from flask import Flask, request, jsonify, session, url_for, redirect
from db_config import get_connection
from flask_cors import CORS  # Import CORS

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')
CORS(app)  # Enable CORS for the entire app

# Decorator to check if user is logged in
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):  # If user is not logged in, redirect to login
            return redirect(url_for('login'))  # Redirect to the login page
        return f(*args, **kwargs)
    return decorated_function

@app.route("/CreateAccount", methods=["POST"])
def CreateAccount():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    email = data.get("email")

    # Validate username and password before proceeding
    if not username or not password or not email:
        return jsonify({"success": False, "message": "All fields are required."}), 400

    # Check if the username already exists
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    existing_user = cursor.fetchone()

    if existing_user:
        conn.close()
        return jsonify({"success": False, "message": "Username already exists."}), 400
    
    # Check if the email already exists
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    existing_email = cursor.fetchone()
    if existing_email:
        conn.close()
        return jsonify({"success": False, "message": "An account already exists with this email address. Please log in"}), 400

    # Validate password strength
    if len(password) < 8:
        return jsonify({"success": False, "message": "Password must be at least 8 characters long."}), 400
    if not any(char.isdigit() for char in password):
        return jsonify({"success": False, "message": "Password must contain at least one digit."}), 400
    if not any(char.isalpha() for char in password):
        return jsonify({"success": False, "message": "Password must contain at least one letter."}), 400
    if not any(char in "!@#$%^&*()_+" for char in password):
        return jsonify({"success": False, "message": "Password must contain at least one special character."}), 400
    if username == password:
        return jsonify({"success": False, "message": "Password cannot be the same as username."}), 400
    if username in password:
        return jsonify({"success": False, "message": "Password cannot contain the username."}), 400
    if password in username:
        return jsonify({"success": False, "message": "Username cannot contain the password."}), 400

    # Hash the password
    password_hash = generate_password_hash(password, method='scrypt')

    # Connect to the database
    cursor.execute("INSERT INTO users (username, password_hash, role, email) VALUES (%s, %s, %s, %s)",
                   (username, password_hash, "Staff Member", email))  # Default role can be 'Staff Member'
    conn.commit()  # Commit the transaction
    conn.close()
    return jsonify({"success": True, "message": "Account created successfully!"}), 201

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    conn.close()

    if user and check_password_hash(user['password_hash'], password):  # Check password hash
        session['logged_in'] = True  # Set session to indicate user is logged in
        return jsonify({"success": True, "message": "Login successful"})
    else:
        return jsonify({"success": False, "message": "Invalid credentials"}), 401

@app.route("/logout", methods=["POST"])
def logout():
    session.pop('logged_in', None)  # Remove the session to log out the user
    return jsonify({"success": True, "message": "Logged out successfully"})

@app.route("/inventory", methods=["GET"])
@login_required  # Apply login check here
def inventory():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM fabric_inventory")
    rows = cursor.fetchall()
    conn.close()
    return jsonify(rows)

@app.route("/orders", methods=["GET"])
@login_required  # Apply login check here
def orders():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM orders")
    rows = cursor.fetchall()
    conn.close()
    return jsonify(rows)

@app.route("/reports", methods=["GET"])
@login_required  # Apply login check here
def reports():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM sales_reports")
    rows = cursor.fetchall()
    conn.close()
    return jsonify(rows)

if __name__ == "__main__":
    app.run(debug=True)
