"""UseCase層: リポジトリ抽象 = 「ポート」

依存性逆転の原則(DIP)の中心。
UseCase は「データをどう保存するか」の詳細を知らず、
この抽象インターフェース(ポート)にだけ依存する。

実体(SQLite / JSON)は Infrastructure層がこの抽象を *実装* する。
矢印が外側(Infra)→内側(UseCase)へ向くため、依存ルールを破らない。
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.user import User


class UserRepository(ABC):
    """User永続化のポート(抽象)。CRUDを定義する。"""

    @abstractmethod
    def create(self, user: User) -> User:
        """Userを保存し、id採番済みのUserを返す。"""

    @abstractmethod
    def find_by_id(self, user_id: int) -> User | None:
        """idで1件取得。存在しなければ None。"""

    @abstractmethod
    def list_all(self) -> list[User]:
        """全件取得。"""

    @abstractmethod
    def update(self, user: User) -> User:
        """既存Userを更新して返す。"""

    @abstractmethod
    def delete(self, user_id: int) -> None:
        """idで削除。"""
