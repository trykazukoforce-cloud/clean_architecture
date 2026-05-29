"""UseCase層: アプリケーション固有の例外。"""
from __future__ import annotations


class PlayerNotFoundError(Exception):
    """指定idのプレイヤーが存在しない。"""

    def __init__(self, player_id: int) -> None:
        super().__init__(f"Player(id={player_id}) は存在しません")
        self.player_id = player_id


class NameAlreadyExistsError(Exception):
    """同名プレイヤーが既に存在する (アプリケーション業務規則)。"""

    def __init__(self, name: str) -> None:
        super().__init__(f"名前 {name!r} は既に使われています")
        self.name = name
