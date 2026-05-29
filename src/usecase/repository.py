"""UseCase層: リポジトリ抽象 = 「ポート」

依存性逆転の原則(DIP)の中心。
UseCase は「セーブデータをどこに保存するか」を知らず、この抽象だけに依存する。
実体(SQLite / JSON)は Infrastructure層がこの抽象を *実装* する。
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.player import Player


class PlayerRepository(ABC):
    """Playerセーブデータ永続化のポート(抽象)。CRUDを定義する。"""

    @abstractmethod
    def create(self, player: Player) -> Player:
        """新規セーブデータを保存し、id採番済みのPlayerを返す。"""

    @abstractmethod
    def find_by_id(self, player_id: int) -> Player | None:
        """idで1件取得。存在しなければ None。"""

    @abstractmethod
    def list_all(self) -> list[Player]:
        """全セーブデータ取得。"""

    @abstractmethod
    def update(self, player: Player) -> Player:
        """既存セーブデータを更新して返す。"""

    @abstractmethod
    def delete(self, player_id: int) -> None:
        """idで削除 (引退)。"""
