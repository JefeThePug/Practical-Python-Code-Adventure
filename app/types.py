from typing import TYPE_CHECKING, TypedDict
from datetime import datetime

from flask import Flask
from itsdangerous import URLSafeTimedSerializer


if TYPE_CHECKING:
    from app.data_access import DataAccess


class AppFlask(Flask):
    data_access: "DataAccess"
    serializer: URLSafeTimedSerializer


class FanArtRow(TypedDict):
    name: str | None
    profile: str | None
    media_type: str
    media_link: str
    message: str | None


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
    dnd: bool
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
    name: str | None
    user_id: str
    github: str | None
    progress: list[list[bool]]


class ChampionRow(TypedDict):
    name: str | None
    github: str | None
    complete: datetime | None


class LeaderboardRow(TypedDict):
    id: int
    name: str
    is_creator: bool
    member_count: int


class LeaderboardMemberRow(TypedDict):
    name: str | None
    progress: list[list[bool]]
    done: int
    complete: datetime | None
