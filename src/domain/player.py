"""Domain層: Playerエンティティ (放置型RPGの「セーブデータ」)

Player はユーザーのセーブデータそのもの。
ゲームの中核ルール(レベルアップ曲線・経験値加算)はこの最も内側の層が持つ。
フレームワーク/DB/時計など外側の都合は一切知らない (標準ライブラリのみ)。
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Player:
    """放置RPGのプレイヤー（=ユーザーのセーブデータ）。

    last_seen: 最後にプレイした時刻 (epoch秒)。
               放置報酬の計算に使う。永続化されてこそ意味を持つ。
    """

    name: str
    level: int = 1
    exp: int = 0
    gold: int = 0
    last_seen: float = 0.0
    id: int | None = None

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        """ドメイン不変条件 (常に成り立つべき状態) を保証する。"""
        if not self.name or not self.name.strip():
            raise ValueError("name は必須です")
        if self.level < 1:
            raise ValueError("level は 1 以上です")
        if self.exp < 0 or self.gold < 0:
            raise ValueError("exp / gold は非負です")

    # ---- ゲームルール (エンタープライズ規則) --------------------------
    @staticmethod
    def exp_to_next(level: int) -> int:
        """次のレベルに必要な経験値 (レベル曲線)。"""
        return level * 100

    @property
    def power(self) -> int:
        """戦闘力 (レベル依存の派生値)。"""
        return self.level * 10

    def gain(self, exp: int, gold: int) -> int:
        """経験値・ゴールドを加算し、必要なだけレベルアップする。

        返り値: 上昇したレベル数。
        レベルアップ判定はドメインの責務 (どこに保存するかとは無関係)。
        """
        if exp < 0 or gold < 0:
            raise ValueError("報酬は非負である必要があります")
        self.exp += exp
        self.gold += gold
        levelups = 0
        while self.exp >= self.exp_to_next(self.level):
            self.exp -= self.exp_to_next(self.level)
            self.level += 1
            levelups += 1
        return levelups
