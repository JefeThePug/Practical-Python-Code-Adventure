import os

from itsdangerous import URLSafeTimedSerializer

from app.ui import ICON_REFERENCE

from .cache import DataCache
from .config import DevConfig, ProdConfig
from .extensions import db, generate_csrf_token, validate_csrf
from .types import AppFlask

SERIALIZER_SALT = "cookie"
CONFIG_MAP = {
    "development": DevConfig,
    "production": ProdConfig,
}


def create_app() -> AppFlask:
    env = os.getenv("FLASK_ENV", "development")

    try:
        config_type = CONFIG_MAP[env]
    except KeyError:
        raise RuntimeError(f"Unknown environment: {env}")

    app = AppFlask(__name__)
    app.config.from_object(config_type)
    assert app.secret_key, "SECRET_KEY must be set"
    app.serializer = URLSafeTimedSerializer(app.secret_key, salt=SERIALIZER_SALT)

    db.init_app(app)
    app.before_request(validate_csrf)
    app.jinja_env.globals["csrf_token"] = generate_csrf_token
    app.jinja_env.globals["ICONS"] = ICON_REFERENCE
    app.data_cache = DataCache()

    from .blueprints import (
        admin_bp,
        auth_bp,
        challenge_bp,
        errors_bp,
        main_bp,
        route_bp,
    )
    from .templating import register_globals

    with app.app_context():
        app.data_cache.load_all()
        register_globals()

    for bp in (
        main_bp,
        auth_bp,
        route_bp,
        challenge_bp,
        admin_bp,
        errors_bp,
    ):
        app.register_blueprint(bp)

    return app
