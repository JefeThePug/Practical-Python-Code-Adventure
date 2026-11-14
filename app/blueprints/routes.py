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
        return redirect(
            url_for("routes.champions", lb=request.form.get("lb", type=int))
        )

    user = get_progress()

    user_id = session.get("user_data", {}).get("id")
    boards = app.data_access.leaderboards.get_for_user(user_id) if user_id else []
    lb = request.args.get("lb", type=int)
    board = next((b for b in boards if b["id"] == lb), None)

    champion_list = app.data_access.get_all_champions(session["year"])
    all_data = app.data_access.get_glance(session["year"])
    names, links = [], []
    for champion in champion_list:
        names.append(champion["name"])
        links.append(champion["github"])

    totals = {i: {1: 0, 2: 0} for i in range(1, 11)}
    for d in all_data:
        for i, p in enumerate(d["progress"], 1):
            s = sum(p)
            totals[i][1] += s > 0
            totals[i][2] += s == 2
    max_total = max(t[1] for t in totals.values()) or 1

    formatted_data = []
    for d in all_data:
        score = sum(sum(week) for week in d["progress"])
        if score == 0:
            continue
        formatted_data.append(
            {
                "progress": [
                    ("empty", "half", "filled")[sum(week)] for week in d["progress"]
                ],
                "score": score,
                "name": d["name"],
                "id": d["user_id"],
            }
        )

    if board and user_id:
        formatted_data = [
            {
                "progress": [
                    ("empty", "half", "filled")[sum(week)] for week in m["progress"]
                ],
                "score": m["done"],
                "name": m["name"],
                "id": m["user_id"],
            }
            for m in app.data_access.leaderboards.get_members(
                board["name"], session["year"], user_id
            )
        ]

    formatted_data.sort(key=lambda x: x["score"], reverse=True)

    print(f"USERID{user_id}")

    return render_template(
        "champions.html",
        img=user["img"],
        year=session["year"],
        champions=names,
        githubs=links,
        totals=totals,
        max_total=max_total,
        all_data=formatted_data,
        boards=boards,
        board=board,
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

    t1, t2, t3 = get_app().data_access.admin.get_sponsors()
    return render_template(
        "sponsor.html",
        img=user["img"],
        year=session["year"],
        t3=t3,
        t2=t2,
        t1=t1,
    )


@route_bp.route("/fan_art")
def fan_art():
    """Render the fan art page.
    Returns: Rendered fan_art.html template with user information.
    """
    user = get_progress()

    page = max(1, request.args.get("page", 1, type=int))
    per_page = 8

    fan_art_data = get_app().data_access.admin.get_fan_art()

    total_pages = (len(fan_art_data) + per_page - 1) // per_page
    page = min(page, max(total_pages, 1))

    start = (page - 1) * per_page
    artwork = fan_art_data[start : start + per_page]

    return render_template(
        "fan_art.html",
        img=user["img"],
        year=session["year"],
        artwork=artwork,
        page=page,
        total_pages=total_pages,
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
