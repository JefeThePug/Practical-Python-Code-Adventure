from datetime import datetime, timezone

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


def released_weeks(year: str) -> int:
    """Number of consecutive weeks (from week 1) that have been released."""
    data = get_app().data_access.admin.get_releases(year)
    if data["all_on"]:
        return 10
    now = datetime.now(timezone.utc)
    count = 0
    for n in range(1, 11):
        release_at = data["releases"].get(n)
        if release_at is None or release_at > now:
            break
        count += 1
    return count


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
        num=released_weeks(session["year"]),
    )
