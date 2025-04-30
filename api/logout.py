import os
from flask import Flask, session, jsonify

app = Flask(__name__)
app.secret_key = os.environ["FLASK_SECRET_KEY"]

@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify(success=True, message="Logged out"), 200