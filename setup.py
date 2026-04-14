import base64
import hashlib
import json
import os
import sys
from pathlib import Path

import requests
import yaml
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM as Encryption
from dotenv import load_dotenv
from flask import Flask
from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.exc import SQLAlchemyError

load_dotenv(Path(__file__).resolve().parent / ".env")

from app.models import (  # noqa: E402
    DiscordID,
    MainEntry,
    Obfuscation,
    Permission,
    Progress,
    Release,
    Solution,
    Sponsor,
    SubEntry,
    User,
    db,
)

# Initialize Flask application
app = Flask(__name__)

# Configure SQLAlchemy database URI and settings
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_SERVER = os.getenv("POSTGRES_SERVER")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
DATABASE_NAME = os.getenv("DATABASE_NAME")
DATABASE_URL = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_SERVER}:{POSTGRES_PORT}/{DATABASE_NAME}"
)
ADMIN_URL = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_SERVER}:{POSTGRES_PORT}/postgres"
)

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

CREATED_TABLES = []


@event.listens_for(db.metadata, "after_create")
def receive_after_create(target, connection, tables, **kwargs):
    for table in tables:
        CREATED_TABLES.append(table.name)
        print(f"Table created: {table.name}")


def main():
    admin_id, latest_year = check_args()
    previous = check_database_exists()

    engine = create_engine(DATABASE_URL)
    backup = None

    if previous:
        with engine.connect() as conn:
            schema = detect_schema(conn)
            backup = fetch_data(conn, schema)

    db.init_app(app)

    with app.app_context():
        drop_tables(db.engine)
        create_missing_tables(db.engine)
        fill_permanent_data(admin_id, latest_year)

        if previous and backup:
            migrate_user_data(backup)
            print("Migration successful.")

        db.session.commit()


def check_args():
    admin_id = os.getenv("DISCORD_ADMIN_USER_ID", "")
    if not admin_id:
        sys.exit(
            "\nPlease include your administrator Discord ID.\n"
            "Usage: python update.py <admin_discord_user_id>"
        )
    latest_year = os.getenv("YEAR", "")
    if not latest_year:
        sys.exit("YEAR env var required")

    return admin_id, int(latest_year)


def check_database_exists():
    admin_engine = create_engine(ADMIN_URL)
    db_exists = False

    with admin_engine.connect() as conn:
        result = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :dbname"),
            {"dbname": DATABASE_NAME},
        )
        db_exists = result.fetchone() is not None

    if not db_exists:
        with admin_engine.connect() as conn:
            conn = conn.execution_options(isolation_level="AUTOCOMMIT")
            conn.execute(text(f"CREATE DATABASE {DATABASE_NAME}"))

    admin_engine.dispose()
    return db_exists


def detect_schema(conn):
    if table_exists(conn, "users") and table_exists(conn, "releases"):
        return "new"
    return "old"


def table_exists(conn, table_name):
    result = conn.execute(
        text(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_name = :name)"
        ),
        {"name": table_name},
    )
    return result.scalar()


def fetch_data(conn, schema):
    progress_rows = [
        dict(row._mapping) for row in conn.execute(text("SELECT * FROM progress"))
    ]
    discord_rows = [
        dict(row._mapping) for row in conn.execute(text("SELECT * FROM discord_ids"))
    ]
    permissions = [
        dict(row._mapping) for row in conn.execute(text("SELECT * FROM permissions"))
    ]
    users = []
    progress = []
    releases = []
    discord = []

    if schema == "old":
        release_value = conn.execute(
            text("SELECT release.release FROM release")
        ).scalar()
        releases = [{"year": "2025", "release_number": release_value or 0}]

        for row in discord_rows:
            discord.append(
                {"year": "2025", "name": row["name"], "discord_id": row["discord_id"]}
            )

        seen_users = set()

        for row in progress_rows:
            user_id = row["user_id"]
            parsed_progress = {f"c{i}": row[f"c{i}"] for i in range(1, 11)}
            if all(v == [False, False] for v in parsed_progress.values()):
                continue

            if user_id not in seen_users:
                users.append(
                    {
                        "user_id": user_id,
                        "name": row.get("name", ""),
                        "github": row.get("github", ""),
                    }
                )
                seen_users.add(user_id)

            progress.append(
                {
                    "reference": user_id,
                    "year": "2025",
                    **parsed_progress,
                }
            )

    elif schema == "new":
        users = [
            dict(row._mapping) for row in conn.execute(text("SELECT * FROM users"))
        ]
        releases = [
            dict(row._mapping) for row in conn.execute(text("SELECT * FROM releases"))
        ]
        discord = discord_rows
        id_to_user = {user["id"]: user["user_id"] for user in users}
        for row in progress_rows:
            progress.append(
                {
                    "reference": id_to_user[row["user_id"]],
                    "year": row["year"],
                    **{f"c{i}": row[f"c{i}"] for i in range(1, 11)},
                }
            )

    return {
        "users": users,
        "progress": progress,
        "discord_ids": discord,
        "permissions": permissions,
        "releases": releases,
    }


