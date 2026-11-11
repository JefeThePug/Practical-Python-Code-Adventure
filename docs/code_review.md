# Flask App Code Review

Date: 2026-09-05
Scope: `app/` (Flask application), plus `css_bundler.py`, `Dockerfile`, `entrypoint.sh`, `pyproject.toml` as supporting context.
Method: manual read-through of every module in `app/` (blueprints, services, cache, models, auth, templating) and the deployment scripts. No files were modified.

---

## 1. Summary

The app is a modular, blueprint-based Flask site (auth, main, routes, challenge, admin, api, errors) backed by Postgres/SQLAlchemy, with an in-memory read cache (`DataCache`) populated at startup and updated alongside DB writes. The structure is clean and consistently typed (`TypedDict`s in `types.py`, `Mapped[...]` models). The most important issues are:

1. **The in-memory cache does not survive multi-worker deployment** — Gunicorn's `--workers 2` (default in `entrypoint.sh`) means writes made through the admin panel update the DB and only *one* worker's copy of `DataCache`; the other worker keeps serving stale data until restart.
2. **Outbound `requests` calls have no timeout**, anywhere. A slow/unresponsive Discord API will hang a Gunicorn worker indefinitely.
3. **`assert app.secret_key`** is the only guard against booting with an empty `SECRET_KEY`. Asserts are removed under `python -O` / `PYTHONOPTIMIZE=1`, silently disabling the check.
4. **Discord OAuth login has no `state` parameter**, leaving the flow open to CSRF-style login/account-linking attacks.
5. A **stray-cookie crash**: `get_progress()` tries to `serializer.loads()` *every* cookie longer than 40 characters, not just its own — any unrelated long cookie throws an uncaught `itsdangerous` exception and 500s the page for anonymous visitors.
6. A **latent `KeyError`**: `DataCache.update_progress` reads `session["user_data"]["name"]`, but Discord's user object (and the rest of the codebase) uses `"username"` — this key doesn't exist and will raise if that code path is ever hit.

Details, plus lower-severity findings and style notes, follow below.

---

## 2. High-impact issues

### 2.1 In-memory cache is per-process, not shared across Gunicorn workers
`app/cache.py` builds `DataCache` once in `create_app()` and stores it on `app.data_cache`. Every admin mutation (`update_releases`, `update_discord`, `update_perms`, `update_sponsors`, `update_html`, `update_solutions`, `update_progress`, `update_users`, `delete_users`) commits to the DB and then patches `self.<field>` in the *same process's* copy of the cache.

`entrypoint.sh` runs `gunicorn --workers "${GUNICORN_WORKERS:-2}"` — with the default sync worker class, each worker is a separate OS process with its own Python heap. A release-number update made by the worker that handled the admin POST will not be visible to requests routed to the other worker until that worker restarts (or the whole app restarts).

