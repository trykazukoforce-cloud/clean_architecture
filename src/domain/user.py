"""Domain層: エンティティ (最も内側)

クリーンアーキテクチャの最重要ルール = 依存は内側へのみ向く。
この層は「業務の核」であり、フレームワーク/DB/UI など外側の
都合を一切知らない。標準ライブラリ以外をimportしないこと。
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class User:
    """Userエンティティ。

    id は永続化時に採番される想定のため Optional。
    エンティティ自身が「正しい状態とは何か」を知っている (自己検証)。
    """

    name: str
    email: str
    id: int | None = None

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        """業務ルール (エンタープライズ規則) をエンティティ内で保証する。"""
        if not self.name or not self.name.strip():
            raise ValueError("name は必須です")
        if "@" not in self.email:
            raise ValueError(f"email の形式が不正です: {self.email!r}")
