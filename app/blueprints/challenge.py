from time import time

import requests
from flask import (
    Blueprint,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app.appctx import exception, get_app
from app.services import get_progress, handle_cooldown, set_progress
from app.types import AppFlask

challenge_bp = Blueprint("challenge", __name__)


def fix_static(txt: str) -> str:
    """Replace the "__STATIC__" placeholder in the html
    with the path to the static directory.
    Args:
        txt (str): Raw html text
    Returns:
        str: html text with the correct path for images and files
    """
    return txt.replace("__STATIC__", url_for("static", filename=""))


def get_discord_membership(
    guild: str, uid: str, headers: dict[str, str]
) -> dict | None:
    """Fetch a user's guild membership from the Discord API.
    Args:
        guild (str): The ID of the Discord guild.
        uid (str): The Discord user ID.
        headers (dict): Request headers containing authorization.
    Returns:
        dict | None: The Guild Member object if found, otherwise None.
    """
    url = f"https://discord.com/api/v9/guilds/{guild}/members/{uid}"
    response = requests.get(url, headers=headers)

    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()


def get_challenge_context(app: AppFlask, year: str, obs_num: str) -> tuple | None:
    """Get challenge and Discord context for a specific challenge.
    Args:
        app (app.types.AppFlask): The Flask application instance.
        year (str): The challenge year.
        obs_num (str): The obfuscated challenge number.
    Returns:
        tuple | None: Challenge number, user data, progress, Discord guild ID,
            channel ID, and API headers, or None if the bot token is missing.
    """
    num = int(app.data_cache.admin.obfuscations[year][obs_num])
    user = get_progress()
    progress = user["progress"][f"c{num}"]

    bot_token = app.config["DISCORD_BOT_TOKEN"]
    if not bot_token:
        return None

    guild_id = app.data_cache.admin.discord_ids["0"]["guild"]
    channel_id = app.data_cache.admin.discord_ids[year][f"{num}"]
    headers = {
        "Authorization": f"Bot {bot_token}",
        "Content-Type": "application/json",
    }
    return num, user, progress, guild_id, channel_id, headers


@challenge_bp.route("/challenge/<year>/<obs_num>", methods=["GET", "POST"])
def challenge(year: str, obs_num: str):
    """Render the challenge page for a specific challenge week number.
    Args:
        year (str): The desired year.
        obs_num (str): The obfuscated challenge number.
    Returns:
        Rendered challenge.html template or error message.
        or redirect to the challenge page on correct guess.
    """
    session["year"] = year
    app = get_app()
    num = int(app.data_cache.admin.html_nums[year][obs_num])
    error = None

    user = get_progress()
    progress = user["progress"][f"c{num}"]
    cooldown_key = f"cooldown_{year}_{num}_{2 if progress[0] else 1}"

    if request.method == "POST":
        allowed, wait_ms = handle_cooldown(cooldown_key)

        if not allowed:
            seconds = (wait_ms + 999) // 1000
            error = f"Too many attempts. Wait {seconds} second{'s' if seconds != 1 else ''}."
        else:
            guesses = [request.form.get(f"answer{i}", None) for i in (1, 2)]
            solutions = app.data_cache.html.solutions[year][num]
            for n, guess in enumerate(guesses):
                if (
                    guess
                    and guess.replace("_", " ").upper().strip()
                    == solutions[f"part{n + 1}"]
                ):
                    cookie = set_progress(num, n)

                    redirect_url = url_for(
                        f"challenge.{('challenge', 'complete')[n]}",
                        year=year,
                        obs_num=obs_num,
                    )
                    resp = make_response(redirect(redirect_url))

                    if cookie:
                        resp.set_cookie(cookie, f"{num}{'AB'[n]}")

                    return resp
                else:
                    error = "Incorrect. Please try again."

    html = app.data_cache.html.html.get(year, {}).get(num, {})
    parts = []
    for part_num in (1, 2):
        part_data = html.get(part_num)
        if not isinstance(part_data, dict):
            return redirect(url_for("main.index"))
        parts.append(
            {
                k: fix_static(v) if isinstance(v, str) else v
                for k, v in part_data.items()
            }
        )
    a, b = parts

    cd = session.get(cooldown_key, {"until": 0})
    remaining_ms = max(0, cd["until"] - int(time() * 1000))
    remaining_s = (remaining_ms + 999) // 1000

    params = {
        "img": user["img"],
        "year": session["year"],
        "num": f"{num}",
        "a": a,
        "b": b,
        "sol1": a["solution"] if progress[0] else a["form"],
        "sol2": b["solution"] if progress[1] else b["form"],
        "part_two": progress[0],
        "done": progress[1] and "user_data" in session,
        "error": error,
        "cooldown": remaining_s,
    }
    return render_template("challenge.html", **params)


@challenge_bp.route("/complete/<year>/<obs_num>", methods=["GET", "POST"])
def complete(year: str, obs_num: str):
    """Render the success page for a specific challenge week number.
    Args:
        year (str): The desired year.
        obs_num (str): The obfuscated challenge number.
    Returns:
        Rendered link_complete.html template.
    """
    app = get_app()
    context = get_challenge_context(app, year, obs_num)
    if context is None:
        return "Error: Bot token not found", 500

    num, user, progress, guild_id, channel_id, headers = context
    user_id = user["id"]
    if user_id is None:
        return "Error: User ID not found", 500

    if not all(progress):
        return redirect(url_for("challenge.challenge", year=year, obs_num=obs_num))

    if request.method == "POST":
        github_username = request.form.get("github_username")
        # save github_id here

    show_github_ask = user["rockets"] and all(all(r) for r in user["rockets"])
    in_guild = get_discord_membership(guild_id, user_id, headers) is not None
    egg = app.data_cache.html.html[year][num]["ee"]

    return render_template(
        "link_complete.html",
        year=year,
        img=user["img"],
        num=num,
        guild=guild_id,
        channel=channel_id,
        in_guild=in_guild,
        egg=egg,
        show_github_ask=show_github_ask,
    )


@challenge_bp.route("/access/<year>/<obs_num>", methods=["POST"])
def access(year: str, obs_num: str):
    """Grant access to a user and assign roles in Discord.
    Args:
        year (str): The desired year.
        obs_num (str): The obfuscated challenge number.
    Returns:
        Redirect to the challenge completion page or an error message.
    """
    app = get_app()
    context = get_challenge_context(app, year, obs_num)
    if context is None:
        return "Error: Bot token not found", 500

    num, user, progress, guild_id, channel_id, headers = context
    user_id = user["id"]
    if user_id is None:
        return "Error: User ID not found", 500

    if not all(progress):
        return "Denied: Challenge not completed", 403

    adventurer_role = app.data_cache.admin.discord_ids["0"]["adventurer"]
    roles_to_add = [adventurer_role]
    if user["rockets"] and all(all(r) for r in user["rockets"]):
        champion_role = app.data_cache.admin.discord_ids[year]["champion"]
        roles_to_add.append(champion_role)

    member_data = get_discord_membership(guild_id, user_id, headers)

    if member_data is not None:
        current_roles = set(member_data.get("roles", []))

        for role in roles_to_add:
            if role in current_roles:
                continue
            try:
                roles_url = f"https://discord.com/api/v9/guilds/{guild_id}/members/{user_id}/roles/{role}"
                res = requests.put(roles_url, headers=headers)
                res.raise_for_status()
            except requests.exceptions.RequestException as e:
                return f"Failed to update roles: {e}", 400

        content = (
            f"<@{user_id}> solved week {num}! If you'd like, "
            "please share how you arrived at the correct answer!"
        )
        url = f"https://discord.com/api/v9/channels/{channel_id}"
        member_url = f"{url}/thread-members/{user_id}"
        msg_url = f"{url}/messages"
        response = requests.get(member_url, headers=headers)
        if response.status_code == 404:
            # User not in thread
            try:
                requests.put(member_url, headers=headers).raise_for_status()
                requests.post(
                    msg_url, headers=headers, json={"content": content}
                ).raise_for_status()
            except requests.exceptions.RequestException as e:
                exception("Thread Message Error", e)

    return redirect(url_for("challenge.complete", year=year, obs_num=obs_num))
