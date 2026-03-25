from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


class DiscordID(db.Model):
    __tablename__ = "discord_ids"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    year: Mapped[str] = mapped_column(db.String(4), nullable=False)
    name: Mapped[str] = mapped_column(db.String(10), nullable=False)
    discord_id: Mapped[str] = mapped_column(db.String(20), nullable=False)


class MainEntry(db.Model):
    __tablename__ = "main_entries"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    year: Mapped[str] = mapped_column(db.String(4), nullable=False)
    val: Mapped[int] = mapped_column(db.Integer, nullable=False)
    ee: Mapped[str | None] = mapped_column(db.Text)

    sub_entries: Mapped[list["SubEntry"]] = relationship(
        "SubEntry",
        back_populates="main_entry",
        cascade="all, delete-orphan",
    )


class SubEntry(db.Model):
    __tablename__ = "sub_entries"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    main_entry_id: Mapped[int] = mapped_column(
        ForeignKey("main_entries.id", ondelete="CASCADE")
    )
    part: Mapped[int] = mapped_column(db.Integer)
    title: Mapped[str] = mapped_column(db.Text)
    content: Mapped[str] = mapped_column(db.Text)
    instructions: Mapped[str] = mapped_column(db.Text)
    input_type: Mapped[str] = mapped_column(db.Text)
    form: Mapped[str] = mapped_column(db.Text)
    solution: Mapped[str] = mapped_column(db.Text)

    # Define the relationship
    main_entry: Mapped[MainEntry] = relationship(
        "MainEntry",
        back_populates="sub_entries",
    )


class Obfuscation(db.Model):
    __tablename__ = "obfuscation"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    year: Mapped[str] = mapped_column(db.String(4), nullable=False)
    val: Mapped[int] = mapped_column(db.Integer, nullable=False)
    obfuscated_key: Mapped[str] = mapped_column(db.String(255), nullable=False)
    html_key: Mapped[str] = mapped_column(db.String(255), nullable=False)


class User(db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(db.String(20), nullable=False, unique=True)
    name: Mapped[str | None] = mapped_column(db.String(50))
    github: Mapped[str | None] = mapped_column(db.String(50))

    progress: Mapped[list["Progress"]] = relationship(
        "Progress",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Progress(db.Model):
    __tablename__ = "progress"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    year: Mapped[str] = mapped_column(db.String(4), nullable=False)
    c1: Mapped[list[bool]] = mapped_column(db.ARRAY(db.Boolean))
    c2: Mapped[list[bool]] = mapped_column(db.ARRAY(db.Boolean))
    c3: Mapped[list[bool]] = mapped_column(db.ARRAY(db.Boolean))
    c4: Mapped[list[bool]] = mapped_column(db.ARRAY(db.Boolean))
    c5: Mapped[list[bool]] = mapped_column(db.ARRAY(db.Boolean))
    c6: Mapped[list[bool]] = mapped_column(db.ARRAY(db.Boolean))
    c7: Mapped[list[bool]] = mapped_column(db.ARRAY(db.Boolean))
    c8: Mapped[list[bool]] = mapped_column(db.ARRAY(db.Boolean))
    c9: Mapped[list[bool]] = mapped_column(db.ARRAY(db.Boolean))
    c10: Mapped[list[bool]] = mapped_column(db.ARRAY(db.Boolean))

    # Define the relationship
    user: Mapped[User] = relationship("User", back_populates="progress")

    def challenge_states(self) -> list[list[bool]]:
        """Return c1-c10 completion flags for a Progress record."""
        return [getattr(self, f"c{i}") for i in range(1, 11)]


class Solution(db.Model):
    __tablename__ = "solutions"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    year: Mapped[str] = mapped_column(db.String(4), nullable=False)
    val: Mapped[int] = mapped_column(db.Integer, nullable=False)
    part1: Mapped[str] = mapped_column(db.Text, nullable=False)
    part2: Mapped[str] = mapped_column(db.Text, nullable=False)


class Permission(db.Model):
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(db.String(20), nullable=False)


class Release(db.Model):
    __tablename__ = "releases"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    year: Mapped[str] = mapped_column(db.String(4), nullable=False)
    release_number: Mapped[int] = mapped_column(db.Integer, nullable=False)


class Sponsor(db.Model):
    __tablename__ = "sponsors"
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(100), nullable=False)
    type: Mapped[str] = mapped_column(db.String(10), nullable=False)
    website: Mapped[str | None] = mapped_column(db.Text)
    image: Mapped[str | None] = mapped_column(db.Text)
    blurb: Mapped[str | None] = mapped_column(db.Text)
    disabled: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
