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
            error = f"Too many attempts. Wait {seconds}{'s' if seconds != 1 else ''}."
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
                    resp = make_response(
                        redirect(
                            url_for("challenge.challenge", year=year, obs_num=obs_num)
                        )
                    )
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


@challenge_bp.route("/access", methods=["POST"])
def access():
    """Grant access to a user and assign roles in Discord.

    Returns:
        Rendered link_complete.html template or error message.
        or Error message with HTTP status code.
    """
    app = get_app()
    bot_token = app.config["DISCORD_BOT_TOKEN"]
    year = session["year"]
    if not bot_token:
        return "Error: Bot token not found", 500

    num = int(app.data_cache.admin.obfuscations[year][f"{request.form.get('num')}"])
    user = get_progress()

    guild_id = app.data_cache.admin.discord_ids["0"]["guild"]
    user_id = user["id"]
    channel_id = app.data_cache.admin.discord_ids[year][f"{num}"]
    verified_role = app.data_cache.admin.discord_ids["0"]["role"]
    adventurer_role = app.data_cache.admin.discord_ids["0"]["adventurer"]
    roles_to_add = [verified_role, adventurer_role]
    if all(all(r) for r in user["rockets"]):
        champion_role = app.data_cache.admin.discord_ids[year]["champion"]
        roles_to_add.append(champion_role)

    headers = {"Authorization": f"Bot {bot_token}", "Content-Type": "application/json"}
    url = f"https://discord.com/api/v9/guilds/{guild_id}/members/{user_id}"
    response = requests.get(url, headers=headers)

    # User is not a member of the guild, add them with roles
    if response.status_code == 404:
        join_payload = {
            "access_token": session["token"],
            "roles": roles_to_add,
        }
        try:
            put_res = requests.put(url, headers=headers, json=join_payload)
            put_res.raise_for_status()
        except requests.exceptions.RequestException as e:
            return f"Error: Failed to join/assign role: {e}", 400

    # User IS a member of the guild, add roles
    elif response.status_code == 200:
        member_data = response.json()
        current_roles = member_data.get("roles", [])
        updated_roles = list(set(current_roles + roles_to_add))
        try:
            patch_res = requests.patch(
                url, headers=headers, json={"roles": updated_roles}
            )
            patch_res.raise_for_status()
        except requests.exceptions.RequestException as e:
            return f"Failed to update roles: {e}", 400

    else:
        return f"Unexpected error: {response.status_code}", response.status_code

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
            res = requests.post(msg_url, headers=headers, json={"content": content})
            res.raise_for_status()
        except requests.exceptions.RequestException as e:
            exception("Thread Message Error", e)

    egg = app.data_cache.html.html[year][num]["ee"]

    return render_template(
        "link_complete.html",
        year=year,
        img=user["img"],
        num=num,
        guild=guild_id,
        channel=channel_id,
        egg=egg,
    )
