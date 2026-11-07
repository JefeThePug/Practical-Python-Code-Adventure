from datetime import datetime, timezone

from sqlalchemy import (
    ARRAY,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    event,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator

from app.extensions import db


class UTCDateTime(TypeDecorator):
    """timestamptz that rejects naive datetimes and normalizes aware ones to UTC."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("Naive datetime not allowed; use an aware datetime")
        return value.astimezone(timezone.utc)


def _challenge_col():
    """boolean[] column defaulting to {false,false}, as in the SQL schema."""
    return mapped_column(
        ARRAY(Boolean),
        nullable=False,
        server_default=text("ARRAY[false,false]"),
    )


class DiscordID(db.Model):
    __tablename__ = "discord_ids"
    __table_args__ = (UniqueConstraint("year", "name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    year: Mapped[str] = mapped_column(String(4), nullable=False)
    name: Mapped[str] = mapped_column(String(10), nullable=False)
    discord_id: Mapped[str] = mapped_column(String(20), nullable=False)

    def __init__(self, *, year: str, name: str, discord_id: str) -> None:
        self.year = year
        self.name = name
        self.discord_id = discord_id


class MainEntry(db.Model):
    __tablename__ = "main_entries"
    __table_args__ = (UniqueConstraint("year", "val"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    year: Mapped[str] = mapped_column(String(4), nullable=False)
    val: Mapped[int] = mapped_column(Integer, nullable=False)
    ee: Mapped[str | None] = mapped_column(Text)

    sub_entries: Mapped[list["SubEntry"]] = relationship(
        "SubEntry",
        back_populates="main_entry",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __init__(self, *, year: str, val: int, ee: str | None = None) -> None:
        self.year = year
        self.val = val
        self.ee = ee


class SubEntry(db.Model):
    __tablename__ = "sub_entries"
    __table_args__ = (UniqueConstraint("main_entry_id", "part"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    main_entry_id: Mapped[int] = mapped_column(
        ForeignKey("main_entries.id", ondelete="CASCADE"), nullable=False
    )
    part: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    instructions: Mapped[str] = mapped_column(Text, nullable=False)
    input_type: Mapped[str] = mapped_column(Text, nullable=False)
    form: Mapped[str] = mapped_column(Text, nullable=False)
    solution: Mapped[str] = mapped_column(Text, nullable=False)

    main_entry: Mapped[MainEntry] = relationship(
        "MainEntry", back_populates="sub_entries"
    )

    def __init__(
        self,
        *,
        main_entry_id: int,
        part: int,
        title: str,
        content: str,
        instructions: str,
        input_type: str,
        form: str,
        solution: str,
    ) -> None:
        self.main_entry_id = main_entry_id
        self.part = part
        self.title = title
        self.content = content
        self.instructions = instructions
        self.input_type = input_type
        self.form = form
        self.solution = solution


class Obfuscation(db.Model):
    __tablename__ = "obfuscation"
    __table_args__ = (UniqueConstraint("year", "val"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    year: Mapped[str] = mapped_column(String(4), nullable=False)
    val: Mapped[int] = mapped_column(Integer, nullable=False)
    obfuscated_key: Mapped[str] = mapped_column(String(255), nullable=False)
    html_key: Mapped[str] = mapped_column(String(255), nullable=False)

    def __init__(
        self, *, year: str, val: int, obfuscated_key: str, html_key: str
    ) -> None:
        self.year = year
        self.val = val
        self.obfuscated_key = obfuscated_key
        self.html_key = html_key


class User(db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    name: Mapped[str | None] = mapped_column(String(50))
    github: Mapped[str | None] = mapped_column(String(50))
    dnd: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=text("false"), nullable=False
    )

    progress: Mapped[list["Progress"]] = relationship(
        "Progress",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __init__(
        self,
        user_id: str,
        *,
        name: str | None = None,
        github: str | None = None,
        dnd: bool = False,
    ) -> None:
        self.user_id = user_id
        self.name = name
        self.github = github
        self.dnd = dnd


class Progress(db.Model):
    __tablename__ = "progress"
    __table_args__ = (
        UniqueConstraint("user_id", "year"),
        *(
            CheckConstraint(f"cardinality(c{i}) = 2", name=f"progress_c{i}_len")
            for i in range(1, 11)
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    year: Mapped[str] = mapped_column(String(4), nullable=False)
    c1: Mapped[list[bool]] = _challenge_col()
    c2: Mapped[list[bool]] = _challenge_col()
    c3: Mapped[list[bool]] = _challenge_col()
    c4: Mapped[list[bool]] = _challenge_col()
    c5: Mapped[list[bool]] = _challenge_col()
    c6: Mapped[list[bool]] = _challenge_col()
    c7: Mapped[list[bool]] = _challenge_col()
    c8: Mapped[list[bool]] = _challenge_col()
    c9: Mapped[list[bool]] = _challenge_col()
    c10: Mapped[list[bool]] = _challenge_col()
    completed_datetime: Mapped[datetime | None] = mapped_column(UTCDateTime)

    user: Mapped[User] = relationship("User", back_populates="progress")

    def __init__(
        self,
        *,
        user_id: int,
        year: str,
        completed_datetime: datetime | None = None,
    ) -> None:
        self.user_id = user_id
        self.year = year
        self.completed_datetime = completed_datetime

    def is_complete(self) -> bool:
        """True if every part of every challenge is done."""
        return all(s and all(s) for s in self.challenge_states())

    def challenge_states(self) -> list[list[bool]]:
        """Return c1-c10 completion flags for a Progress record."""
        return [getattr(self, f"c{i}") for i in range(1, 11)]


@event.listens_for(Progress, "before_insert")
@event.listens_for(Progress, "before_update")
def _stamp_completed(mapper, connection, target: Progress) -> None:
    """Keep completed_datetime in step with whether every challenge is complete."""
    complete = target.is_complete()
    if complete and target.completed_datetime is None:
        target.completed_datetime = datetime.now(timezone.utc)
    elif not complete and target.completed_datetime is not None:
        target.completed_datetime = None


class Solution(db.Model):
    __tablename__ = "solutions"
    __table_args__ = (UniqueConstraint("year", "val"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    year: Mapped[str] = mapped_column(String(4), nullable=False)
    val: Mapped[int] = mapped_column(Integer, nullable=False)
    part1: Mapped[str] = mapped_column(Text, nullable=False)
    part2: Mapped[str] = mapped_column(Text, nullable=False)

    def __init__(self, *, year: str, val: int, part1: str, part2: str) -> None:
        self.year = year
        self.val = val
        self.part1 = part1
        self.part2 = part2


class Permission(db.Model):
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)

    def __init__(self, user_id: str) -> None:
        self.user_id = user_id


class ReleaseYear(db.Model):
    __tablename__ = "release_years"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    year: Mapped[str] = mapped_column(String(4), nullable=False, unique=True)
    all_on: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=text("false"), nullable=False
    )

    releases: Mapped[list["Release"]] = relationship(
        "Release",
        back_populates="release_year",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __init__(self, year: str, *, all_on: bool = False) -> None:
        self.year = year
        self.all_on = all_on
        self.releases = [Release(n) for n in range(1, 11)]


class Release(db.Model):
    __tablename__ = "releases"
    __table_args__ = (
        UniqueConstraint("year_id", "number"),
        CheckConstraint("number BETWEEN 1 AND 10"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    year_id: Mapped[int] = mapped_column(
        ForeignKey("release_years.id", ondelete="CASCADE"), nullable=False
    )
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    release_at: Mapped[datetime | None] = mapped_column(UTCDateTime)

    release_year: Mapped[ReleaseYear] = relationship(
        "ReleaseYear", back_populates="releases"
    )

    def __init__(self, number: int, release_at: datetime | None = None) -> None:
        self.number = number
        self.release_at = release_at


class Sponsor(db.Model):
    __tablename__ = "sponsors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[str] = mapped_column(String(10), nullable=False)
    website: Mapped[str | None] = mapped_column(Text)
    image: Mapped[str | None] = mapped_column(Text)
    blurb: Mapped[str | None] = mapped_column(Text)
    disabled: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=text("false"), nullable=False
    )

    def __init__(
        self,
        *,
        name: str,
        type: str,
        website: str | None = None,
        image: str | None = None,
        blurb: str | None = None,
        disabled: bool = False,
    ) -> None:
        self.name = name
        self.type = type
        self.website = website
        self.image = image
        self.blurb = blurb
        self.disabled = disabled


class Leaderboard(db.Model):
    __tablename__ = "leaderboards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    creator: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )

    members: Mapped[list["LeaderboardMember"]] = relationship(
        "LeaderboardMember",
        back_populates="leaderboard",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __init__(self, *, name: str, creator: int) -> None:
        self.name = name
        self.creator = creator


class LeaderboardMember(db.Model):
    __tablename__ = "leaderboard_members"
    __table_args__ = (
        UniqueConstraint("leaderboard_id", "user_id"),
        Index("leaderboard_members_user_idx", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    leaderboard_id: Mapped[int] = mapped_column(
        ForeignKey("leaderboards.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    leaderboard: Mapped[Leaderboard] = relationship(
        "Leaderboard", back_populates="members"
    )
    user: Mapped[User] = relationship("User")

    def __init__(self, *, leaderboard_id: int, user_id: int) -> None:
        self.leaderboard_id = leaderboard_id
        self.user_id = user_id


class FanArt(db.Model):
    __tablename__ = "fanart"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    profile: Mapped[str | None] = mapped_column(String(100))
    media_type: Mapped[str] = mapped_column(
        String(10), nullable=False, default="img", server_default=text("'img'")
    )
    media_link: Mapped[str] = mapped_column(String(100), nullable=False)
    message: Mapped[str | None] = mapped_column(Text)

    def __init__(
        self,
        *,
        name: str,
        media_link: str,
        profile: str | None = None,
        media_type: str = "img",
        message: str | None = None,
    ) -> None:
        self.name = name
        self.profile = profile
        self.media_type = media_type
        self.media_link = media_link
        self.message = message
