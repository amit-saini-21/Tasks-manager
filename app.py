import atexit

from flask import Flask, jsonify
from psycopg2 import Error as PsycopgError
from psycopg2 import IntegrityError
from werkzeug.exceptions import HTTPException

from config import Config
from utils.api_errors import APIError
from routes.auth import auth_bp
from routes.notes import notes_bp
from routes.other import other_bp
from routes.tasks import tasks_bp
import models



app = Flask(__name__)
app.config.from_object(Config)

app.register_blueprint(auth_bp)
app.register_blueprint(other_bp)
app.register_blueprint(notes_bp)
app.register_blueprint(tasks_bp)


def _error_payload(message, details=None):
    payload = {"error": message}
    if app.debug and details:
        payload["details"] = details
    return payload


@app.errorhandler(APIError)
def handle_api_error(exc):
    return jsonify(_error_payload(exc.message, exc.details)), exc.status_code


@app.errorhandler(PsycopgError)
def handle_db_error(exc):
    app.logger.exception("Database error")
    if isinstance(exc, IntegrityError):
        return jsonify(_error_payload("Database constraint violation")), 409
    return jsonify(_error_payload("Database operation failed")), 500


@app.errorhandler(Exception)
def handle_unexpected_error(exc):
    if isinstance(exc, HTTPException):
        return jsonify(_error_payload(exc.description)), exc.code

    app.logger.exception("Unhandled exception")
    return jsonify(_error_payload("Internal server error")), 500


def close_db_connection():
    models.close_shared_connection()


atexit.register(close_db_connection)

if __name__ == '__main__':
    app.run(debug=False, port=5000, use_reloader=False)