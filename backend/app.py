import os
from functools import wraps
import mysql.connector
from dotenv import load_dotenv
load_dotenv()
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, request, jsonify, session, url_for, redirect, send_from_directory
from db_config import get_connection
from flask_cors import CORS


app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')
CORS(app)  # Enable CORS for the entire app

# Define directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_ROOT = os.path.join(BASE_DIR, "..", "frontend")
FRONTEND_HTML = os.path.join(FRONTEND_ROOT, "html")

# Decorator to check if user is logged in
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Route to serve static files from the frontend folder (CSS, images, etc.)
@app.route("/frontend/<path:filename>")
def serve_frontend_files(filename):
    return send_from_directory(FRONTEND_ROOT, filename)

# Serve the landing page from the frontend/html folder
@app.route("/")
def home():
    return send_from_directory(FRONTEND_HTML, "index.html")

# Test database connection
@app.route("/test_db", methods=["GET"])
def test_db():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        conn.close()
        return jsonify({"success": True, "message": "Database connection successful!", "result": result})
    except Exception as e:
        return jsonify({"success": False, "message": f"Database connection failed: {str(e)}"}), 500

# Login route: handle GET and POST
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        data = request.json
        username = data.get("username")
        password = data.get("password")

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['logged_in'] = True
            return jsonify({"success": True, "message": "Login successful"})
        else:
            return jsonify({"success": False, "message": "Invalid credentials"}), 401
    else:
        # Serve login.html on GET requests
        return send_from_directory(FRONTEND_HTML, "login.html")

@app.route("/CreateAccount", methods=["GET", "POST"])
def CreateAccount():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    email = data.get("email")

    if not username or not password or not email:
        return jsonify({"success": False, "message": "All fields are required."}), 400

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    existing_user = cursor.fetchone()

    if existing_user:
        conn.close()
        return jsonify({"success": False, "message": "Username already exists."}), 400

    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    existing_email = cursor.fetchone()
    if existing_email:
        conn.close()
        return jsonify({"success": False, "message": "An account already exists with this email address. Please log in"}), 400

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

    password_hash = generate_password_hash(password, method='scrypt')

    cursor.execute("INSERT INTO users (username, password_hash, role, email) VALUES (%s, %s, %s, %s)",
                   (username, password_hash, "Staff Member", email))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Account created successfully!"}), 201

@app.route("/logout", methods=["POST"])
def logout():
    session.pop('logged_in', None)
    return jsonify({"success": True, "message": "Logged out successfully"})

@app.route("/inventory", methods=["GET"])
@login_required
def inventory():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM fabric_inventory")
    rows = cursor.fetchall()
    conn.close()
    return jsonify(rows)

@app.route("/orders", methods=["GET"])
@login_required
def orders():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM orders")
    rows = cursor.fetchall()
    conn.close()
    return jsonify(rows)

@app.route("/reports", methods=["GET"])
@login_required
def reports():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM sales_reports")
    rows = cursor.fetchall()
    conn.close()
    return jsonify(rows)

# Catch-all route to serve any .html files from frontend/html
@app.route('/<path:filename>')
def serve_static_html(filename):
    if filename.endswith('.html'):
        return send_from_directory(FRONTEND_HTML, filename)
    return "Not Found", 404

if __name__ == "__main__":
    app.run(debug=True)