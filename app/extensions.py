import secrets

from flask import abort, request, session
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def generate_csrf_token():
    """Create a token and store it in the session if it doesn't exist."""
    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_hex(32)
    return session["_csrf_token"]


def validate_csrf():
    """Gatekeeper: Runs before every request."""
    if request.method == "POST":
        session_token = session.get("_csrf_token")
        form_token = request.form.get("csrf_token")
        if (
            not session_token
            or not form_token
            or not secrets.compare_digest(session_token, form_token)
        ):
            abort(400, description="CSRF token missing or invalid.")
