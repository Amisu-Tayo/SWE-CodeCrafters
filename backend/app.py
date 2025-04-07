import os
from werkzeug.security import generate_password_hash
from flask import Flask, request, jsonify, session, url_for, redirect
from db_config import get_connection
from flask_cors import CORS  # Import CORS

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')
CORS(app)  # Enable CORS for the entire app

@app.route("/create_account", methods=["POST"])
def create_account():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    email = data.get("email")

    # Validate username and password before proceeding
    if not username or not password or not email:
        return jsonify({"success": False, "message": "All fields are required."}), 400

    # Hash the password
    password_hash = generate_password_hash(password)

    # Connect to the database
    conn = get_connection()
    cursor = conn.cursor()

    # Insert the user data into the database
    try:
        cursor.execute("INSERT INTO users (username, password_hash, role, email) VALUES (%s, %s, %s, %s)",
                       (username, password_hash, "Staff Member", email))  # Default role can be 'Staff Member'
        conn.commit()  # Commit the transaction
        conn.close()
        return jsonify({"success": True, "message": "Account created successfully!"}), 201
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):  # If user is not logged in, redirect to login
            return redirect(url_for('login'))  # Redirect to the login page
        return f(*args, **kwargs)
    return decorated_function


@app.route("/")
def home():
    return "Fabric Inventory API is running!"
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


@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = %s AND password_hash = %s", (username, password))
    user = cursor.fetchone()
    conn.close()

    if user:
        session['logged_in'] = True  # Set session to indicate user is logged in
        return jsonify({"success": True, "message": "Login successful"})
    else:
        return jsonify({"success": False, "message": "Invalid credentials"}), 401

@app.route("/logout", methods=["POST"])
def logout():
    session.pop('logged_in', None)  # Remove the session to log out the user
    return jsonify({"success": True, "message": "Logged out successfully"})

@app.route("/inventory", methods=["GET"])
def inventory():
    if not session.get('logged_in'):  # If user is not logged in, redirect to login
        return jsonify({"success": False, "message": "Please log in first."}), 401
     
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM fabric_inventory")
    rows = cursor.fetchall()
    conn.close()
    return jsonify(rows)

if __name__ == "__main__":
    app.run(debug=True)

if __name__ == "__main__":
    app.run(debug=True)
