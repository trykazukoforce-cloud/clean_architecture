"""Infrastructure層: ローカルJSONファイルによる UserRepository 実装

SQLite版と全く同じ UserRepository(ポート)を実装する。
内側(UseCase)から見れば SQLite版と区別がつかない = 完全に差し替え可能。
json への依存はこのファイルに限定される。

このコミットでは UseCase / Domain / 既存 SQLite実装 を 1行も変更していない。
新しい実装クラスを増やすだけで「保存先の選択肢」を増やせる ―― これがDIP の効果。
"""
from __future__ import annotations

import json
import os

from src.domain.user import User
from src.usecase.repository import UserRepository


class JsonUserRepository(UserRepository):
    def __init__(self, file_path: str = "users.json") -> None:
        self._path = file_path
        if not os.path.exists(self._path):
            self._save([])

    # ---- 永続化ヘルパ -------------------------------------------------
    def _load(self) -> list[dict]:
        with open(self._path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self, records: list[dict]) -> None:
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)

    def _next_id(self, records: list[dict]) -> int:
        return max((r["id"] for r in records), default=0) + 1

    @staticmethod
    def _to_user(record: dict) -> User:
        return User(id=record["id"], name=record["name"], email=record["email"])

    # ---- UserRepository 実装 -----------------------------------------
    def create(self, user: User) -> User:
        records = self._load()
        user.id = self._next_id(records)
        records.append({"id": user.id, "name": user.name, "email": user.email})
        self._save(records)
        return user

    def find_by_id(self, user_id: int) -> User | None:
        for r in self._load():
            if r["id"] == user_id:
                return self._to_user(r)
        return None

    def list_all(self) -> list[User]:
        return [self._to_user(r) for r in sorted(self._load(), key=lambda r: r["id"])]

    def update(self, user: User) -> User:
        records = self._load()
        for r in records:
            if r["id"] == user.id:
                r["name"] = user.name
                r["email"] = user.email
                break
        self._save(records)
        return user

    def delete(self, user_id: int) -> None:
        records = [r for r in self._load() if r["id"] != user_id]
        self._save(records)