def drop_tables(engine):
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
    print("Reset public schema, clearing all tables.")


def create_missing_tables(engine):
    CREATED_TABLES.clear()
    db.metadata.create_all(bind=engine)

    if CREATED_TABLES:
        print(f"Success: {len(CREATED_TABLES)} new table(s) created.")
    else:
        print("No new tables needed; all schemas already exist.")


def fetch(url: str) -> requests.Response:
    res = requests.get(url, timeout=10)
    res.raise_for_status()
    return res


def fill_permanent_data(admin_id, latest_year):
    def decrypt(enc_b64: str, key: bytes) -> bytes:
        aes = Encryption(key)
        raw = base64.b64decode(enc_b64)
        return aes.decrypt(raw[:12], raw[12:], None)

    def process_json(to_load: str) -> dict[int, list | None]:
        url = base64.b64decode(to_load).decode()
        data = fetch(url).json()
        result = {}
        for year, enc in data.items():
            year = int(year)
            key_str = os.getenv(f"KEY{year}")
            if not key_str:
                print(f"Missing key for {year}")
                result[year] = None
                continue
            try:
                key = hashlib.sha256(key_str.encode()).digest()
                decrypted = decrypt(enc.strip(), key)
                result[year] = json.loads(decrypted.decode())
            except (InvalidTag, json.JSONDecodeError):
                print(f"Invalid data for {year}")
                result[year] = None
        return result

    releases = []
    for year in range(2025, latest_year + 1):
        r = Release()
        r.year = f"{year}"
        r.release_number = 0
        releases.append(r)
    db.session.add_all(releases)
    print("Inserted releases ✓")

    permissions = []
    for uid in ("609283782897303554", admin_id):
        p = Permission()
        p.user_id = uid
        permissions.append(p)
    db.session.add_all(permissions)
    print("Inserted permissions ✓")

    discord_ids = []
    for zeros in ("guild", "adventurer"):
        d = DiscordID()
        d.year = "0"
        d.name = zeros
        d.discord_id = ""
        discord_ids.append(d)
    for y in range(2025, latest_year + 1):
        for i in range(11):
            d = DiscordID()
            d.year = f"{y}"
            d.name = f"{i}" if i > 0 else "champion"
            d.discord_id = ""
            discord_ids.append(d)
    db.session.add_all(discord_ids)
    print("Inserted discord ids ✓")

    to_load = (
        "aHR0cHM6Ly9naXN0LmdpdGh1YnVzZXJjb250ZW50LmNvbS9KZWZlVGhlUHVnLzYzNG"
        "FhMjdkZDFmNGJkOTlhYWU4NDAzNjA1ZThhNWJiL3Jhdy9vYmZ1c2NhdGlvbi5qc29u"
    )
    results = process_json(to_load)
    rows = []
    for y in range(2025, latest_year + 1):
        for i, (k, h) in enumerate(results.get(y) or [], 1):
            o = Obfuscation()
            o.year = str(y)
            o.val = i
            o.obfuscated_key = k
            o.html_key = h
            rows.append(o)
    db.session.add_all(rows)
    print("Inserted obfuscation data ✓")

    to_load = (
        "aHR0cHM6Ly9naXN0LmdpdGh1YnVzZXJjb250ZW50LmNvbS9KZWZlVGhlUHVn"
        "L2M5NWFmY2IwOTFiY2JiODhmMDQ4NTRkMzZlYTMxOTRmL3Jhdy9lZS5qc29u"
    )
    results = process_json(to_load)
    rows = []
    for y in range(2025, latest_year + 1):
        for i, ee in enumerate(results.get(y) or [], 1):
            m = MainEntry()
            m.year = str(y)
            m.val = i
            m.ee = ee
            rows.append(m)
    db.session.add_all(rows)
    print("Inserted main entries ✓")

    to_load = (
        "aHR0cHM6Ly9naXN0LmdpdGh1YnVzZXJjb250ZW50LmNvbS9KZWZlVGhlUHVnLz"
        "c5YmM3OWMzMzkzOWFlNTRjYjEyYWQ3Yjc5NmFmNjk2L3Jhdy9odG1sLmpzb24="
    )
    url = base64.b64decode(to_load).decode()
    repos = fetch(url).json()

    parts = (
        base64.b64decode(
            "aHR0cHM6Ly9naXN0LmdpdGh1YnVzZXJjb250ZW50LmNvbS9KZWZlVGhlUHVnLw=="
        ).decode(),
        base64.b64decode("L3Jhdy8=").decode(),
    )

    for year, r in enumerate(repos, 2025):
        url = f"{r.join(parts)}{year}.txt"
        key_str = os.getenv(f"KEY{year}")
        if not key_str:
            print(f"Missing key for {year}")
            continue
        response = fetch(url)
        key = hashlib.sha256(key_str.encode()).digest()
        try:
            plaintext = decrypt(response.text.strip(), key)
            data = yaml.safe_load(plaintext.decode())
            db.session.add_all(SubEntry(**d) for d in data)
        except InvalidTag:
            print(f"Invalid key for {year}")

    print("Inserted sub entries ✓")

    to_load = (
        "aHR0cHM6Ly9naXN0LmdpdGh1YnVzZXJjb250ZW50LmNvbS9KZWZlVGhlUHVnLzQ2ZG"
        "VhZmI5MmU1OTUwNzc4ZTY0NWYzYmVjMWU1NzUxL3Jhdy9zb2x1dGlvbnMuanNvbg=="
    )
    results = process_json(to_load)
    rows = []
    for y in range(2025, latest_year + 1):
        for i, r in enumerate(results.get(y) or [], 1):
            s = Solution()
            s.year = str(y)
            s.val = i
            s.part1 = r.get("part1", "")
            s.part2 = r.get("part2", "")
            rows.append(s)
    db.session.add_all(rows)
    print("Inserted solutions ✓")

    to_load = (
        "aHR0cHM6Ly9naXN0LmdpdGh1YnVzZXJjb250ZW50LmNvbS9KZWZlVGhlUHVnLzg5"
        "MDAzYTg2NDEyYzIzNmM3MmU3ODlkYjJhODdhYTgxL3Jhdy9zcG9uc29ycy5qc29u"
    )
    url = base64.b64decode(to_load).decode()
    data = fetch(url).json()
    db.session.add_all(Sponsor(**row) for row in data.get("sponsors") or [])
    print("Inserted sponsors ✓")


