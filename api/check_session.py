import os
from flask import Flask, jsonify, session
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

@app.route("/", methods=["GET"])
def check_session():
    return jsonify(logged_in=bool(session.get("logged_in"))), 200