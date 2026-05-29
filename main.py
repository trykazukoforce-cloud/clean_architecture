"""エントリポイント (Composition Root / 合成ルート) — 放置型RPG

使い方:
    python main.py                 # 既定sqlite で対話プレイ
    python main.py json            # JSONセーブで対話プレイ
    python main.py sqlite --demo   # スクリプト化デモ (時計を擬似的に進める)

CRUD とゲーム操作の対応:
    Create = キャラ作成 / Read = ステータス・ランキング
    Update = 放置報酬(login)・冒険(adventure) / Delete = 引退
"""
from __future__ import annotations

import sys

from src.container import build_controller


# ---- スクリプト化デモ (動作確認用・時計を注入して放置を再現) -------------
def run_demo(backend: str) -> None:
    print(f"\n===== DEMO backend = {backend} =====")

    # 擬似時計: 呼ぶたびに任意の値を返せる。これで「放置時間」を自在に再現。
    clock = {"t": 1000.0}

    def fake_now() -> float:
        return clock["t"]

    game = build_controller(backend, now=fake_now)

    print(game.create("勇者アレックス"))
    print(game.create("魔法使いベラ"))

    print("\n-- 勇者が冒険に2回 --")
    print(game.adventure(1))
    print(game.adventure(1))

    print("\n-- 2時間放置してからログイン --")
    clock["t"] += 2 * 60 * 60  # 時計を2時間進める = 2時間放置
    print(game.login(1))

    print("\n-- ベラも少し冒険 --")
    print(game.adventure(2))

    print("\n" + game.ranking())

    print("\n-- 魔法使いベラを引退 (Delete) --")
    print(game.retire(2))
    print(game.ranking())


# ---- 対話プレイ ---------------------------------------------------------
MENU = """
==== 放置型RPG ====
 1) キャラ作成        (Create)
 2) ログイン/放置精算 (Update)
 3) 冒険する          (Update)
 4) ステータス確認    (Read)
 5) ランキング        (Read)
 6) 改名              (Update)
 7) 引退              (Delete)
 0) 終了
"""


def _ask_int(prompt: str) -> int:
    return int(input(prompt).strip())


def run_interactive(backend: str) -> None:
    game = build_controller(backend)  # 本物の時計(time.time)で放置時間を計測
    print(f"セーブ先: {backend}")
    while True:
        print(MENU)
        try:
            choice = input("選択> ").strip()
            if choice == "0":
                print("またね！")
                return
            elif choice == "1":
                print(game.create(input("名前: ").strip()))
            elif choice == "2":
                print(game.login(_ask_int("id: ")))
            elif choice == "3":
                print(game.adventure(_ask_int("id: ")))
            elif choice == "4":
                print(game.status(_ask_int("id: ")))
            elif choice == "5":
                print(game.ranking())
            elif choice == "6":
                pid = _ask_int("id: ")
                print(game.rename(pid, input("新しい名前: ").strip()))
            elif choice == "7":
                print(game.retire(_ask_int("id: ")))
            else:
                print("不正な選択です。")
        except (ValueError, Exception) as e:  # noqa: BLE001 デモ簡略化
            print(f"エラー: {e}")


def main() -> None:
    args = [a for a in sys.argv[1:]]
    backend = "sqlite"
    demo = False
    for a in args:
        if a == "--demo":
            demo = True
        else:
            backend = a
    if demo:
        run_demo(backend)
    else:
        run_interactive(backend)


if __name__ == "__main__":
    main()
