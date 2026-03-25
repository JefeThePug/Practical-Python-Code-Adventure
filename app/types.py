from typing import TYPE_CHECKING, TypedDict

from flask import Flask
from itsdangerous import URLSafeTimedSerializer

if TYPE_CHECKING:
    from app.cache import DataCache


class AppFlask(Flask):
    data_cache: "DataCache"
    serializer: URLSafeTimedSerializer


class ProgressPayload(TypedDict):
    id: str | None
    img: str
    progress: dict[str, list[bool]]
    rockets: list[list[bool]]


class SponsorRow(TypedDict):
    id: int
    name: str
    type: str
    website: str | None
    image: str | None
    blurb: str | None
    disabled: bool
    bucket: str


class UserRow(TypedDict):
    id: int
    user_id: str
    name: str | None
    github: str | None
    c1: list[bool]
    c2: list[bool]
    c3: list[bool]
    c4: list[bool]
    c5: list[bool]
    c6: list[bool]
    c7: list[bool]
    c8: list[bool]
    c9: list[bool]
    c10: list[bool]


class GlanceRow(TypedDict):
    name: str
    user_id: str
    progress: list[list[bool]]
