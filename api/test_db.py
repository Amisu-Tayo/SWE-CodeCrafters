# This script is used to test the database connection
# and ensure that the database is reachable.
# It is a simple Flask application that responds with "OK" if the database connection is successful,
# or an error message if there is a problem.
from flask import Flask, make_response
from api.db_config import get_connection

app = Flask(__name__)

@app.route("/", methods=["GET"])
def test_db():
    try:
        conn = get_connection()
        conn.ping(reconnect=True)
        conn.close()
        return make_response("OK", 200)
    except Exception as e:
        return make_response(f"DB error: {e}", 500)