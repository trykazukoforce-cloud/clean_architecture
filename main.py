"""エントリポイント (Composition Root / 合成ルート)

実行例:
    python main.py            # 既定: sqlite
    python main.py json       # JSONファイルに保存
    python main.py sqlite     # SQLite DBに保存

同じデモ手順を、backend を変えるだけで両方で動かせることを示す。
"""
from __future__ import annotations

import sys

from src.container import build_controller


def demo(backend: str) -> None:
    print(f"\n===== backend = {backend} =====")
    # ここで初めて具体実装が決まる。以降は Controller 経由で同一コード。
    user = build_controller(backend)

    # CREATE
    alice = user.create("Alice", "alice@example.com")
    bob = user.create("Bob", "bob@example.com")
    print("created:", alice, bob)

    # READ
    print("list  :", user.list())
    print("get   :", user.get(alice["id"]))

    # UPDATE
    print("rename:", user.rename(alice["id"], "Alice Smith"))

    # DELETE
    user.delete(bob["id"])
    print("after delete:", user.list())


def main() -> None:
    backend = sys.argv[1] if len(sys.argv) > 1 else "sqlite"
    demo(backend)


if __name__ == "__main__":
    main()
