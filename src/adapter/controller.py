"""Interface Adapter層: コントローラ + プレゼンタ

外側(CLI)からの入力を受けて UseCase を呼び、結果を表示用テキストに変換する。
UseCase(インタラクタ)に依存するが、具体リポジトリ/時計は知らない。
"""
from __future__ import annotations

from src.domain.player import Player
from src.usecase.player_interactor import PlayerInteractor


class PlayerController:
    def __init__(self, interactor: PlayerInteractor) -> None:
        self._interactor = interactor

    # ---- プレゼンタ (エンティティ→表示文字列) ------------------------
    @staticmethod
    def _status_line(p: Player) -> str:
        need = Player.exp_to_next(p.level)
        return (
            f"[id={p.id}] {p.name}  "
            f"Lv.{p.level}  EXP {p.exp}/{need}  "
            f"Gold {p.gold}  戦闘力 {p.power}"
        )

    # ---- Create -----------------------------------------------------
    def create(self, name: str) -> str:
        p = self._interactor.create_player(name)
        return f"キャラ作成: {self._status_line(p)}"

    # ---- Read -------------------------------------------------------
    def status(self, player_id: int) -> str:
        return self._status_line(self._interactor.get(player_id))

    def ranking(self) -> str:
        players = self._interactor.ranking()
        if not players:
            return "（プレイヤーがいません）"
        lines = ["=== ランキング ==="]
        for rank, p in enumerate(players, 1):
            lines.append(f"{rank}位  {self._status_line(p)}")
        return "\n".join(lines)

    # ---- Update -----------------------------------------------------
    def login(self, player_id: int) -> str:
        p, reward = self._interactor.login(player_id)
        msg = [
            f"おかえりなさい！ 放置時間 {reward.elapsed_seconds:.0f} 秒",
            f"  放置報酬: EXP +{reward.gained_exp} / Gold +{reward.gained_gold}",
        ]
        if reward.levelups:
            msg.append(f"  ★ {reward.levelups} レベルアップ！")
        msg.append("  " + self._status_line(p))
        return "\n".join(msg)

    def adventure(self, player_id: int) -> str:
        p, res = self._interactor.adventure(player_id)
        msg = [f"冒険に出た！ EXP +{res.gained_exp} / Gold +{res.gained_gold}"]
        if res.levelups:
            msg.append(f"  ★ {res.levelups} レベルアップ！")
        msg.append("  " + self._status_line(p))
        return "\n".join(msg)

    def rename(self, player_id: int, new_name: str) -> str:
        p = self._interactor.rename(player_id, new_name)
        return f"改名: {self._status_line(p)}"

    # ---- Delete -----------------------------------------------------
    def retire(self, player_id: int) -> str:
        self._interactor.retire(player_id)
        return f"id={player_id} を引退させました。"
