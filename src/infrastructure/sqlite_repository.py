"""Infrastructure層: SQLite による UserRepository 実装

「詳細(detail)」はこの一番外側の層に閉じ込める。
UserRepository(ポート)を実装することで、内側のUseCaseに対して
「差し替え可能な部品」になる。sqlite3 への依存はこのファイルに限定される。
"""
from __future__ import annotations

import sqlite3

from src.domain.user import User
from src.usecase.repository import UserRepository


class SqliteUserRepository(UserRepository):
    def __init__(self, db_path: str = ":memory:") -> None:
        # check_same_thread=False はデモ簡略化のため
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._create_table()

    def _create_table(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id    INTEGER PRIMARY KEY AUTOINCREMENT,
                name  TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE
            )
            """
        )
        self._conn.commit()

    @staticmethod
    def _row_to_user(row: sqlite3.Row) -> User:
        return User(id=row["id"], name=row["name"], email=row["email"])

    def create(self, user: User) -> User:
        cur = self._conn.execute(
            "INSERT INTO users (name, email) VALUES (?, ?)",
            (user.name, user.email),
        )
        self._conn.commit()
        user.id = cur.lastrowid
        return user

    def find_by_id(self, user_id: int) -> User | None:
        row = self._conn.execute(
            "SELECT id, name, email FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        return self._row_to_user(row) if row else None

    def list_all(self) -> list[User]:
        rows = self._conn.execute(
            "SELECT id, name, email FROM users ORDER BY id"
        ).fetchall()
        return [self._row_to_user(r) for r in rows]

    def update(self, user: User) -> User:
        self._conn.execute(
            "UPDATE users SET name = ?, email = ? WHERE id = ?",
            (user.name, user.email, user.id),
        )
        self._conn.commit()
        return user

    def delete(self, user_id: int) -> None:
        self._conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        self._conn.commit()
