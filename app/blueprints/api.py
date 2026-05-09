from flask import Blueprint, Response, jsonify

from app.appctx import get_app

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/leaderboard/<year>")
def leaderboard(year: str) -> Response:
    """
    Output leaderboard data for a given year in JSON format
    """
    all_data = get_app().data_cache.get_glance(str(year))
    return jsonify(all_data)
