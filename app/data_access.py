from datetime import datetime
from typing import Any, ClassVar, Literal, cast

from flask import flash, session
from sqlalchemy import delete, func, insert
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import aliased, contains_eager, selectinload

from app.appctx import exception, get_app, log_info
from app.extensions import db
from app.types import (
    ChampionRow,
    FanArtRow,
    GlanceRow,
    LeaderboardRow,
    LeaderboardMemberRow,
    SponsorRow,
    UserRow,
)

from .models import (
    DiscordID,
    FanArt,
    MainEntry,
    Leaderboard,
    LeaderboardMember,
    Obfuscation,
    Permission,
    Progress,
    ReleaseYear,
    Solution,
    Sponsor,
    User,
)


def flash_msg(message: str, *, success: bool = True) -> None:
    """Create a Flash message."""

    flash(message, "success" if success else "error")


def fail(e: Exception, action: str, *, show_details: bool = True) -> bool:
    """Roll back, flash a message and log. Always returns False.

    ValueError messages are ours, so they're always shown. Database errors are
    shown only with show_details=True (admin pages); otherwise users get a
    generic message.
    """
    db.session.rollback()
    if isinstance(e, ValueError) or show_details:
        flash_msg(f"Failed: {e}", success=False)
    else:
        flash_msg("Something went wrong. Please try again.", success=False)
    if not isinstance(e, ValueError):
        exception(f"{action} failed", e)
    return False


