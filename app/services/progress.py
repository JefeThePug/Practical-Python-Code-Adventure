from flask import request, session

from app.appctx import get_app
from app.types import ProgressPayload


def sync_progress(year: str, user_id: str) -> None:
    """Synchronize the user's progress from the database into the session.
    Loads the user's progress via the DataCache and stores it in the Flask
    session so request handlers and templates can access it without
    additional database queries.
    Args:
        year (str): Current year.
        user_id (str): The Discord user ID.
    """
    session["progress"] = get_app().data_cache.load_progress(year, user_id)


def set_progress(challenge_num: int, progress: int) -> str | None:
    """Update the progress for the current user in the database.
    Args:
        challenge_num (int): The challenge number.
        progress (int): The specific progress index (0 or 1).
    Returns:
        str | None: The serialized progress if user is not logged in, otherwise None.
    """
    if "user_data" in session:
        # Change database and update Data Cache
        get_app().data_cache.update_progress(
            session["year"],
            session["user_data"]["id"],
            challenge_num,
            progress,
        )
        sync_progress(session["year"], session["user_data"]["id"])
        return None
    else:
        # Alter Browser Cookies
        dumped = get_app().serializer.dumps(f"{challenge_num}{'AB'[progress]}")
        match dumped:
            case bytes() | bytearray():
                return dumped.decode("utf-8")
            case memoryview():
                return dumped.tobytes().decode("utf-8")
            case str():
                return dumped
            case _:
                return str(dumped)


def get_progress() -> ProgressPayload:
    """Retrieve the progress of the user.
    Returns:
        dict: A dictionary containing user progress and session information.
    """
    if "user_data" in session:
        # Retrieve information from Flask session and Data Cache
        sync_progress(session["year"], session["user_data"]["id"])
        return {
            "id": session["user_data"]["id"],
            "img": session["user_data"]["img"],
            "progress": session["progress"],
            "rockets": [session["progress"][f"c{i}"] for i in range(1, 11)],
        }
    # Else, retrieve information from Browser Cookies
    cookies = [*request.cookies.keys()]
    s = [get_app().serializer.loads(x) for x in cookies if len(x) > 40]
    rockets = [[f"{n}{p}" in s for p in "AB"] for n in range(1, 11)]
    progress = {f"c{i}": r for i, r in enumerate(rockets, 1)}
    return {
        "id": None,
        "img": "no_img.png",
        "progress": progress,
        "rockets": rockets,
    }
