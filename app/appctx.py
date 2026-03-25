from typing import cast

from flask import current_app, has_app_context

from app.types import AppFlask


def get_app() -> AppFlask:
    return cast(AppFlask, current_app)


def warning(msg: str) -> None:
    if has_app_context():
        current_app.logger.warning(msg)
    else:
        print(msg)


def exception(msg: str, e: Exception | None = None) -> None:
    if has_app_context():
        current_app.logger.exception(f"{msg}: {e}")
    else:
        print(msg, e, sep="\n")


def log_info(msg: str) -> None:
    if has_app_context():
        current_app.logger.info(msg)
    else:
        print(msg)
