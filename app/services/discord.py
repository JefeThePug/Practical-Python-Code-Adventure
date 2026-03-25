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
