from functools import wraps

from flask import abort, session

from app.appctx import get_app


def admin_only(func):
    """Restrict route access to users present in the admin permission cache."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        user = session.get("user_data")
        if not user:
            abort(401)
        if user["id"] not in get_app().data_cache.admin.get_permissions(login=True):
            abort(403)
        return func(*args, **kwargs)

    return wrapper
