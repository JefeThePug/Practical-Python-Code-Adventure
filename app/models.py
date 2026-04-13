from sqlalchemy import ARRAY, Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


class DiscordID(db.Model):
    __tablename__ = "discord_ids"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    year: Mapped[str] = mapped_column(String(4), nullable=False)
    name: Mapped[str] = mapped_column(String(10), nullable=False)
    discord_id: Mapped[str] = mapped_column(String(20), nullable=False)


class MainEntry(db.Model):
    __tablename__ = "main_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    year: Mapped[str] = mapped_column(String(4), nullable=False)
    val: Mapped[int] = mapped_column(Integer, nullable=False)
    ee: Mapped[str | None] = mapped_column(Text)

    sub_entries: Mapped[list["SubEntry"]] = relationship(
        "SubEntry",
        back_populates="main_entry",
        cascade="all, delete-orphan",
    )


class SubEntry(db.Model):
    __tablename__ = "sub_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    main_entry_id: Mapped[int] = mapped_column(
        ForeignKey("main_entries.id", ondelete="CASCADE")
    )
    part: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text)
    instructions: Mapped[str] = mapped_column(Text)
    input_type: Mapped[str] = mapped_column(Text)
    form: Mapped[str] = mapped_column(Text)
    solution: Mapped[str] = mapped_column(Text)

    # Define the relationship
    main_entry: Mapped[MainEntry] = relationship(
        "MainEntry",
        back_populates="sub_entries",
    )


class Obfuscation(db.Model):
    __tablename__ = "obfuscation"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    year: Mapped[str] = mapped_column(String(4), nullable=False)
    val: Mapped[int] = mapped_column(Integer, nullable=False)
    obfuscated_key: Mapped[str] = mapped_column(String(255), nullable=False)
    html_key: Mapped[str] = mapped_column(String(255), nullable=False)


class User(db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    name: Mapped[str | None] = mapped_column(String(50))
    github: Mapped[str | None] = mapped_column(String(50))

    progress: Mapped[list["Progress"]] = relationship(
        "Progress",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Progress(db.Model):
    __tablename__ = "progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    year: Mapped[str] = mapped_column(String(4), nullable=False)
    c1: Mapped[list[bool]] = mapped_column(ARRAY(Boolean))
    c2: Mapped[list[bool]] = mapped_column(ARRAY(Boolean))
    c3: Mapped[list[bool]] = mapped_column(ARRAY(Boolean))
    c4: Mapped[list[bool]] = mapped_column(ARRAY(Boolean))
    c5: Mapped[list[bool]] = mapped_column(ARRAY(Boolean))
    c6: Mapped[list[bool]] = mapped_column(ARRAY(Boolean))
    c7: Mapped[list[bool]] = mapped_column(ARRAY(Boolean))
    c8: Mapped[list[bool]] = mapped_column(ARRAY(Boolean))
    c9: Mapped[list[bool]] = mapped_column(ARRAY(Boolean))
    c10: Mapped[list[bool]] = mapped_column(ARRAY(Boolean))

    # Define the relationship
    user: Mapped[User] = relationship("User", back_populates="progress")

    def challenge_states(self) -> list[list[bool]]:
        """Return c1-c10 completion flags for a Progress record."""
        return [getattr(self, f"c{i}") for i in range(1, 11)]


class Solution(db.Model):
    __tablename__ = "solutions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    year: Mapped[str] = mapped_column(String(4), nullable=False)
    val: Mapped[int] = mapped_column(Integer, nullable=False)
    part1: Mapped[str] = mapped_column(Text, nullable=False)
    part2: Mapped[str] = mapped_column(Text, nullable=False)


class Permission(db.Model):
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(String(20), nullable=False)


class Release(db.Model):
    __tablename__ = "releases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    year: Mapped[str] = mapped_column(String(4), nullable=False)
    release_number: Mapped[int] = mapped_column(Integer, nullable=False)


class Sponsor(db.Model):
    __tablename__ = "sponsors"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[str] = mapped_column(String(10), nullable=False)
    website: Mapped[str | None] = mapped_column(Text)
    image: Mapped[str | None] = mapped_column(Text)
    blurb: Mapped[str | None] = mapped_column(Text)
    disabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