**Suggested fix:** either (a) drop the in-memory cache in favor of querying the DB (Postgres + these table sizes almost certainly don't need a cache), (b) move shared state to something actually shared (Redis, or a DB-backed "version" you re-check per-request), or (c) if the cache stays, pin Gunicorn to a single worker (fine for this traffic level) and document why, so nobody adds a second worker later expecting consistency.

### 2.2 No timeouts on outbound HTTP calls
None of the `requests.get/post/put` calls in `app/services/discord.py` or `app/blueprints/challenge.py` (`access()`) pass `timeout=`. If discord.com is slow or unreachable, the call blocks forever, tying up a Gunicorn worker (and with only 1–2 workers configured, this can take the whole site down for other users).

**Suggested fix:** add a module-level constant, e.g. `DISCORD_TIMEOUT = 10`, and pass `timeout=DISCORD_TIMEOUT` to every `requests.*` call in `services/discord.py` and `blueprints/challenge.py`.

### 2.3 `SECRET_KEY` presence is only checked via `assert`
`app/__init__.py:29`:
```python
assert app.secret_key, "SECRET_KEY must be set"
```
`python -O` (or `PYTHONOPTIMIZE=1` in the environment) strips all `assert` statements at compile time. If that ever gets set in the container (directly, or via a base image / `PYTHONOPTIMIZE` env leaking in), the app boots successfully with an empty secret key, and Flask sessions/CSRF tokens/`itsdangerous` cookies become signable by anyone. Given `config.py` already defaults `SECRET_KEY` to `""` when unset, this is the only thing standing between a misconfigured deploy and a fully broken session/CSRF scheme.

**Suggested fix:** replace with an explicit check that always runs:
```python
if not app.secret_key:
    raise RuntimeError("SECRET_KEY must be set")
```

### 2.4 Discord OAuth flow has no `state` parameter
`blueprints/auth.py` `login()` builds the Discord authorize URL without a `state` value, and `callback()` never validates one. Without `state`, the OAuth flow is vulnerable to session-fixation/login CSRF: an attacker can obtain their own valid `code`, trick a victim into visiting `/callback?code=<attacker's code>`, and the victim's session ends up authenticated as (i.e. logs progress against) the attacker's Discord account.

**Suggested fix:** generate a random `state`, store it in the session before redirecting, and verify `request.args.get("state")` matches in `callback()` before exchanging the code.

### 2.5 `get_progress()` can crash on unrelated cookies
`app/services/progress.py:66-68`:
```python
cookies = [*request.cookies.keys()]
s = [get_app().serializer.loads(x) for x in cookies if len(x) > 40]
```
This iterates *cookie names* (not the app's own progress cookies specifically) and tries to deserialize any name longer than 40 characters with the app's `itsdangerous` serializer. Any browser extension, analytics cookie, or previous session artifact whose *name* happens to exceed 40 characters will raise `itsdangerous.BadSignature`/`BadData`, which is not caught anywhere in this call chain — it will 500 the page for that anonymous visitor on every request (`get_progress()` is called from `main.index`, `routes.how_to`, `routes.champions`, `routes.gratitude`, `routes.sponsor`, `auth.pre_login`, `challenge.challenge`).

Two separate issues here:
- It should filter on cookie *names that this app itself set* (e.g. a recognizable prefix), not "any cookie name over 40 chars."
- Even after filtering, `serializer.loads()` should be wrapped in a `try/except itsdangerous.BadData` and skip the malformed value rather than propagate.

### 2.6 `session["user_data"]["name"]` — key that doesn't exist
`app/cache.py:502` (`DataCache.update_progress`):
```python
main = DataCache.add_user(user, session["user_data"]["name"])
```
Discord's `/users/@me` response has no `"name"` field (it's `"username"`), and nothing in `auth.py` adds a `"name"` key to `session["user_data"]`. Compare with `DataCache.load_progress` a few lines above, which correctly uses `session["user_data"]["username"]`.

This path only triggers when a logged-in user's `User` row is missing (e.g., an admin used `delete_users` on someone who is still logged in and then submits a correct answer) — an edge case, but currently guaranteed to raise `KeyError` rather than recreate the user, and that `KeyError` isn't caught by the surrounding `except (SQLAlchemyError, ValueError)`.

**Suggested fix:** change `session["user_data"]["name"]` to `session["user_data"]["username"]`.

---

## 3. Medium-impact issues

### 3.1 `SQLALCHEMY_DATABASE_URI` built by raw string interpolation
`app/config.py:14-17` interpolates `POSTGRES_USER`/`POSTGRES_PASSWORD`/etc. directly into the connection string. If a password contains characters like `@`, `:`, `/`, or `#`, the resulting URI is malformed or misparsed (e.g. an `@` in the password gets read as the user/host separator). Not currently exploitable by an attacker (values come from your own `.env`), but it's a footgun the moment someone generates a "strong" random password containing URL-reserved characters.

**Suggested fix:** use `sqlalchemy.engine.URL.create(...)` or `urllib.parse.quote_plus()` on the user/password components.

### 3.2 `FLASK_ENV` fails open to development
`app/__init__.py:20`: `env = os.getenv("FLASK_ENV", "development")`. If the env var is ever unset in a production-like environment (typo in compose file, missing from a new deploy target, etc.), the app silently boots with `DevConfig` — `DEBUG = True`, `SESSION_COOKIE_SECURE` unset — rather than failing loudly. Defaulting to the safer config (or raising if `FLASK_ENV` is unset) would make misconfiguration visible immediately instead of shipping a debug-enabled server.

### 3.3 Duplicated business rules (drift risk)
- `AdminConstantsCache.TYPE_MAP` (`cache.py:39-44`) maps sponsor `type` → tier bucket. `blueprints/admin.py` `sponsor()` (POST branch) redefines the identical mapping inline as `bucket = {...}`. If a new sponsor type is ever added, it's easy to update one and forget the other, and the two are already very slightly out of sync in spirit (constant vs. hand-rolled dict, same keys).
- The Discord ID `"609283782897303554"` (a bot/system account to exclude from leaderboards) is hardcoded twice: once as `AdminConstantsCache.RPI` and once as a literal string inside `DataCache._progress()` (`cache.py:417`). `_progress` should reference `AdminConstantsCache.RPI` instead of re-typing the literal.

**Suggested fix:** have `admin.py` import and reuse `AdminConstantsCache.TYPE_MAP`; have `_progress()` reference `AdminConstantsCache.RPI`.

### 3.4 Unhandled `KeyError`s on user-facing routes
Several public routes index into cache dicts without validating the key exists first, e.g.:
- `challenge_bp.challenge()`: `app.data_cache.admin.html_nums[year][obs_num]` — an invalid/old obfuscated URL raises `KeyError` → generic 500 instead of a 404/redirect.
- `challenge_bp.access()`: `app.data_cache.admin.obfuscations[year][...]`, `app.data_cache.admin.discord_ids[year][...]` — same pattern.

Because `DEBUG=False` in production this won't leak a traceback, but it does mean a bad/stale link produces an ugly generic error page instead of the site's own 404 (which is otherwise nicely styled as the 418 teapot in `errors.py`). Since `KeyError` isn't handled here, it also bypasses that custom error page entirely (Flask's default error handling only intercepts HTTP exceptions, not arbitrary `KeyError`s, unless you register a handler for `Exception`/`KeyError`).

