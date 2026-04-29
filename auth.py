from __future__ import annotations

import os
from functools import lru_cache, wraps
from types import SimpleNamespace
from urllib.parse import quote

from flask import abort, g, redirect, request, session

from .user_store import UserStore

DEFAULT_USER_DB_PATH = "/var/www/apps/portal/data/.user_store.sqlite3"
LOGIN_PATH = "/login"


def _public_request_target() -> str:
    prefix = (request.script_root or "").rstrip("/")
    path = request.path or "/"
    target = f"{prefix}{path}" if prefix else path
    if request.query_string:
        target = f"{target}?{request.query_string.decode('utf-8', errors='ignore')}"
    return target


def _normalize_user(user: dict[str, object] | None):
    if user is None:
        return None
    display_name = str(user.get("display_name") or user.get("email") or "")
    allowed_apps = tuple(str(app) for app in user.get("allowed_apps", []) or [])
    return SimpleNamespace(
        user_id=int(user["user_id"]),
        id=int(user["user_id"]),
        email=str(user.get("email") or ""),
        display_name=display_name,
        is_admin=bool(user.get("is_admin")),
        allowed_apps=allowed_apps,
    )


@lru_cache(maxsize=1)
def get_user_store() -> UserStore:
    user_db_path = os.getenv("USER_DB_PATH", DEFAULT_USER_DB_PATH)
    return UserStore(user_db_path)


def current_user():
    user = g.get("current_user")
    if user is not None:
        return user

    user_id = session.get("user_id")
    if user_id is None:
        g.current_user = None
        return None

    user = get_user_store().get_user_by_id(user_id)
    if user is None:
        session.clear()
        g.current_user = None
        return None

    normalized = _normalize_user(user)
    g.current_user = normalized
    return normalized


def login_url(next_url: str | None = None) -> str:
    target = next_url or _public_request_target() or "/"
    if not target.startswith("/"):
        target = "/"
    return f"{LOGIN_PATH}?next={quote(target, safe='')}"


def redirect_to_login(next_url: str | None = None):
    return redirect(login_url(next_url))


def require_login(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if current_user() is None:
            return redirect_to_login(_public_request_target())
        return view(*args, **kwargs)

    return wrapped


def require_admin(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user()
        if user is None:
            return redirect_to_login(_public_request_target())
        if not user.is_admin:
            abort(403)
        return view(*args, **kwargs)

    return wrapped


def require_app_access(app_slug: str):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            user = current_user()
            if user is None:
                return redirect_to_login(_public_request_target())
            if not user.is_admin and app_slug not in set(user.allowed_apps):
                abort(403)
            return view(*args, **kwargs)

        return wrapped

    return decorator


def visible_apps_for_user(user, app_catalog: dict[str, dict[str, object]]) -> list[dict[str, object]]:
    if user is None:
        return []
    if user.is_admin:
        return list(app_catalog.values())
    allowed = set(user.allowed_apps)
    return [app for slug, app in app_catalog.items() if slug in allowed]