class AdminSettings:
    """Get and manage admin-controlled reference tables and settings."""

    RPI: ClassVar[set[str]] = {"609283782897303554"}
    TYPE_MAP: ClassVar[dict[str, str]] = {
        "pioneer": "t3",
        "explorer": "t2",
        "pathfinder": "t1",
        "wayfarer": "t1",
    }
    SPONSOR_FIELDS: ClassVar[
        tuple[Literal["name", "type", "website", "image", "blurb", "disabled"], ...]
    ] = ("name", "type", "website", "image", "blurb", "disabled")
    FAN_ART_FIELDS: ClassVar[
        tuple[Literal["name", "profile", "media_type", "media_link", "message"], ...]
    ] = ("name", "profile", "media_type", "media_link", "message")

    def __init__(self):
        self.obfuscations: dict[str, dict[int | str, int | str]] = {}
        self.html_nums: dict[str, dict[int | str, int | str]] = {}

    def load_constants(self):
        """Load all constants from the database into memory (startup only)."""
        with get_app().app_context():
            obfuscations = db.session.execute(
                db.select(
                    Obfuscation.year,
                    Obfuscation.val,
                    Obfuscation.obfuscated_key,
                    Obfuscation.html_key,
                )
            )
            for year, val, obf_key, html_key in obfuscations:
                self.obfuscations.setdefault(year, {}).update(
                    {val: obf_key, obf_key: val}
                )
                self.html_nums.setdefault(year, {}).update(
                    {val: html_key, html_key: val}
                )

    def get_permissions(self, login: bool = False) -> list[str]:
        """Return permission user IDs excluding reserved system accounts."""
        permissions = db.session.scalars(db.select(Permission.user_id)).all()
        if login:
            return list(permissions)
        return [p for p in permissions if p not in self.RPI]

    def update_permissions(self, perms: list[str]) -> bool:
        """Replace the set of admin users in the database."""
        perm_set = set(perms) | self.RPI
        try:
            existing = set(db.session.scalars(db.select(Permission.user_id)).all())
            to_delete = existing - perm_set
            to_add = perm_set - existing

            if to_delete:
                db.session.execute(
                    delete(Permission).where(Permission.user_id.in_(to_delete))
                )
            if to_add:
                db.session.execute(
                    insert(Permission), [{"user_id": uid} for uid in to_add]
                )

            changed = bool(to_delete or to_add)
            db.session.commit()

            flash_msg("Admin list updated" if changed else "No changes made")
            return True
        except SQLAlchemyError as e:
            return fail(e, "Update admin settings")

    def get_discord(self, year: str) -> dict[str, dict[str, str]]:
        """Return discord IDs from the database for the root and for a given year."""
        discord_ids = {}
        for y, name, discord_id in db.session.execute(
            db.select(DiscordID.year, DiscordID.name, DiscordID.discord_id).where(
                DiscordID.year.in_(["0", year])
            )
        ):
            discord_ids.setdefault(y, {})[name] = discord_id
        return discord_ids

    def update_discord(self, values: dict[str, dict[str, str]]) -> bool:
        """Update Discord channel IDs in the database."""
        try:
            changed = False
            entries = db.session.scalars(
                db.select(DiscordID).where(DiscordID.year.in_(list(values)))
            ).all()
            for entry in entries:
                new = values[entry.year].get(entry.name, "")
                if entry.discord_id != new:
                    entry.discord_id = new
                    changed = True

            db.session.commit()

            flash_msg("Discord ID settings updated" if changed else "No changes made")
            return True
        except SQLAlchemyError as e:
            return fail(e, "Update Discord IDs")

    def get_fan_art(self) -> list[FanArtRow]:
        """Return all fan art entries."""
        return [
            {"id": f.id, **{k: getattr(f, k) for k in self.FAN_ART_FIELDS}}
            for f in db.session.scalars(db.select(FanArt).order_by(FanArt.id)).all()
        ]

    def update_fan_art(self, fan_art: list[FanArtRow]) -> bool:
        """Update fan art records in the database."""
        try:
            existing = {f.id: f for f in db.session.scalars(db.select(FanArt)).all()}
            for item in fan_art:
                values = {f: item.get(f) for f in self.FAN_ART_FIELDS}
                values["media_type"] = values["media_type"] or "img"

                row = existing.get(item.get("id"))
                if row:
                    for f, new in values.items():
                        if getattr(row, f) != new:
                            setattr(row, f, new)
                else:
                    db.session.add(
                        FanArt(
                            name=item["name"],
                            media_link=item["media_link"],
                            profile=item.get("profile"),
                            media_type=item.get("media_type") or "img",
                            message=item.get("message"),
                        )
                    )

            changed = bool(db.session.dirty or db.session.new)
            db.session.commit()

            flash_msg("Fan Art updated" if changed else "No changes made")
            return True
        except (SQLAlchemyError, KeyError) as e:
            return fail(e, "Update fan art")

    def get_sponsors(
        self, include_disabled: bool = False
    ) -> list[list[dict[str, Any]]]:
        """Return sponsors grouped by tier, optionally including disabled ones."""
        tiers = {"t1": [], "t2": [], "t3": []}
        for s in db.session.scalars(db.select(Sponsor)).all():
            if not include_disabled and s.disabled:
                continue
            bucket = self.TYPE_MAP.get(s.type, "t1")
            tiers[bucket].append(
                {
                    "id": s.id,
                    "type": s.type,
                    "bucket": bucket,
                    "name": s.name,
                    "website": s.website,
                    "disabled": s.disabled,
                    "image": s.image,
                    "blurb": s.blurb,
                }
            )
        return list(tiers.values())

    def update_sponsors(self, sponsors: list[SponsorRow]) -> bool:
        """Update sponsor records in the database."""
        try:
            existing = {s.id: s for s in db.session.scalars(db.select(Sponsor)).all()}
            for s in sponsors:
                row = existing.get(s["id"])
                if row:
                    for f in self.SPONSOR_FIELDS:
                        new = s[f]
                        if getattr(row, f) != new:
                            setattr(row, f, new)
                else:
                    db.session.add(
                        Sponsor(
                            name=s["name"],
                            type=s["type"],
                            website=s["website"],
                            image=s["image"],
                            blurb=s["blurb"],
                            disabled=s["disabled"],
                        )
                    )

            changed = bool(db.session.dirty or db.session.new)
            db.session.commit()

            flash_msg("Sponsors updated" if changed else "No changes made")
            return True
        except (SQLAlchemyError, KeyError) as e:
            return fail(e, "Update sponsors settings")

    def get_releases(self, year: str) -> dict[str, Any]:
        """Return all_on or release times for a given year."""
        ry = db.session.scalar(
            db.select(ReleaseYear)
            .where(ReleaseYear.year == year)
            .options(selectinload(ReleaseYear.releases))
        )
        if ry is None:
            return {"all_on": False, "releases": {n: None for n in range(1, 11)}}

        return {
            "all_on": ry.all_on,
            "releases": {r.number: r.release_at for r in ry.releases},
        }

    def update_releases(
        self,
        year: str,
        releases: dict[int, datetime | None],
        all_on: bool | None = None,
    ) -> bool:
        """
        Update the release schedule for one year.
        * If all_on is or becomes True, every stored time is cleared
        * and the releases argument is ignored.
        """
        try:
            ry = db.session.scalar(
                db.select(ReleaseYear)
                .where(ReleaseYear.year == year)
                .options(selectinload(ReleaseYear.releases))
            )
            if ry is None:
                ry = ReleaseYear(year)
                db.session.add(ry)

            if all_on is not None and ry.all_on != all_on:
                ry.all_on = all_on

            if ry.all_on:
                for rel in ry.releases:
                    if rel.release_at is not None:
                        rel.release_at = None
            else:
                by_number = {r.number: r for r in ry.releases}
                for number, release_at in releases.items():
                    rel = by_number.get(number)
                    if rel is None:
                        raise ValueError(f"Invalid release number {number}")
                    if rel.release_at != release_at:
                        rel.release_at = release_at

            changed = bool(db.session.dirty or db.session.new)
            db.session.commit()

            flash_msg(f"{year} releases updated" if changed else "No changes made")
            return True
        except (SQLAlchemyError, ValueError) as e:
            return fail(e, "Update releases")