def migrate_user_data(backup):
    progress_added = users_added = 0
    reference_to_id = {}

    existing_users = {u.user_id: u for u in User.query.all()}
    for row in backup["users"]:
        user_id = row["user_id"]
        user = existing_users.get(user_id)
        if not user:
            user = User()
            user.user_id = user_id
            user.name = row["name"]
            user.github = row["github"]
            db.session.add(user)
            db.session.flush()
            existing_users[user_id] = user
            users_added += 1

        reference_to_id[user_id] = user.id

    for row in backup["progress"]:
        user_id = row["reference"]
        if user_id not in reference_to_id:
            print(f"Skipping orphan progress for user_id={user_id}")
            continue
        progress = Progress()
        progress.user_id = reference_to_id[user_id]
        progress.year = row["year"]
        for i in range(1, 11):
            setattr(progress, f"c{i}", row[f"c{i}"])
        db.session.add(progress)
        progress_added += 1

    for row in backup["discord_ids"]:
        name = row.get("name", "")
        year = "0" if name in ("guild", "adventurer") else row["year"]
        db.session.query(DiscordID).filter_by(year=year, name=name).update(
            {"discord_id": row["discord_id"]}
        )

    existing_user_ids = {row[0] for row in db.session.query(Permission.user_id).all()}
    for row in backup["permissions"]:
        user_id = row["user_id"]
        if user_id not in existing_user_ids:
            p = Permission()
            p.user_id = user_id
            db.session.add(p)
            existing_user_ids.add(user_id)

    for row in backup["releases"]:
        db.session.query(Release).filter_by(year=row["year"]).update(
            {"release_number": row["release_number"]}
        )

    print(
        f"Migrated: {users_added} Users, {progress_added} rows of Progress,"
        "all Discord IDs, Admin Permissions and Release Numbers"
    )


if __name__ == "__main__":
    main()
    print(
        "Database setup complete.\nAfter logging in with your administrator account, "
        "go to the Admin dashboard (/admin) to customize this app for your server."
    )
