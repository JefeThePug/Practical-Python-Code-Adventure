from typing import NoReturn

from flask import Blueprint, Response, abort, make_response, send_from_directory
from werkzeug.exceptions import NotFound

errors_bp = Blueprint("errors", __name__)


@errors_bp.app_errorhandler(404)
def teapot(_: NotFound) -> Response:
    """Handle 404 errors by returning a 418 teapot response with an image.
    Args:
        _ (Exception): The error that occurred. (Not Used)
    Returns:
        Response: Custom response with a 418 status code and an image.
    """
    response = make_response(send_from_directory("static/images", "hmm.png"))
    response.headers["Easter-Egg"] = "TO BE CONTINUED"
    response.status_code = 418
    return response


@errors_bp.route("/418")
def trigger_418() -> NoReturn:
    """Trigger a 418 error for testing purposes."""
    abort(404)