class ChallengeContent:
    """Read and update challenge content and solutions."""

    HTML_FIELDS: ClassVar[
        tuple[
            Literal[
                "title", "content", "instructions", "input_type", "form", "solution"
            ],
            ...,
        ]
    ] = ("title", "content", "instructions", "input_type", "form", "solution")

    @staticmethod
    def normalize(s: str) -> str:
        """Normalize line endings to LF (\\n) for consistent storage and comparison."""
        return s.replace("\r\n", "\n").replace("\r", "\n")

    def get_html(self, year: str, week: int) -> dict[int | str, Any] | None:
        """Return HTML and Easter Egg for one week, or None if missing."""
        main = db.session.scalar(
            db.select(MainEntry)
            .where(MainEntry.year == year, MainEntry.val == week)
            .options(selectinload(MainEntry.sub_entries))
        )
        if main is None:
            return None

        week_data = {
            s.part: {f: getattr(s, f) for f in self.HTML_FIELDS}
            for s in main.sub_entries
        }
        week_data["ee"] = main.ee
        return week_data

    def update_html(
        self,
        year: str,
        week: int,
        fields: list[str],
        ee: str | None,
        parts: dict[int, dict[str, str]],
    ) -> bool:
        """Update challenge content for one week."""
        try:
            bad = set(fields) - set(self.HTML_FIELDS)
            if bad:
                raise ValueError(f"Invalid fields: {', '.join(sorted(bad))}")

            main = db.session.scalar(
                db.select(MainEntry)
                .where(MainEntry.year == year, MainEntry.val == week)
                .options(selectinload(MainEntry.sub_entries))
            )
            if main is None:
                raise ValueError("MainEntry not found")

            by_part = {s.part: s for s in main.sub_entries}
            if main.ee != ee:
                main.ee = ee
            for part, contents in parts.items():
                row = by_part.get(part)
                if row is None:
                    raise ValueError(f"SubEntry part {part} not found")
                for field in fields:
                    fixed = self.normalize(contents.get(field, ""))
                    if getattr(row, field) != fixed:
                        setattr(row, field, fixed)

            changed = bool(db.session.dirty)
            db.session.commit()

            flash_msg(f"{year}:#{week} Updated!" if changed else "No changes made")
            return True
        except (SQLAlchemyError, ValueError) as e:
            return fail(e, "Update HTML")

    def get_solution(self, year: str, week: int) -> dict[str, str] | None:
        """One week's solution, for checking a guess. None if missing."""
        row = db.session.execute(
            db.select(Solution.part1, Solution.part2).where(
                Solution.year == year, Solution.val == week
            )
        ).one_or_none()
        return None if row is None else {"part1": row.part1, "part2": row.part2}

    def get_solutions(self, year: str) -> dict[int, dict[str, str]]:
        """Every week's solution for one year, for the admin page."""
        rows = db.session.execute(
            db.select(Solution.val, Solution.part1, Solution.part2)
            .where(Solution.year == year)
            .order_by(Solution.val)
        )
        return {val: {"part1": a, "part2": b} for val, a, b in rows}

    def update_solutions(self, year: str, solutions: dict[int, dict[str, str]]) -> bool:
        """Update stored solutions for a year."""
        try:
            existing = {
                s.val: s
                for s in db.session.scalars(
                    db.select(Solution).where(Solution.year == year)
                ).all()
            }
            for val, parts in solutions.items():
                solution = existing.get(val)
                if solution is None:
                    raise ValueError(f"Solution not found for year={year}, val={val}")
                for part in ("part1", "part2"):
                    if part not in parts:
                        raise ValueError(f"Missing {part} for val={val}")
                    if getattr(solution, part) != parts[part]:
                        setattr(solution, part, parts[part])

            changed = bool(db.session.dirty)
            db.session.commit()

            flash_msg(
                "Solutions updated successfully" if changed else "No changes made"
            )
            return True
        except (SQLAlchemyError, ValueError) as e:
            return fail(e, "Update solutions")


