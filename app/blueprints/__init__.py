from .admin import admin_bp
from .auth import auth_bp
from .challenge import challenge_bp
from .errors import errors_bp
from .main import main_bp
from .routes import route_bp

__all__ = ["admin_bp", "auth_bp", "challenge_bp", "errors_bp", "main_bp", "route_bp"]
