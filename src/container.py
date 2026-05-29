"""DIコンテナ (合成ルートの部品)

「どの実装を使うか」を決める唯一の場所。
backend を切り替えるだけで、UseCase/Controller のコードは一切変えずに
SQLite ⇔ JSON を入れ替えられる = Dependency Injection の効果。
"""
from __future__ import annotations

import time

from src.adapter.controller import PlayerController
from src.infrastructure.json_repository import JsonPlayerRepository
from src.infrastructure.sqlite_repository import SqlitePlayerRepository
from src.usecase.player_interactor import PlayerInteractor
from src.usecase.repository import PlayerRepository


def build_repository(backend: str) -> PlayerRepository:
    """文字列指定でリポジトリ実装を生成 (ファクトリ)。"""
    if backend == "sqlite":
        return SqlitePlayerRepository(db_path="players.db")
    if backend == "json":
        return JsonPlayerRepository(file_path="players.json")
    raise ValueError(f"未知のbackend: {backend!r} (sqlite / json のいずれか)")


def build_interactor(backend: str, now=time.time) -> PlayerInteractor:
    """リポジトリ実装を選んでインタラクタを組み立てる。

    now を差し替えれば放置時間を擬似的に進められる (テスト/デモで活用)。
    """
    repository: PlayerRepository = build_repository(backend)
    return PlayerInteractor(repository, now=now)


def build_controller(backend: str, now=time.time) -> PlayerController:
    """CLI用Adapter(コントローラ)を組み立てて返す。"""
    return PlayerController(build_interactor(backend, now=now))


def build_app(backend: str, now=time.time):
    """HTTP用Adapter(FastAPIアプリ)を組み立てて返す。

    CLIと全く同じ UseCase(PlayerInteractor) を、別のAdapterに注入するだけ。
    内側(UseCase/Domain)のコードは1行も変えていない。
    """
    # ここで初めて FastAPI を import (外側の詳細を Infrastructure側に閉じ込める)
    from src.adapter.http_controller import create_app
    return create_app(build_interactor(backend, now=now))
