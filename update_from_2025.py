import json
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask
from sqlalchemy import create_engine, text

from app.models import DiscordID, Progress, Release, User, db

load_dotenv(Path(__file__).resolve().parent / ".env")

POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_SERVER = os.getenv("POSTGRES_SERVER")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
DATABASE_NAME = os.getenv("DATABASE_NAME")

DATABASE_URL = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_SERVER}:{POSTGRES_PORT}/{DATABASE_NAME}"
)


def main():
    admin_id = check_args()
    engine = create_engine(DATABASE_URL)
    progress, discord, release = fetch_old_data(engine)
    drop_tables(engine)
    run_setup(admin_id)
    migrate_user_data(progress, discord, release)


def check_args():
    if len(sys.argv) != 2:
        sys.exit(
            "\nPlease include your administrator Discord ID.\n"
            "Usage: python update.py <admin_discord_user_id>"
        )
    return sys.argv[1].strip()


def fetch_old_data(engine):
    with engine.begin() as conn:
        progress_result = conn.execute(text("SELECT * FROM progress"))
        discord_result = conn.execute(text("SELECT * FROM discord_ids"))
        progress = [dict(row._mapping) for row in progress_result]
        discord = [dict(row._mapping) for row in discord_result]
        release_value = (
            conn.execute(text("SELECT release.release FROM release")).scalar() or 0
        )
    print(
        f"Fetched {len(progress)} progress rows, {len(discord)} Discord IDs, and 2025 release."
    )
    return progress, discord, release_value


def drop_tables(engine):
    with engine.begin() as conn:
        result = conn.execute(
            text(
                """
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'public'
                """
            )
        )

        tables = [row[0] for row in result]

        if not tables:
            print("No tables to drop.")
            return

        print(f"Dropping {len(tables)} table(s): {', '.join(tables)}")

        for table in tables:
            conn.execute(text(f'DROP TABLE "{table}" CASCADE'))


def run_setup(admin_id: str):
    print("Running setup.py...\n")

    subprocess.run(
        [sys.executable, "setup.py", admin_id],
        check=True,
    )


def migrate_user_data(old_progress, old_discord, release_num):
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
    db.init_app(app)

    def parse(val):
        if val is None:
            return [False, False]
        if isinstance(val, str):
            return json.loads(val)
        return val

    progress_skipped = 0
    progress_migrated = 0

    with app.app_context():
        # Add users with progress
        for row in old_progress:
            if all(parse(row.get(f"c{i}")) == [False, False] for i in range(1, 11)):
                progress_skipped += 1
                continue

            discord_id = row["user_id"]
            user = User.query.filter_by(user_id=discord_id).one_or_none()

            if not user:
                user = User(
                    user_id=discord_id,  # type: ignore
                    name=row.get("name", ""),  # type: ignore
                    github=row.get("github", ""),  # type: ignore
                )
                db.session.add(user)
                db.session.flush()

            progress = Progress(
                user_id=user.id,  # type: ignore
                year="2025",  # type: ignore
                **{f"c{i}": parse(row.get(f"c{i}")) for i in range(1, 11)},
            )
            db.session.add(progress)
            progress_migrated += 1

        # Update previous Discord IDs and 2025 release number
        for row in old_discord:
            name = row.get("name", "")
            year = "0" if name == "guild" else "2025"
            db.session.query(DiscordID).filter_by(year=year, name=name).update(
                {"discord_id": row.get("discord_id", "")}
            )

        db.session.query(Release).filter_by(year="2025").update(
            {"release_number": release_num}
        )

        db.session.commit()
    print(f"Migrated: {progress_migrated} users, all discord IDs, and 2025 Release")
    print(f"Users skipped (due to no challenge progress): {progress_skipped}")


if __name__ == "__main__":
    main()
    print(
        "Database update and setup complete.\nAfter logging in with your administrator account, "
        "go to the Admin dashboard (/admin) to customize this app for your server."
    )
