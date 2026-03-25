import base64
import hashlib
import json
import os
import sys
from pathlib import Path

import requests
import yaml
from dotenv import load_dotenv
from flask import Flask
from sqlalchemy import create_engine, event, text
from sqlalchemy.exc import SQLAlchemyError
from cryptography.hazmat.primitives.ciphers.aead import AESGCM as Encryption
from cryptography.exceptions import InvalidTag

load_dotenv(Path(__file__).resolve().parent / ".env")

from app.models import (  # noqa: E402
    DiscordID,
    MainEntry,
    Obfuscation,
    Permission,
    Release,
    Solution,
    Sponsor,
    SubEntry,
    db,
)

# Initialize Flask application
app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True

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
app.config["SQLALCHEMY_COMMIT_ON_TEARDOWN"] = False

CREATED_TABLES = []


@event.listens_for(db.metadata, "after_create")
def receive_after_create(target, connection, tables, **kwargs):
    for table in tables:
        CREATED_TABLES.append(table.name)
        print(f"Table created: {table.name}")


def main():
    admin_id = check_args()
    check_database_exists()
    db.init_app(app)
    create_missing_tables()
    fill_permanent_data(admin_id)


def check_args():
    if len(sys.argv) != 2:
        sys.exit(
            "\nPlease include your administrator Discord ID.\n"
            "Usage: python setup.py <admin_discord_user_id>"
        )
    if not os.getenv("YEAR"):
        sys.exit("YEAR env var required")

    return sys.argv[1].strip()


def check_database_exists():
    engine = create_engine(ADMIN_URL).execution_options(isolation_level="AUTOCOMMIT")

    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :dbname"),
            {"dbname": DATABASE_NAME},
        )
        if not result.fetchone():
            if not DATABASE_NAME:
                sys.exit("Database Name must be stored in .env")
            conn.execute(text(f"CREATE DATABASE {DATABASE_NAME}"))
            print(f"Database {DATABASE_NAME} created.")

    engine.dispose()


def create_missing_tables():
    CREATED_TABLES.clear()

    with app.app_context():
        db.create_all()

        if CREATED_TABLES:
            print(f"Success: {len(CREATED_TABLES)} new table(s) created.")
        else:
            print("No new tables needed; all schemas already exist.")


def fetch(url: str) -> requests.Response:
    res = requests.get(url, timeout=10)
    res.raise_for_status()
    return res


def fill_permanent_data(admin_id):
    def commit_block(label: str):
        try:
            db.session.commit()
            print(f"{label} ✓")
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"{label} ✗  ({e})")

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

    latest_year = int(os.getenv("YEAR") or "2025")

    with app.app_context():
        inspector = db.inspect(db.engine)
        table_names = inspector.get_table_names()

        if "releases" in table_names and not db.session.query(Release).first():
            releases = [
                Release(year=f"{year}", release_number=0)  # type: ignore
                for year in range(2025, latest_year + 1)
            ]
            db.session.add_all(releases)
            commit_block("Inserted releases")

        if "permissions" in table_names:
            if not db.session.query(Permission).first():
                db.session.add_all(
                    [
                        Permission(user_id="609283782897303554"),  # type: ignore
                        Permission(user_id=admin_id),  # type: ignore
                    ]
                )
                commit_block("Inserted permissions")
            else:
                if (
                    not db.session.query(Permission)
                    .filter_by(user_id=admin_id)
                    .one_or_none()
                ):
                    db.session.add(Permission(user_id=admin_id))  # type: ignore
                    commit_block("Added missing admin permission")

        if "discord_ids" in table_names and not db.session.query(DiscordID).first():
            discord_ids = [
                DiscordID(year="0", name="guild", discord_id=""),  # type: ignore
                DiscordID(year="0", name="role", discord_id=""),  # type: ignore
                DiscordID(year="0", name="adventurer", discord_id=""),  # type: ignore
                *[
                    DiscordID(
                        year=f"{y}",  # type: ignore
                        name=(f"{i}" if i > 0 else "champion"),  # type: ignore
                        discord_id="",  # type: ignore
                    )
                    for y in range(2025, latest_year + 1)
                    for i in range(11)
                ],
            ]
            db.session.add_all(discord_ids)
            commit_block("Inserted discord ids")

        if "obfuscation" in table_names and not db.session.query(Obfuscation).first():
            to_load = (
                "aHR0cHM6Ly9naXN0LmdpdGh1YnVzZXJjb250ZW50LmNvbS9KZWZlVGhlUHVnLzYzNG"
                "FhMjdkZDFmNGJkOTlhYWU4NDAzNjA1ZThhNWJiL3Jhdy9vYmZ1c2NhdGlvbi5qc29u"
            )
            results = process_json(to_load)
            rows = [
                Obfuscation(year=str(y), val=i, obfuscated_key=o, html_key=h)  # type: ignore
                for y in range(2025, latest_year + 1)
                for i, (o, h) in enumerate(results.get(y) or [], 1)
            ]
            db.session.add_all(rows)
            commit_block("Inserted obfuscation data")

        if "main_entries" in table_names and not db.session.query(MainEntry).first():
            to_load = (
                "aHR0cHM6Ly9naXN0LmdpdGh1YnVzZXJjb250ZW50LmNvbS9KZWZlVGhlUHVn"
                "L2M5NWFmY2IwOTFiY2JiODhmMDQ4NTRkMzZlYTMxOTRmL3Jhdy9lZS5qc29u"
            )
            results = process_json(to_load)
            rows = [
                MainEntry(year=str(y), val=i, ee=ee)  # type: ignore
                for y in range(2025, latest_year + 1)
                for i, ee in enumerate(results.get(y) or [], 1)
            ]
            db.session.add_all(rows)
            commit_block("Inserted main entries")

        if "sub_entries" in table_names and not db.session.query(SubEntry).first():
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

            commit_block("Inserted sub entries")

        if "solutions" in table_names and not db.session.query(Solution).first():
            to_load = (
                "aHR0cHM6Ly9naXN0LmdpdGh1YnVzZXJjb250ZW50LmNvbS9KZWZlVGhlUHVnLzQ2ZG"
                "VhZmI5MmU1OTUwNzc4ZTY0NWYzYmVjMWU1NzUxL3Jhdy9zb2x1dGlvbnMuanNvbg=="
            )
            results = process_json(to_load)
            rows = [
                Solution(
                    year=str(y),  # type: ignore
                    val=i,  # type: ignore
                    part1=s.get("part1", ""),  # type: ignore
                    part2=s.get("part2", ""),  # type: ignore
                )
                for y in range(2025, latest_year + 1)
                for i, s in enumerate(results.get(y) or [], 1)
            ]
            db.session.add_all(rows)
            commit_block("Inserted solutions")

        if "sponsors" in table_names and not db.session.query(Sponsor).first():
            to_load = (
                "aHR0cHM6Ly9naXN0LmdpdGh1YnVzZXJjb250ZW50LmNvbS9KZWZlVGhlUHVnLzg5"
                "MDAzYTg2NDEyYzIzNmM3MmU3ODlkYjJhODdhYTgxL3Jhdy9zcG9uc29ycy5qc29u"
            )
            url = base64.b64decode(to_load).decode()
            data = fetch(url).json()
            db.session.add_all(Sponsor(**row) for row in data.get("sponsors") or [])
            commit_block("Inserted sponsors")


if __name__ == "__main__":
    main()
    print(
        "Database setup complete.\nAfter logging in with your administrator account, "
        "go to the Admin dashboard (/admin) to customize this app for your server."
    )
