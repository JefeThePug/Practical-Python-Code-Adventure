from flask import Blueprint, render_template, session

from app.appctx import get_app
from app.services import get_progress

route_bp = Blueprint("routes", __name__)


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


@route_bp.route("/champions")
def champions():
    """Render the champions page.
    Returns: Rendered champions.html template with user information.
    """
    user = get_progress()

    champion_list = get_app().data_cache.get_all_champions(session["year"])
    all_data = get_app().data_cache.get_glance(session["year"])
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
