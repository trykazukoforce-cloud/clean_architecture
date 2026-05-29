"""Infrastructure層: ローカルJSONファイルによる PlayerRepository 実装

SQLite版と全く同じ PlayerRepository(ポート)を実装する。
内側(UseCase)から見れば SQLite版と区別がつかない = 完全に差し替え可能。
json 依存はこのファイルに限定。
"""
from __future__ import annotations

import json
import os

from src.domain.player import Player
from src.usecase.repository import PlayerRepository


class JsonPlayerRepository(PlayerRepository):
    def __init__(self, file_path: str = "players.json") -> None:
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
    def _to_player(r: dict) -> Player:
        return Player(
            id=r["id"], name=r["name"], level=r["level"],
            exp=r["exp"], gold=r["gold"], last_seen=r["last_seen"],
        )

    @staticmethod
    def _to_record(p: Player) -> dict:
        return {
            "id": p.id, "name": p.name, "level": p.level,
            "exp": p.exp, "gold": p.gold, "last_seen": p.last_seen,
        }

    # ---- PlayerRepository 実装 ---------------------------------------
    def create(self, player: Player) -> Player:
        records = self._load()
        player.id = self._next_id(records)
        records.append(self._to_record(player))
        self._save(records)
        return player

    def find_by_id(self, player_id: int) -> Player | None:
        for r in self._load():
            if r["id"] == player_id:
                return self._to_player(r)
        return None

    def list_all(self) -> list[Player]:
        return [self._to_player(r) for r in sorted(self._load(), key=lambda r: r["id"])]

    def update(self, player: Player) -> Player:
        records = self._load()
        for i, r in enumerate(records):
            if r["id"] == player.id:
                records[i] = self._to_record(player)
                break
        self._save(records)
        return player

    def delete(self, player_id: int) -> None:
        records = [r for r in self._load() if r["id"] != player_id]
        self._save(records)