class Leaderboards:
    """Create, join and read leaderboards."""

    @staticmethod
    def _user_pk(user_id: str) -> int:
        """Database ID for a Discord user ID. Raises ValueError if unknown."""
        pk = db.session.scalar(db.select(User.id).where(User.user_id == user_id))
        if pk is None:
            raise ValueError("User not found")
        return pk

    def get_for_user(self, user_id: str) -> list[LeaderboardRow]:
        """Every leaderboard this user is in."""
        uid = db.session.scalar(db.select(User.id).where(User.user_id == user_id))
        if uid is None:
            return []

        members = aliased(LeaderboardMember)
        member_count = (
            db.select(func.count(members.id))
            .where(members.leaderboard_id == Leaderboard.id)
            .scalar_subquery()
        )
        rows = db.session.execute(
            db.select(
                Leaderboard.id, Leaderboard.name, Leaderboard.creator, member_count
            )
            .join(LeaderboardMember, LeaderboardMember.leaderboard_id == Leaderboard.id)
            .where(LeaderboardMember.user_id == uid)
            .order_by(Leaderboard.name)
        ).all()
        return [
            {
                "id": lb_id,
                "name": name,
                "is_creator": creator == uid,
                "member_count": count,
            }
            for lb_id, name, creator, count in rows
        ]

    def get_members(self, name: str, year: str, pw: str) -> list[LeaderboardMemberRow]:
        """
        Members of one leaderboard, ranked, with their progress for a year.
        pw must be the Discord ID of someone in that board
        """
        board_id = db.session.scalar(
            db.select(Leaderboard.id)
            .join(LeaderboardMember, LeaderboardMember.leaderboard_id == Leaderboard.id)
            .join(User, User.id == LeaderboardMember.user_id)
            .where(Leaderboard.name == name.strip(), User.user_id == pw)
        )
        if board_id is None:
            return []

        rows = db.session.execute(
            db.select(User, Progress)
            .select_from(LeaderboardMember)
            .join(User, User.id == LeaderboardMember.user_id)
            .outerjoin(
                Progress, (Progress.user_id == User.id) & (Progress.year == year)
            )
            .where(LeaderboardMember.leaderboard_id == board_id)
        ).all()

        members = []
        for user, progress in rows:
            states = (
                progress.challenge_states()
                if progress
                else [[False, False] for _ in range(10)]
            )
            members.append(
                {
                    "user_id": user.user_id,
                    "name": user.name,
                    "progress": states,
                    "done": sum(sum(s) for s in states),
                    "complete": progress.completed_datetime if progress else None,
                }
            )

        return sorted(
            members,
            key=lambda m: (
                -m["done"],
                m["complete"] is None,
                m["complete"].timestamp() if m["complete"] else 0.0,
                m["name"] or "",
            ),
        )

    def create(self, user_id: str, name: str) -> bool:
        """Create a leaderboard (one per user). The creator is added as a member."""
        try:
            name = name.strip()
            if not 1 <= len(name) <= 50:
                raise ValueError("Name must be between 1 and 50 characters")

            uid = self._user_pk(user_id)
            if db.session.scalar(
                db.select(Leaderboard.id).where(Leaderboard.creator == uid)
            ):
                raise ValueError("You already have a leaderboard")
            if db.session.scalar(
                db.select(Leaderboard.id).where(Leaderboard.name == name)
            ):
                raise ValueError("That name is already taken")

            board = Leaderboard(name=name, creator=uid)
            db.session.add(board)
            db.session.flush()
            db.session.add(LeaderboardMember(leaderboard_id=board.id, user_id=uid))
            db.session.commit()

            flash_msg(f'Created leaderboard "{name}"')
            return True
        except (SQLAlchemyError, ValueError) as e:
            return fail(e, "Create leaderboard", show_details=False)

    def delete(self, user_id: str) -> bool:
        """Delete the user's own leaderboard. The database removes its members."""
        try:
            uid = self._user_pk(user_id)
            deleted = db.session.scalar(
                db.delete(Leaderboard)
                .where(Leaderboard.creator == uid)
                .returning(Leaderboard.id)
            )
            if deleted is None:
                raise ValueError("You don't have a leaderboard to delete")

            db.session.commit()

            flash_msg("Leaderboard deleted")
            return True
        except (SQLAlchemyError, ValueError) as e:
            return fail(e, "Delete leaderboard", show_details=False)

    def join(self, user_id: str, name: str) -> bool:
        """Join a leaderboard by its name."""
        try:
            uid = self._user_pk(user_id)
            board_id = db.session.scalar(
                db.select(Leaderboard.id).where(Leaderboard.name == name.strip())
            )
            if board_id is None:
                raise ValueError("Leaderboard not found")

            inserted = db.session.execute(
                pg_insert(LeaderboardMember)
                .values(leaderboard_id=board_id, user_id=uid)
                .on_conflict_do_nothing(index_elements=["leaderboard_id", "user_id"])
                .returning(LeaderboardMember.id)
            ).scalar_one_or_none()

            db.session.commit()

            flash_msg(
                f'Joined "{name.strip()}"'
                if inserted is not None
                else "You're already in that leaderboard"
            )
            return True
        except (SQLAlchemyError, ValueError) as e:
            return fail(e, "Join leaderboard", show_details=False)

    def leave(self, user_id: str, leaderboard_id: int) -> bool:
        """Leave a leaderboard. Creators delete theirs instead of leaving it."""
        try:
            uid = self._user_pk(user_id)
            creator = db.session.scalar(
                db.select(Leaderboard.creator).where(Leaderboard.id == leaderboard_id)
            )
            if creator == uid:
                raise ValueError(
                    "You created this leaderboard, so delete it instead of leaving"
                )

            left = db.session.scalar(
                db.delete(LeaderboardMember)
                .where(
                    LeaderboardMember.leaderboard_id == leaderboard_id,
                    LeaderboardMember.user_id == uid,
                )
                .returning(LeaderboardMember.id)
            )
            if left is None:
                raise ValueError("You're not in that leaderboard")

            db.session.commit()

            flash_msg("Left leaderboard")
            return True
        except (SQLAlchemyError, ValueError) as e:
            return fail(e, "Leave leaderboard", show_details=False)


