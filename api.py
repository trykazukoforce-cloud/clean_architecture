"""APIエントリポイント (合成ルート / HTTP版)

CLIの main.py と並列に、もう1つの「外側からの入力チャネル」として
HTTP APIを公開する。UseCase/Domain は両方から共有される。

使い方:
    python api.py                # 既定: sqlite (players.db)
    python api.py json           # JSONセーブ
  → http://127.0.0.1:8000/docs で Swagger UI が開く
"""
from __future__ import annotations

import sys

import uvicorn

from src.container import build_app


def main() -> None:
    backend = sys.argv[1] if len(sys.argv) > 1 else "sqlite"
    app = build_app(backend)
    print(f"API: backend={backend}  Swagger UI -> http://127.0.0.1:8000/docs")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")


if __name__ == "__main__":
    main()
