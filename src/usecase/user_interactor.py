"""UseCase層: インタラクタ (アプリケーション業務規則)

「ユースケースの手順」をここに書く。
- 入力の検証、業務ルール(email重複禁止など)の適用
- ポート(UserRepository)経由での永続化

コンストラクタで UserRepository を受け取る = コンストラクタ・インジェクション。
ここで具体実装(SQLite/JSON)を new しないのが最大のポイント。
"""
from __future__ import annotations

from src.domain.user import User
from src.usecase.errors import EmailAlreadyExistsError, UserNotFoundError
from src.usecase.repository import UserRepository


class UserInteractor:
    def __init__(self, repository: UserRepository) -> None:
        # 抽象に依存する。中身が DB か JSON かは知らない。
        self._repo = repository

    def register(self, name: str, email: str) -> User:
        """新規User登録。email重複は業務エラーとして弾く。"""
        for existing in self._repo.list_all():
            if existing.email == email:
                raise EmailAlreadyExistsError(email)
        # Userエンティティ生成時にドメイン検証(name必須/email形式)が走る
        user = User(name=name, email=email)
        return self._repo.create(user)

    def get(self, user_id: int) -> User:
        user = self._repo.find_by_id(user_id)
        if user is None:
            raise UserNotFoundError(user_id)
        return user

    def list_users(self) -> list[User]:
        return self._repo.list_all()

    def change_name(self, user_id: int, new_name: str) -> User:
        user = self.get(user_id)
        user.name = new_name
        user.validate()
        return self._repo.update(user)

    def remove(self, user_id: int) -> None:
        # 存在確認してから削除 (存在しなければ UserNotFoundError)
        self.get(user_id)
        self._repo.delete(user_id)