**Suggested fix:** wrap the lookups (or use `.get()` + explicit `abort(404)`) so malformed/stale challenge links degrade gracefully.

### 3.5 `exchange_code()` doesn't handle non-JSON / error responses
`app/services/discord.py:25-31` posts to Discord's token endpoint and immediately calls `response.json()` without checking `response.status_code` or catching a JSON decode failure. If Discord returns an HTML error page (e.g., a 502 from Discord's edge, or a WAF block), `.json()` raises `requests.exceptions.JSONDecodeError`, which isn't caught by `auth.callback()`'s `except requests.exceptions.RequestException` (JSON decode errors are not `RequestException` subclasses in recent `requests` versions) — this would propagate as an unhandled 500.

**Suggested fix:** call `response.raise_for_status()` before `.json()`, and either let `RequestException` propagate (already handled one level up for `get_user_data`) or wrap the `.json()` call too.

### 3.6 `Progress` model: ten flat boolean-array columns
`c1`...`c10` in `models.py` (and mirrored in `types.py`'s `UserRow`, and accessed everywhere via `getattr(obj, f"c{i}")`/`setattr`) is a denormalized schema that trades relational cleanliness for convenience. It works, but:
- Every place touching progress needs string-formatted attribute access (`getattr`/`setattr` with `f"c{i}"`), which defeats static typing/IDE navigation and is easy to typo silently (a typo'd `f"c{i}"` just returns `None` via `getattr(..., None)` in `update_progress`, rather than erroring).
- Adding an 11th challenge in a future year means a schema migration touching every one of these tables/dicts, rather than adding a row.

This isn't wrong, and a full renormalization is a bigger change than a "review" should prescribe — flagging it as a design tradeoff worth revisiting if the challenge count ever changes, or if a future year needs more/fewer than 10.

### 3.7 Two identical-looking builder functions with empty docstrings
`app/services/discord.py`: `get_avatar_url` and `get_user_data` both have a bare `""" """` docstring — dead weight that adds nothing (contrast with `exchange_code` right above them, which has a real docstring). Either fill them in briefly or delete them; an empty docstring is worse than no docstring since it looks like a stub someone forgot to finish.

---

## 4. Low-impact / style notes

- **`app/blueprints/challenge.py` `challenge()` POST loop** (`for n, guess in enumerate(guesses): ... else: error = "Incorrect..."`): the `else` branch fires even when `guess` is `None` (i.e., that part's field wasn't submitted at all), not just on a genuine wrong answer. In practice both cases render the same "Incorrect. Please try again." message and a correct answer in the *other* slot still short-circuits and returns, so the user-visible behavior is mostly fine — but the code doesn't distinguish "you got it wrong" from "you didn't answer this part," which will be confusing if the two-part form is ever submitted independently per part.
- **Sentinel `"0"` year key**: `DiscordID`/`discord_ids` overload the "year" concept with a fake year `"0"` to store global settings (`guild`, `adventurer`). This works but isn't self-describing — a reader has to learn that `"0"` is special by reading `admin.py`'s `discord()` view rather than the schema. A short comment at the `DiscordID` model (or a dedicated settings table) would help.
- **Dual-direction dicts**: `AdminConstantsCache.obfuscations`/`html_nums` store both `{val: key}` and `{key: val}` in the same dict (`cache.py:85-86`) so a single mapping can be used for encode and decode. It works because keys are `int` vs `str` and won't collide, but this isn't obvious from the code and would benefit from a one-line comment explaining the bidirectional-lookup trick.
- **`services/progress.py` `set_progress()`** pattern-matches on `bytes | bytearray | memoryview | str` for the return of `itsdangerous.URLSafeTimedSerializer.dumps()`, which per its type stubs and actual implementation always returns `str`. This is defensive code for a case that can't occur; a plain `return dumped` would be simpler and equally correct.
- **Magic numbers for challenge count**: `range(1, 11)` / `range(11)` (10 challenges) appears repeated across `models.py`, `cache.py`, `admin.py`, and `types.py` rather than referencing a single `NUM_CHALLENGES = 10` constant.
- **No test suite**: there is no `tests/` directory, pytest config, or CI test step (only `.github/FUNDING.yml` under `.github/`). For a login flow, CSRF handling, cooldown logic, and admin data-mutation code like this, even a small set of unit tests around `services/cooldown.py`, `services/progress.py`, and the cache `update_*` methods would catch regressions like 2.6 above.
- **No linter/type-checker config committed**: a `.ruff_cache/` exists (so Ruff is being run locally) but there's no `[tool.ruff]` section in `pyproject.toml` or a `ruff.toml`, so lint rules aren't pinned/shared across contributors or enforced in CI.
- **`errors.py`**: every 404 is rewritten into an HTTP 418 with a custom image — a fun easter egg, but worth knowing that this also means uptime monitors, link checkers, and search-engine crawlers that specifically check for `404 Not Found` won't recognize truly missing pages as missing (418 is not a status any of that tooling treats as "gone"). Intentional here, just flagging the side effect.
- **`admin.py` `print_yaml()`**: `year = int(request.form["year"]) - 2025` has no bounds checking, but since `request.form["year"]` missing already raises a `werkzeug.exceptions.BadRequestKeyError` → Flask/Werkzeug turns that into a 400 automatically; a non-numeric value, however, raises a plain `ValueError` from `int()` that is *not* caught and would 500. Minor, since this is an admin-only, same-origin form field.

---

## 5. What's already solid

Worth calling out, since a review that's all criticism is misleading:

- **CSRF is implemented correctly and consistently**: `extensions.py`'s `validate_csrf` runs as a global `before_request` on every POST, uses `secrets.compare_digest`, and every POST form in `app/templates/**` (checked via grep) includes the hidden `csrf_token` field.
- **Session cookies are configured sensibly**: `HTTPOnly`, `SameSite=Lax`, and `Secure` in production.
- **Type hints and `TypedDict`s** (`app/types.py`) are used throughout to describe cache/service payload shapes, which is more rigorous than most Flask apps this size bother with.
- **Admin write paths consistently follow a DB-then-cache, rollback-on-error pattern** with `flash()` messages — the "no changes made" vs "updated successfully" distinction via dirty-checking is a nice touch for admin UX.
- **The cooldown service** (`services/cooldown.py`) is simple, self-contained, and easy to reason about — a good example of scoped, single-purpose code in this codebase.
