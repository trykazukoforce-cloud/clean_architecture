"""GUIエントリポイント (合成ルート / Tkinter版)

CLI(main.py) / HTTP(api.py) と並列の、3つめの「外側からの入力チャネル」。
UseCase/Domain は3つ全てから共有される。

使い方:
    python gui.py            # 既定: sqlite (players.db)
    python gui.py json       # JSONセーブ (players.json)
"""
from __future__ import annotations

import sys

from src.container import build_gui


def main() -> None:
    backend = sys.argv[1] if len(sys.argv) > 1 else "sqlite"
    root = build_gui(backend)
    root.mainloop()


if __name__ == "__main__":
    main()
