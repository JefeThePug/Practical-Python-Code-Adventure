import json
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from flask import Flask
from app.models import db, User, Progress

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

    old_rows = fetch_old_progress(engine)
    drop_tables(engine)
    run_setup(admin_id)
    migrate_user_data(old_rows)


def check_args():
    if len(sys.argv) != 2:
        sys.exit(
            "\nPlease include your administrator Discord ID.\n"
            "Usage: python update.py <admin_discord_user_id>"
        )
    return sys.argv[1].strip()


def fetch_old_progress(engine):
    with engine.begin() as conn:
        result = conn.execute(text("SELECT * FROM progress"))
        rows = [dict(row._mapping) for row in result]

    print(f"Fetched {len(rows)} old progress rows.")
    return rows


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


def migrate_user_data(old_rows):
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
    db.init_app(app)

    def parse(val):
        if val is None:
            return [False, False]
        if isinstance(val, str):
            return json.loads(val)
        return val

    skipped = 0
    migrated = 0

    with app.app_context():
        for row in old_rows:
            if all(parse(row.get(f"c{i}")) == [False, False] for i in range(1, 11)):
                skipped += 1
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
            migrated += 1

        db.session.commit()
    print(f"Migrated: {migrated}")
    print(f"Skipped (no progress): {skipped}")


if __name__ == "__main__":
    main()
    print(
        "Database update and setup complete.\nAfter logging in with your administrator account, "
        "go to the Admin dashboard (/admin) to customize this app for your server."
    )
