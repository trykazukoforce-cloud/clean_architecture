"""テスト: 同じUseCaseが両backendで同じ振る舞いをすることを確認。

クリーンアーキテクチャの利点: テスト時はインメモリ実装を注入でき、
UseCaseのテストにDBファイルやJSONファイルの実体が不要(差し替え可能)。
"""
from __future__ import annotations

import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.infrastructure.json_repository import JsonUserRepository  # noqa: E402
from src.infrastructure.sqlite_repository import SqliteUserRepository  # noqa: E402
from src.usecase.errors import EmailAlreadyExistsError, UserNotFoundError  # noqa: E402
from src.usecase.user_interactor import UserInteractor  # noqa: E402


def make_interactors():
    tmp = tempfile.mkdtemp()
    return [
        UserInteractor(SqliteUserRepository(":memory:")),
        UserInteractor(JsonUserRepository(os.path.join(tmp, "users.json"))),
    ]


@pytest.mark.parametrize("uc", make_interactors())
def test_crud(uc):
    # CREATE
    a = uc.register("Alice", "alice@example.com")
    assert a.id is not None
    # READ
    assert uc.get(a.id).name == "Alice"
    assert len(uc.list_users()) == 1
    # UPDATE
    uc.change_name(a.id, "Alice S.")
    assert uc.get(a.id).name == "Alice S."
    # DELETE
    uc.remove(a.id)
    assert uc.list_users() == []


@pytest.mark.parametrize("uc", make_interactors())
def test_duplicate_email(uc):
    uc.register("Alice", "dup@example.com")
    with pytest.raises(EmailAlreadyExistsError):
        uc.register("Other", "dup@example.com")


@pytest.mark.parametrize("uc", make_interactors())
def test_not_found(uc):
    with pytest.raises(UserNotFoundError):
        uc.get(999)


def test_domain_validation():
    uc = UserInteractor(SqliteUserRepository(":memory:"))
    with pytest.raises(ValueError):
        uc.register("", "x@example.com")   # name必須
    with pytest.raises(ValueError):
        uc.register("Bob", "invalid-email")  # email形式
