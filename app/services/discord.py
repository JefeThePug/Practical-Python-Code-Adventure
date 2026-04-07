import requests

from app.appctx import get_app


def exchange_code(code: str) -> dict:
    """Exchange a Discord OAuth2 authorization code for an access token.
    Sends the authorization code to Discord's OAuth2 token endpoint and
    returns the decoded JSON response containing the access token and
    related metadata.
    Args:
        code (str): The authorization code returned by Discord.
    Returns:
        dict: The JSON response from Discord, including access_token,
        token_type, expires_in, and scope.
    """
    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": get_app().config["DISCORD_REDIRECT_URI"],
        "client_id": get_app().config["DISCORD_CLIENT_ID"],
        "client_secret": get_app().config["DISCORD_CLIENT_SECRET"],
    }

    response = requests.post(
        "https://discord.com/api/oauth2/token",
        data=token_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    return response.json()


def get_avatar_url(user_data: dict) -> str:
    """"""
    avatar_hash = user_data.get("avatar")
    if not avatar_hash:
        return "images/no_img.png"

    ext = "gif" if avatar_hash.startswith("a_") else "png"
    return f"https://cdn.discordapp.com/avatars/{user_data['id']}/{avatar_hash}.{ext}"


def get_user_data(token: str) -> dict:
    """"""
    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get("https://discord.com/api/users/@me", headers=headers)
    res.raise_for_status()
    return res.json()
