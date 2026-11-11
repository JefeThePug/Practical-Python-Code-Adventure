from datetime import datetime, timezone

import yaml
from flask import (
    Blueprint,
    Response,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from app.appctx import get_app
from app.auth.decorators import admin_only
from app.types import SponsorRow

admin_bp = Blueprint("admin", __name__)


def get_years(app):
    """Return the list of valid admin years as strings."""
    return list(map(str, range(2025, app.config["CURRENT_YEAR"] + 1)))


def get_selected_year(app):
    """Resolve the currently selected year from request data."""
    return request.args.get(
        "year", request.form.get("year", f"{app.config['CURRENT_YEAR']}")
    )


def yaml_formatter(dumper, d):
    """
    Represent strings in YAML using block style (|) when multiline.
    Single-line strings use the default style.
    """
    return dumper.represent_scalar(
        "tag:yaml.org,2002:str", d, "|" if "\n" in d else None
    )


yaml.add_representer(str, yaml_formatter)


@admin_bp.route("/admin", methods=["GET", "POST"])
@admin_only
def admin():
    return render_template("admin/default.html")


@admin_bp.route("/admin/home")
@admin_only
def admin_home():
    return render_template("admin/home.html")


RELEASE_INPUT_FORMAT = "%Y-%m-%dT%H:%M"


@admin_bp.route("/admin/release", methods=["GET", "POST"])
@admin_only
def release():
    app = get_app()
    years = get_years(app)
    selected_year = get_selected_year(app)

    if request.method == "POST":
        releases: dict[int, datetime | None] = {}
        for n in range(1, 11):
            raw = request.form.get(f"r{n}", "").strip()
            try:
                releases[n] = (
                    datetime.strptime(raw, RELEASE_INPUT_FORMAT).replace(
                        tzinfo=timezone.utc
                    )
                    if raw
                    else None
                )
            except ValueError:
                flash(f"Week {n}: invalid date/time", "error")
                return redirect(url_for("admin.release", year=selected_year))
        app.data_access.admin.update_releases(
            selected_year, releases, all_on="all_on" in request.form
        )
        return redirect(url_for("admin.release", year=selected_year))

    data = app.data_access.admin.get_releases(selected_year)
    releases_utc = {
        n: (t.astimezone(timezone.utc).strftime(RELEASE_INPUT_FORMAT) if t else "")
        for n, t in data["releases"].items()
    }
    return render_template(
        "admin/release.html",
        years=years,
        selected_year=selected_year,
        all_on=data["all_on"],
        releases=releases_utc,
    )


@admin_bp.route("/admin/discord", methods=["GET", "POST"])
@admin_only
def discord():
    app = get_app()
    years = get_years(app)
    selected_year = get_selected_year(app)
    discord_ids = app.data_access.admin.get_discord(selected_year)
    main = discord_ids.get("0", {})
    channels = {selected_year: discord_ids.get(selected_year, {})}

    if request.method == "POST":
        values = {
            selected_year: {
                (f"{i}" if i > 0 else "champion"): request.form.get(f"c{i}", "").strip()
                for i in range(11)
            },
            "0": {
                key: request.form.get(key, "").strip()
                for key in ("guild", "adventurer")
            },
        }
        app.data_access.admin.update_discord(values)
        return redirect(url_for("admin.discord", year=selected_year))

    return render_template(
        "admin/discord.html",
        years=years,
        selected_year=selected_year,
        guild=main.get("guild", ""),
        adventurer=main.get("adventurer", ""),
        channels=channels,
    )


@admin_bp.route("/admin/html", methods=["GET", "POST"])
@admin_only
def html():
    app = get_app()
    years = get_years(app)
    selected_year = get_selected_year(app)
    selected_week = int(request.args.get("week", request.form.get("week", 1)))
    fields = ["title", "content", "instructions", "input_type", "form", "solution"]

    if request.method == "POST":
        ee = request.form.get("easter-egg") or None
        parts = {
            i: {cat: request.form.get(f"{cat}{i}") or "" for cat in fields}
            for i in range(1, 3)
        }
        app.data_access.html.update_html(
            selected_year, selected_week, fields, ee, parts
        )
        return redirect(url_for("admin.html", year=selected_year, week=selected_week))

    week_data = app.data_access.html.get_html(selected_year, selected_week)
    if week_data is None:
        flash(f"{selected_year}:#{selected_week} not found", "error")
        week_data = {}
    empty = {f: "" for f in fields}
    data = {part: week_data.get(part, empty) for part in range(1, 3)}
    egg = week_data.get("ee") or ""

    return render_template(
        "admin/html.html",
        years=years,
        selected_year=selected_year,
        selected_week=selected_week,
        fields=fields,
        data=data,
        egg=egg,
    )


@admin_bp.route("/admin/html/print", methods=["POST"])
@admin_only
def print_yaml():
    fields = ["title", "content", "instructions", "input_type", "form", "solution"]
    year = int(request.form["year"]) - 2025
    week = int(request.form["week"])

    data = [
        val
        for i in range(1, 3)
        for val in (
            {"_#": float(f"{week}.{i}")},
            {
                "main_entry_id": year * 10 + week,
                "part": i,
                **{
                    cat: "\n".join(
                        line.rstrip()
                        for line in (request.form.get(f"{cat}{i}") or "").splitlines()
                    )
                    for cat in fields
                },
            },
        )
    ]

    yaml_text = yaml.dump(
        data,
        sort_keys=False,
        default_flow_style=False,
        allow_unicode=True,
        width=10_000,
    ).replace("- _#: ", "\n# ")

    return Response(yaml_text, mimetype="text/yaml")


@admin_bp.route("/admin/solutions", methods=["GET", "POST"])
@admin_only
def solutions():
    app = get_app()
    years = get_years(app)
    selected_year = get_selected_year(app)
    solution_list = app.data_access.html.get_solutions(selected_year)

    if request.method == "POST":
        contents = {
            i: {"part1": request.form[f"{i}1"], "part2": request.form[f"{i}2"]}
            for i in range(1, 11)
        }
        app.data_access.html.update_solutions(selected_year, contents)
        return redirect(url_for("admin.solutions", year=selected_year))

    return render_template(
        "admin/solutions.html",
        years=years,
        selected_year=selected_year,
        solutions=solution_list,
    )


@admin_bp.route("/admin/users", methods=["GET", "POST"])
@admin_only
def user():
    app = get_app()
    years = get_years(app)
    selected_year = get_selected_year(app)
    users = app.data_access.get_glance(selected_year)

    if request.method == "POST":
        numbers = set(
            int(k)
            for key in request.form
            if "_" in key and (k := key.rsplit("_", 1)[1]).isdigit()
        )
        user_data = []
        deletes = []
        for n in sorted(numbers):
            if request.form.get(f"name_{n}", "").strip():
                uid = app.data_access.get_user_id(request.form[f"user_id_{n}"])
                user_data.append(
                    {
                        "id": uid,
                        "user_id": request.form.get(f"user_id_{n}") or "",
                        "name": request.form.get(f"name_{n}") or None,
                        "github": request.form.get(f"github_{n}") or None,
                        **{
                            f"c{i}": [
                                f"{i}A_{n}" in request.form,
                                f"{i}B_{n}" in request.form,
                            ]
                            for i in range(1, 11)
                        },
                    }
                )
            else:
                if request.form.get(f"user_id_{n}", "").strip():
                    deletes.append(request.form.get(f"user_id_{n}"))

        app.data_access.update_users(selected_year, user_data)
        if deletes:
            app.data_access.delete_users(deletes)
        return redirect(url_for("admin.user", year=selected_year))

    return render_template(
        "admin/users.html",
        years=years,
        selected_year=selected_year,
        users=users,
    )


@admin_bp.route("/admin/sponsors", methods=["GET", "POST"])
@admin_only
def sponsor():
    app = get_app()
    fields = ["name", "type", "website", "image", "blurb"]
    contents = [fields[:3], fields[:4], fields[:]]
    t1, t2, t3 = app.data_access.admin.get_sponsors(include_disabled=True)

    if request.method == "POST":
        numbers = set(
            int(k)
            for key in request.form
            if "_" in key and (k := key.rsplit("_", 1)[1]).isdigit()
        )
        bucket = {
            "wayfarer": "t1",
            "pathfinder": "t1",
            "explorer": "t2",
            "pioneer": "t3",
        }
        sponsors: list[SponsorRow] = [
            {
                "disabled": f"disabled_{n}" in request.form,
                "id": int(request.form[f"id_{n}"]),
                "bucket": bucket[request.form[f"type_{n}"]],
                "type": request.form[f"type_{n}"],
                "name": request.form[f"name_{n}"],
                "website": request.form.get(f"website_{n}"),
                "image": request.form.get(f"image_{n}"),
                "blurb": request.form.get(f"blurb_{n}"),
            }
            for n in sorted(numbers)
            if request.form.get(f"name_{n}", "").strip()
        ]
        app.data_access.admin.update_sponsors(sponsors)
        return redirect(url_for("admin.sponsor"))

    return render_template(
        "admin/sponsors.html",
        contents=contents,
        t3=t3,
        t2=t2,
        t1=t1,
    )


@admin_bp.route("/admin/perms", methods=["GET", "POST"])
@admin_only
def perms():
    app = get_app()
    permissions = app.data_access.admin.get_permissions()

    if request.method == "POST":
        values = [p.strip() for p in request.form.get("perms", "").splitlines()]
        app.data_access.admin.update_permissions([v for v in values if v])
        return redirect(url_for("admin.perms"))

    return render_template(
        "admin/perms.html",
        perms=permissions,
    )