class DataAccess:
    """High-level facade combining admin, HTML, leaderboard and user progress classes."""

    def __init__(self):
        self.admin = AdminSettings()
        self.html = ChallengeContent()
        self.leaderboards = Leaderboards()

    def load(self):
        """Load obfuscation constants from the database into a cache."""
        self.admin.load_constants()

    @staticmethod
    def _session_name() -> str | None:
        """Display name of the logged-in user, from the session."""
        return session.get("user_data", {}).get("username")

    @staticmethod
    def _clean_github(github: str | None) -> str | None:
        """Blank GitHub names are stored as NULL."""
        return (github or "").strip() or None

    @staticmethod
    def _resolve_dnd(github: str | None, dnd: bool) -> bool:
        """A stored GitHub name always implies dnd."""
        return dnd or github is not None

    @staticmethod
    def _get_or_create_user(
        user_id: str,
        name: str | None,
        github: str | None = None,
        dnd: bool = False,
    ) -> User:
        """Return the user with this Discord ID, creating it if missing."""
        github = DataAccess._clean_github(github)
        dnd = DataAccess._resolve_dnd(github, dnd)

        query = db.select(User).where(User.user_id == user_id)
        user = db.session.scalar(query)
        if user is None:
            created = db.session.execute(
                pg_insert(User)
                .values(user_id=user_id, name=name, github=github, dnd=dnd)
                .on_conflict_do_nothing(index_elements=["user_id"])
                .returning(User.id)
            ).scalar_one_or_none()
            if created is not None:
                log_info(f"User {name}:{user_id} (id={created}) added to database.")
            user = db.session.execute(query).scalar_one()
        return user

    @staticmethod
    def _get_or_create_progress(year: str, uid: int) -> Progress:
        """Return the progress row for a user and year, creating it if missing."""
        query = db.select(Progress).where(
            Progress.year == year, Progress.user_id == uid
        )
        progress = db.session.scalar(query)
        if progress is None:
            created = db.session.execute(
                pg_insert(Progress)
                .values(user_id=uid, year=year)
                .on_conflict_do_nothing(index_elements=["user_id", "year"])
                .returning(Progress.id)
            ).scalar_one_or_none()
            if created is not None:
                log_info(f"{year} progress for user {uid} added to database.")
            progress = db.session.execute(query).scalar_one()
        return progress

    @staticmethod
    def _progress(year: str) -> list[Progress]:
        """All progress rows for a year, excluding system accounts."""
        return list(
            db.session.scalars(
                db.select(Progress)
                .join(Progress.user)
                .where(
                    Progress.year == year,
                    User.user_id.not_in(list(AdminSettings.RPI)),
                )
                .options(contains_eager(Progress.user))
            ).all()
        )

    @staticmethod
    def get_progress(year: str, user_id: str) -> dict[str, list[bool]]:
        """Return a user's progress for a year, creating empty records if needed."""
        try:
            user = DataAccess._get_or_create_user(user_id, DataAccess._session_name())
            progress = DataAccess._get_or_create_progress(year, user.id)
            states = {f"c{i}": list(getattr(progress, f"c{i}")) for i in range(1, 11)}
            db.session.commit()
            return states
        except SQLAlchemyError as e:
            fail(e, f"Load progress for user {user_id}", show_details=False)
            return {}

    def update_progress(self, year: str, user: str, num: int, part: int) -> bool:
        """Mark one part (0 or 1) of one challenge (1-10) as complete."""
        try:
            if num not in range(1, 11) or part not in (0, 1):
                raise ValueError(f"Invalid challenge or part: {num=} {part=}")

            main = self._get_or_create_user(user, self._session_name())
            progress = self._get_or_create_progress(year, main.id)

            field = f"c{num}"
            challenge = list(getattr(progress, field))
            challenge[part] = True
            setattr(progress, field, challenge)

            db.session.commit()
            return True
        except (SQLAlchemyError, ValueError) as e:
            return fail(e, "Update progress")

    @staticmethod
    def get_glance(year: str) -> list[GlanceRow]:
        """Return a summary of each user's progress for a year."""
        try:
            return cast(
                list[GlanceRow],
                [
                    {
                        "user_id": p.user.user_id,
                        "name": p.user.name,
                        "github": p.user.github,
                        "progress": p.challenge_states(),
                    }
                    for p in DataAccess._progress(year)
                ],
            )
        except SQLAlchemyError as e:
            fail(e, "Fetching user progress", show_details=False)
            return []

    @staticmethod
    def get_all_champions(year: str) -> list[ChampionRow]:
        """Return users who completed every challenge for the given year."""
        try:
            return cast(
                list[ChampionRow],
                [
                    {
                        "name": p.user.name,
                        "github": p.user.github,
                        "complete": p.completed_datetime,
                    }
                    for p in DataAccess._progress(year)
                    if p.is_complete()
                ],
            )
        except SQLAlchemyError as e:
            fail(e, "Fetching champions", show_details=False)
            return []

    @staticmethod
    def update_champions(champions: list[dict[str, Any]]) -> bool:
        """Update GitHub usernames (and optionally dnd) for champion users."""
        try:
            wanted = {c["user_id"]: c for c in champions}
            changed = False
            for user in db.session.scalars(
                db.select(User).where(User.user_id.in_(list(wanted)))
            ).all():
                item = wanted[user.user_id]
                github = DataAccess._clean_github(item["github"])
                dnd = DataAccess._resolve_dnd(github, item.get("dnd", user.dnd))

                for field, new in (("github", github), ("dnd", dnd)):
                    if getattr(user, field) != new:
                        setattr(user, field, new)
                        changed = True

            db.session.commit()

            flash_msg("GitHub updated successfully" if changed else "No changes made")
            return True
        except (SQLAlchemyError, KeyError) as e:
            return fail(e, "Update champions")

    @staticmethod
    def get_user_id(user_id: str) -> int:
        """Return the database ID for a Discord user ID, or 0 if not found."""
        if not user_id.strip():
            return 0
        return db.session.scalar(db.select(User.id).where(User.user_id == user_id)) or 0

    def update_users(self, year: str, users: list[UserRow]) -> bool:
        """Create or update users and their progress records for a year."""
        try:
            changed = False
            user_map = {
                u.id: u
                for u in db.session.scalars(
                    db.select(User).where(User.id.in_([d["id"] for d in users]))
                ).all()
            }
            progress_map = {
                p.user_id: p
                for p in db.session.scalars(
                    db.select(Progress).where(
                        Progress.year == year,
                        Progress.user_id.in_(list(user_map)),
                    )
                ).all()
            }

            for data in users:
                name = (data["name"] or "").strip() or None
                github = self._clean_github(data["github"])
                user = user_map.get(data["id"])
                # dnd is optional: when not supplied, keep the stored value
                dnd = self._resolve_dnd(
                    github, data.get("dnd", user.dnd if user else False)
                )

                if not user:
                    changed = True
                    user = self._get_or_create_user(data["user_id"], name, github, dnd)

                progress = progress_map.get(user.id)
                if not progress:
                    changed = True
                    progress = self._get_or_create_progress(year, user.id)

                for field, new in (("name", name), ("github", github), ("dnd", dnd)):
                    if getattr(user, field) != new:
                        changed = True
                        setattr(user, field, new)

                for i in range(1, 11):
                    field = f"c{i}"
                    if getattr(progress, field) != data[field]:
                        changed = True
                        setattr(progress, field, data[field])

            db.session.commit()

            flash_msg("Progress updated" if changed else "No changes made")
            return True
        except (SQLAlchemyError, KeyError, ValueError) as e:
            return fail(e, "Update users")

    def delete_users(self, deletes: list[str]) -> bool:
        """Delete users and their progress completely."""
        try:
            deleted = db.session.scalars(
                delete(User).where(User.user_id.in_(deletes)).returning(User.id)
            ).all()
            if not deleted:
                raise ValueError("No matching users found in the database.")

            db.session.commit()

            flash_msg(f"{len(deleted)} user(s) deleted successfully")
            return True
        except (SQLAlchemyError, ValueError) as e:
            return fail(e, "Delete users")
