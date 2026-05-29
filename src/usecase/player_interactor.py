"""UseCase層: インタラクタ (放置RPGのアプリケーション業務規則)

CRUD をゲーム操作に対応させる:
  - create_player : Create (キャラ作成)
  - get / ranking : Read   (ステータス・ランキング閲覧)
  - login / adventure : Update (放置報酬・冒険で経験値とLvを更新)
  - retire        : Delete (引退)

依存はすべてコンストラクタ・インジェクション:
  - repository : 永続化ポート (SQLite / JSON)
  - now        : 時計 (放置時間の計算用) も注入 → テストで時間を固定できる
ここで具体実装(SQLite/JSON/本物の時計)を new しないのが要点。
"""
from __future__ import annotations

import time
from dataclasses import dataclass

from src.domain.player import Player
from src.usecase.errors import NameAlreadyExistsError, PlayerNotFoundError
from src.usecase.repository import PlayerRepository


@dataclass
class IdleReward:
    """放置報酬の結果 (UseCase→外側への出力データ)。"""

    elapsed_seconds: float
    gained_exp: int
    gained_gold: int
    levelups: int


@dataclass
class AdventureResult:
    gained_exp: int
    gained_gold: int
    levelups: int


class PlayerInteractor:
    def __init__(
        self,
        repository: PlayerRepository,
        now=time.time,
        idle_exp_per_sec: float = 5.0,
        idle_gold_per_sec: float = 2.0,
        idle_cap_seconds: float = 60 * 60 * 8,  # 放置報酬は最大8時間ぶん
    ) -> None:
        self._repo = repository      # 抽象に依存 (DB か JSON かは知らない)
        self._now = now              # 時計も抽象的に注入
        self._idle_exp = idle_exp_per_sec
        self._idle_gold = idle_gold_per_sec
        self._idle_cap = idle_cap_seconds

    # ---- Create -----------------------------------------------------
    def create_player(self, name: str) -> Player:
        for p in self._repo.list_all():
            if p.name == name:
                raise NameAlreadyExistsError(name)
        player = Player(name=name, last_seen=self._now())
        return self._repo.create(player)

    # ---- Read -------------------------------------------------------
    def get(self, player_id: int) -> Player:
        player = self._repo.find_by_id(player_id)
        if player is None:
            raise PlayerNotFoundError(player_id)
        return player

    def ranking(self) -> list[Player]:
        """強い順 (レベル→経験値) に並べたランキング。"""
        return sorted(
            self._repo.list_all(),
            key=lambda p: (p.level, p.exp),
            reverse=True,
        )

    # ---- Update -----------------------------------------------------
    def login(self, player_id: int) -> tuple[Player, IdleReward]:
        """ログイン時の放置報酬を精算する。

        last_seen からの経過秒に応じて経験値・ゴールドを付与し、
        last_seen を現在時刻に更新して保存する。
        """
        player = self.get(player_id)
        now = self._now()
        elapsed = max(0.0, now - player.last_seen)
        capped = min(elapsed, self._idle_cap)
        exp = int(capped * self._idle_exp)
        gold = int(capped * self._idle_gold)
        levelups = player.gain(exp, gold)
        player.last_seen = now
        self._repo.update(player)
        return player, IdleReward(elapsed, exp, gold, levelups)

    def adventure(self, player_id: int) -> tuple[Player, AdventureResult]:
        """能動的な冒険で即時報酬を得る。"""
        player = self.get(player_id)
        exp = 60 + player.level * 10
        gold = 20 + player.level * 5
        levelups = player.gain(exp, gold)
        player.last_seen = self._now()
        self._repo.update(player)
        return player, AdventureResult(exp, gold, levelups)

    def rename(self, player_id: int, new_name: str) -> Player:
        player = self.get(player_id)
        player.name = new_name
        player.validate()
        return self._repo.update(player)

    # ---- Delete -----------------------------------------------------
    def retire(self, player_id: int) -> None:
        self.get(player_id)  # 存在確認 (なければ PlayerNotFoundError)
        self._repo.delete(player_id)
