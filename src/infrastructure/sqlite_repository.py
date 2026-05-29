"""Infrastructure層: SQLite による PlayerRepository 実装

「詳細(detail)」はこの一番外側の層に閉じ込める。
PlayerRepository(ポート)を実装することで、内側のUseCaseにとって
差し替え可能な部品になる。sqlite3 依存はこのファイルに限定。
last_seen(放置時刻) も含めて永続化する点に注目。
"""
from __future__ import annotations

import sqlite3

from src.domain.player import Player
from src.usecase.repository import PlayerRepository


class SqlitePlayerRepository(PlayerRepository):
    def __init__(self, db_path: str = ":memory:") -> None:
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._create_table()

    def _create_table(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS players (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                name      TEXT NOT NULL UNIQUE,
                level     INTEGER NOT NULL,
                exp       INTEGER NOT NULL,
                gold      INTEGER NOT NULL,
                last_seen REAL NOT NULL
            )
            """
        )
        self._conn.commit()

    @staticmethod
    def _row_to_player(row: sqlite3.Row) -> Player:
        return Player(
            id=row["id"],
            name=row["name"],
            level=row["level"],
            exp=row["exp"],
            gold=row["gold"],
            last_seen=row["last_seen"],
        )

    def create(self, player: Player) -> Player:
        cur = self._conn.execute(
            "INSERT INTO players (name, level, exp, gold, last_seen) "
            "VALUES (?, ?, ?, ?, ?)",
            (player.name, player.level, player.exp, player.gold, player.last_seen),
        )
        self._conn.commit()
        player.id = cur.lastrowid
        return player

    def find_by_id(self, player_id: int) -> Player | None:
        row = self._conn.execute(
            "SELECT * FROM players WHERE id = ?", (player_id,)
        ).fetchone()
        return self._row_to_player(row) if row else None

    def list_all(self) -> list[Player]:
        rows = self._conn.execute("SELECT * FROM players ORDER BY id").fetchall()
        return [self._row_to_player(r) for r in rows]

    def update(self, player: Player) -> Player:
        self._conn.execute(
            "UPDATE players SET name = ?, level = ?, exp = ?, gold = ?, "
            "last_seen = ? WHERE id = ?",
            (player.name, player.level, player.exp, player.gold,
             player.last_seen, player.id),
        )
        self._conn.commit()
        return player

    def delete(self, player_id: int) -> None:
        self._conn.execute("DELETE FROM players WHERE id = ?", (player_id,))
        self._conn.commit()
