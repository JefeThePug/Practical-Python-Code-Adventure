from flask import Blueprint, redirect, render_template, session, url_for

from app.appctx import get_app
from app.services import get_progress

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """Redirect to the index page for the current year or the year in session.
    Returns: Redirect to current year.
    """
    if "year" not in session:
        session["year"] = f"{get_app().config['CURRENT_YEAR']}"
    return redirect(url_for("main.release", year=session["year"]))


@main_bp.route("/<int:year>")
def release(year: int):
    """Render the index page for a specific year with user progress and release number.
    Returns: Rendered index.html template.
    """
    session["year"] = f"{year}"
    user = get_progress()
    return render_template(
        "index.html",
        img=user["img"],
        year=session["year"],
        rockets=user["rockets"],
        num=get_app().data_cache.admin.releases[session["year"]],
    )
