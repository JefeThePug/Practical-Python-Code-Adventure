from flask import (
    Blueprint,
    Response,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)

from app.appctx import get_app
from app.services import get_progress

route_bp = Blueprint("routes", __name__)


@route_bp.before_app_request
def ensure_year_in_session():
    if "year" not in session:
        session["year"] = str(get_app().config["CURRENT_YEAR"])


@route_bp.route("/how_to")
def how_to():
    """Render the help page.
    Returns: Rendered howto.html template with user information.
    """
    user = get_progress()
    return render_template(
        "how_to.html",
        img=user["img"],
        year=session["year"],
    )


@route_bp.route("/champions", methods=["GET", "POST"])
def champions():
    """Render the champions page.
    Returns: Rendered champions.html template with user information.
    """
    app = get_app()
    if request.method == "POST":
        valid_years = {str(y) for y in range(2025, app.config["CURRENT_YEAR"] + 1)}
        year = request.form["year"]
        if year in valid_years:
            session["year"] = year
        return redirect(url_for("routes.champions"))

    user = get_progress()

    champion_list = app.data_cache.get_all_champions(session["year"])
    all_data = app.data_cache.get_glance(session["year"])
    names, links = [], []
    for champion in champion_list:
        names.append(champion["name"])
        links.append(champion["github"])

    formatted_data = []
    for d in all_data:
        progress = "".join(
            "".join("☆★"[part] for part in week) for week in d["progress"]
        )
        if "★" not in progress:
            continue
        p = iter(progress)
        progress = ["".join(pair) for pair in zip(p, p)]
        formatted_data.append(
            {
                "progress": progress,
                "scores": [x.count("★") for x in progress],
                "name": d["name"],
                "id": d["user_id"],
            }
        )
    formatted_data.sort(key=lambda x: sum(x["scores"]), reverse=True)

    return render_template(
        "champions.html",
        img=user["img"],
        year=session["year"],
        champions=names,
        githubs=links,
        all_data=formatted_data,
    )


@route_bp.route("/gratitude")
def gratitude():
    """Render the gratitude page.
    Returns: Rendered gratitude.html template with user information.
    """
    user = get_progress()
    return render_template(
        "gratitude.html",
        img=user["img"],
        year=session["year"],
    )


@route_bp.route("/sponsor")
def sponsor():
    """Render the sponsor page.
    Returns: Rendered sponsor.html template with user information.
    """
    user = get_progress()

    t1, t2, t3 = get_app().data_cache.admin.get_sponsors()
    return render_template(
        "sponsor.html",
        img=user["img"],
        year=session["year"],
        t3=t3,
        t2=t2,
        t1=t1,
    )


@route_bp.route("/robots.txt")
def robots():
    static_dir = get_app().static_folder
    assert static_dir is not None
    return send_from_directory(static_dir, "robots.txt")


@route_bp.route("/sitemap.xml")
def sitemap():
    base_url = "https://adventure.practicalpython.org"

    pages = list(range(2025, get_app().config["CURRENT_YEAR"] + 1)) + [
        "how_to",
        "champions",
        "gratitude",
        "sponsor",
    ]

    xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    xml.append(f"<url><loc>{base_url}/</loc></url>")
    for page in pages:
        xml.append(f"<url><loc>{base_url}/{page}</loc></url>")
    xml.append("</urlset>")

    return Response("\n".join(xml), mimetype="application/xml")
