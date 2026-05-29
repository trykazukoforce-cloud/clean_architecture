"""UseCase層: アプリケーション固有の例外。"""
from __future__ import annotations


class UserNotFoundError(Exception):
    """指定idのUserが存在しない。"""

    def __init__(self, user_id: int) -> None:
        super().__init__(f"User(id={user_id}) は存在しません")
        self.user_id = user_id


class EmailAlreadyExistsError(Exception):
    """同一emailのUserが既に存在する (アプリケーション業務規則)。"""

    def __init__(self, email: str) -> None:
        super().__init__(f"email={email!r} は既に登録済みです")
        self.email = email
