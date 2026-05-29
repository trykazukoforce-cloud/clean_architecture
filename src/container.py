"""DIコンテナ (合成ルートの部品)

ここが「どの実装を使うか」を決める唯一の場所。
backend を切り替えるだけで、UseCase/Controller のコードは一切変えずに
SQLite ⇔ JSON を入れ替えられる = Dependency Injection の効果。
"""
from __future__ import annotations

from src.adapter.controller import UserController
from src.infrastructure.json_repository import JsonUserRepository
from src.infrastructure.sqlite_repository import SqliteUserRepository
from src.usecase.repository import UserRepository
from src.usecase.user_interactor import UserInteractor


def build_repository(backend: str) -> UserRepository:
    """文字列指定でリポジトリ実装を生成 (ファクトリ)。"""
    if backend == "sqlite":
        return SqliteUserRepository(db_path="users.db")
    if backend == "json":
        return JsonUserRepository(file_path="users.json")
    raise ValueError(f"未知のbackend: {backend!r} (sqlite / json のいずれか)")


def build_controller(backend: str) -> UserController:
    """依存関係を内側から外側へ順に組み立てて注入する。"""
    repository: UserRepository = build_repository(backend)  # 詳細
    interactor = UserInteractor(repository)                 # 注入
    controller = UserController(interactor)                 # 注入
    return controller
