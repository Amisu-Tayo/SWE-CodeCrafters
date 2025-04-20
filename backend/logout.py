# backend/logout.py
from flask import Flask, make_response

app = Flask(__name__)

@app.route("/", methods=["POST", "GET"])
def logout():
    # Since we’re stateless, simply return a success message.
    # front end will clear sessionStorage/localStorage as needed.
    return make_response("Logged out", 200)