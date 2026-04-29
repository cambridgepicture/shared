import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from werkzeug.security import check_password_hash, generate_password_hash


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _normalize_allowed_apps(allowed_apps: Optional[Iterable[str]]) -> list[str]:
    if not allowed_apps:
        return []
    return sorted({str(app).strip() for app in allowed_apps if str(app).strip()})


class UserStore:
    def __init__(self, db_path: str) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    is_admin INTEGER NOT NULL DEFAULT 0,
                    allowed_apps TEXT NOT NULL DEFAULT '[]',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()

    def _row_to_user(self, row: sqlite3.Row) -> Dict[str, Any]:
        try:
            allowed_apps = json.loads(row['allowed_apps'] or '[]')
        except json.JSONDecodeError:
            allowed_apps = []
        return {
            'user_id': row['user_id'],
            'email': row['email'],
            'is_admin': bool(row['is_admin']),
            'allowed_apps': _normalize_allowed_apps(allowed_apps),
            'created_at': row['created_at'],
            'updated_at': row['updated_at'],
        }

    def count_users(self) -> int:
        with self._connect() as conn:
            row = conn.execute('SELECT COUNT(*) AS count FROM users').fetchone()
        return int(row['count']) if row else 0

    def count_admins(self) -> int:
        with self._connect() as conn:
            row = conn.execute('SELECT COUNT(*) AS count FROM users WHERE is_admin = 1').fetchone()
        return int(row['count']) if row else 0

    def seed_admin(self, *, email: str, password: str, allowed_apps: Optional[Iterable[str]] = None) -> None:
        if not email or not password:
            return
        if self.get_user_by_email(email) is not None:
            return
        self.create_user(email=email, password=password, is_admin=True, allowed_apps=allowed_apps)

    def create_user(self, *, email: str, password: str, is_admin: bool = False, allowed_apps: Optional[Iterable[str]] = None) -> Dict[str, Any]:
        normalized_email = _normalize_email(email)
        if not normalized_email:
            raise ValueError('Email is required.')
        if not password:
            raise ValueError('Password is required.')

        with self._connect() as conn:
            cursor = conn.execute(
                'INSERT INTO users (email, password_hash, is_admin, allowed_apps) VALUES (?, ?, ?, ?)',
                (normalized_email, generate_password_hash(password), int(is_admin), json.dumps(_normalize_allowed_apps(allowed_apps))),
            )
            conn.commit()
            user_id = cursor.lastrowid
        return self.get_user_by_id(user_id)

    def update_user(self, user_id: int, *, email: Optional[str] = None, password: Optional[str] = None, is_admin: Optional[bool] = None, allowed_apps: Optional[Iterable[str]] = None) -> Dict[str, Any]:
        assignments: list[str] = []
        values: list[Any] = []
        if email is not None:
            normalized_email = _normalize_email(email)
            if not normalized_email:
                raise ValueError('Email is required.')
            assignments.append('email = ?')
            values.append(normalized_email)
        if password is not None:
            if not password:
                raise ValueError('Password cannot be empty.')
            assignments.append('password_hash = ?')
            values.append(generate_password_hash(password))
        if is_admin is not None:
            if not is_admin and self.count_admins() <= 1:
                with self._connect() as conn:
                    row = conn.execute('SELECT is_admin FROM users WHERE user_id = ?', (user_id,)).fetchone()
                if row and bool(row['is_admin']):
                    raise ValueError('At least one admin user is required.')
            assignments.append('is_admin = ?')
            values.append(int(is_admin))
        if allowed_apps is not None:
            assignments.append('allowed_apps = ?')
            values.append(json.dumps(_normalize_allowed_apps(allowed_apps)))
        if not assignments:
            user = self.get_user_by_id(user_id)
            if user is None:
                raise ValueError('User not found.')
            return user
        values.append(user_id)
        with self._connect() as conn:
            conn.execute(f"UPDATE users SET {', '.join(assignments)}, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?", values)
            conn.commit()
        return self.get_user_by_id(user_id)

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()
        return None if row is None else self._row_to_user(row)

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute('SELECT * FROM users WHERE email = ?', (_normalize_email(email),)).fetchone()
        return None if row is None else self._row_to_user(row)

    def list_users(self) -> list[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute('SELECT * FROM users ORDER BY is_admin DESC, email ASC').fetchall()
        return [self._row_to_user(row) for row in rows]

    def authenticate(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        user = self.get_user_by_email(email)
        if user is None:
            return None
        with self._connect() as conn:
            row = conn.execute('SELECT password_hash FROM users WHERE user_id = ?', (user['user_id'],)).fetchone()
        if row is None or not check_password_hash(row['password_hash'], password):
            return None
        return user
