"""テスト: 同じUseCaseが両backendで同じ振る舞いをすることを確認。

放置時間の計算は注入した擬似時計(fake clock)で固定する。
→ 実時間を待たずにテストでき、これが「時計もDIする」利点。
"""
from __future__ import annotations

import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.domain.player import Player  # noqa: E402
from src.infrastructure.json_repository import JsonPlayerRepository  # noqa: E402
from src.infrastructure.sqlite_repository import SqlitePlayerRepository  # noqa: E402
from src.usecase.errors import NameAlreadyExistsError, PlayerNotFoundError  # noqa: E402
from src.usecase.player_interactor import PlayerInteractor  # noqa: E402


class FakeClock:
    """擬似時計。tick() で時間を進められる。"""

    def __init__(self, start: float = 1000.0) -> None:
        self.t = start

    def __call__(self) -> float:
        return self.t

    def tick(self, seconds: float) -> None:
        self.t += seconds


def make_interactors(clock):
    tmp = tempfile.mkdtemp()
    return [
        PlayerInteractor(SqlitePlayerRepository(":memory:"), now=clock,
                         idle_exp_per_sec=5.0, idle_gold_per_sec=2.0),
        PlayerInteractor(JsonPlayerRepository(os.path.join(tmp, "players.json")),
                         now=clock, idle_exp_per_sec=5.0, idle_gold_per_sec=2.0),
    ]


@pytest.fixture(params=["sqlite", "json"])
def uc(request):
    clock = FakeClock()
    sqlite_uc, json_uc = make_interactors(clock)
    uc = sqlite_uc if request.param == "sqlite" else json_uc
    uc._clock = clock  # テストから時計を操作できるよう保持
    return uc


def test_create_and_read(uc):
    p = uc.create_player("Alice")          # Create
    assert p.id is not None and p.level == 1
    assert uc.get(p.id).name == "Alice"    # Read


def test_idle_reward_levels_up(uc):
    p = uc.create_player("Idler")
    uc._clock.tick(100)                    # 100秒放置
    p2, reward = uc.login(p.id)            # Update (放置精算)
    assert reward.gained_exp == 500        # 100s * 5exp/s
    assert reward.gained_gold == 200       # 100s * 2gold/s
    # exp_to_next(1)=100,(2)=200,(3)=300 → 500=100+200で Lv1→Lv3 (残exp200)
    assert p2.level == 3
    assert p2.exp == 200
    assert reward.levelups == 2


def test_idle_persists_across_reload(uc):
    """放置時刻が永続化され、再取得しても整合することを確認。"""
    p = uc.create_player("Saver")
    uc._clock.tick(50)
    uc.login(p.id)
    reloaded = uc.get(p.id)
    assert reloaded.last_seen == uc._clock.t   # 保存された last_seen


def test_adventure(uc):
    p = uc.create_player("Hero")
    _, res = uc.adventure(p.id)            # Update (冒険)
    assert res.gained_exp == 70            # 60 + level(1)*10
    assert res.gained_gold == 25           # 20 + level(1)*5


def test_ranking_order(uc):
    a = uc.create_player("A")
    b = uc.create_player("B")
    uc._clock.tick(200)
    uc.login(b.id)                         # B を強化
    ranking = uc.ranking()                 # Read
    assert ranking[0].id == b.id           # 強い順


def test_retire(uc):
    p = uc.create_player("Bye")
    uc.retire(p.id)                        # Delete
    assert uc.ranking() == []
    with pytest.raises(PlayerNotFoundError):
        uc.get(p.id)


def test_duplicate_name(uc):
    uc.create_player("Dup")
    with pytest.raises(NameAlreadyExistsError):
        uc.create_player("Dup")


def test_domain_validation(uc):
    with pytest.raises(ValueError):
        uc.create_player("")               # name必須 (ドメイン検証)


def test_levelup_logic_unit():
    """ドメイン単体: gain のレベルアップ計算。"""
    p = Player(name="x")
    levelups = p.gain(exp=350, gold=0)     # 100+200=300で Lv1→Lv3, 残50
    assert p.level == 3 and p.exp == 50 and levelups == 2
