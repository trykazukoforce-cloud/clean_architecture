"""Interface Adapter層: コントローラ

外側(CLI/Web等)からの入力を受け、UseCaseを呼び出し、
結果を外向けの形(ここでは dict / 文字列)へ変換する。
UseCase(インタラクタ)に依存するが、具体リポジトリは知らない。
"""
from __future__ import annotations

from src.domain.user import User
from src.usecase.user_interactor import UserInteractor


class UserController:
    def __init__(self, interactor: UserInteractor) -> None:
        self._interactor = interactor

    @staticmethod
    def _present(user: User) -> dict:
        """エンティティを外向けDTO(dict)へ変換 (プレゼンタ役)。"""
        return {"id": user.id, "name": user.name, "email": user.email}

    def create(self, name: str, email: str) -> dict:
        return self._present(self._interactor.register(name, email))

    def get(self, user_id: int) -> dict:
        return self._present(self._interactor.get(user_id))

    def list(self) -> list[dict]:
        return [self._present(u) for u in self._interactor.list_users()]

    def rename(self, user_id: int, new_name: str) -> dict:
        return self._present(self._interactor.change_name(user_id, new_name))

    def delete(self, user_id: int) -> None:
        self._interactor.remove(user_id)
