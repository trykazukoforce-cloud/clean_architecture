"""テスト: HTTP Adapter (FastAPI) の振る舞い。

同じUseCaseを使うので、CLI版と同じ挙動が HTTP 経由でも得られる。
- backend を SQLite / JSON に切り替えても、APIの応答は同一
- 時計を擬似化することで、放置時間も実時間を待たずにテスト可能
"""
from __future__ import annotations

import os
import sys
import tempfile

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.adapter.http_controller import create_app  # noqa: E402
from src.infrastructure.json_repository import JsonPlayerRepository  # noqa: E402
from src.infrastructure.sqlite_repository import SqlitePlayerRepository  # noqa: E402
from src.usecase.player_interactor import PlayerInteractor  # noqa: E402


class FakeClock:
    def __init__(self, start: float = 1000.0) -> None:
        self.t = start

    def __call__(self) -> float:
        return self.t

    def tick(self, seconds: float) -> None:
        self.t += seconds


def _make(backend: str):
    clock = FakeClock()
    if backend == "sqlite":
        repo = SqlitePlayerRepository(":memory:")
    else:
        tmp = tempfile.mkdtemp()
        repo = JsonPlayerRepository(os.path.join(tmp, "players.json"))
    interactor = PlayerInteractor(
        repo, now=clock, idle_exp_per_sec=5.0, idle_gold_per_sec=2.0
    )
    app = create_app(interactor)
    return TestClient(app), clock


@pytest.fixture(params=["sqlite", "json"])
def client_and_clock(request):
    return _make(request.param)


def test_full_crud_via_http(client_and_clock):
    client, clock = client_and_clock

    # Create
    r = client.post("/players", json={"name": "Alice"})
    assert r.status_code == 201
    pid = r.json()["id"]
    assert r.json()["level"] == 1

    # Read (single)
    r = client.get(f"/players/{pid}")
    assert r.status_code == 200
    assert r.json()["name"] == "Alice"

    # Read (list/ranking)
    r = client.get("/players")
    assert r.status_code == 200
    assert len(r.json()) == 1

    # Update: adventure
    r = client.post(f"/players/{pid}/adventure")
    assert r.status_code == 200
    assert r.json()["result"]["gained_exp"] == 70

    # Update: idle (login) — 100秒経過させる
    clock.tick(100)
    r = client.post(f"/players/{pid}/login")
    assert r.status_code == 200
    body = r.json()
    assert body["reward"]["gained_exp"] == 500
    assert body["reward"]["gained_gold"] == 200

    # Update: rename
    r = client.patch(f"/players/{pid}", json={"name": "Alice2"})
    assert r.status_code == 200
    assert r.json()["name"] == "Alice2"

    # Delete
    r = client.delete(f"/players/{pid}")
    assert r.status_code == 204
    r = client.get(f"/players/{pid}")
    assert r.status_code == 404


def test_error_mapping(client_and_clock):
    client, _ = client_and_clock

    # 404
    assert client.get("/players/999").status_code == 404

    # 409: 同名重複
    client.post("/players", json={"name": "Dup"})
    r = client.post("/players", json={"name": "Dup"})
    assert r.status_code == 409

    # 400: ドメイン検証エラー (空名)
    r = client.post("/players", json={"name": ""})
    assert r.status_code == 400
