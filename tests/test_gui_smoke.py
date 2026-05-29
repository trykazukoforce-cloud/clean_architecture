"""GUIスモークテスト: Tk が利用可能な環境でのみ、構築できることを確認。

GUI の中身(ボタンクリック等)は手動確認の範囲とし、ここでは
- 依存注入が成立し、ウィジェットが例外なく作れる
- refresh() が UseCase を呼んで Treeview を更新できる
を最低限担保する。
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Tk が使えない環境(ヘッドレスCI等)では全テストスキップ
tk = pytest.importorskip("tkinter")
try:
    _probe = tk.Tk()
    _probe.destroy()
except Exception as e:  # noqa: BLE001
    pytest.skip(f"GUI不可: {e}", allow_module_level=True)

from src.adapter.gui_view import GameWindow  # noqa: E402
from src.infrastructure.sqlite_repository import SqlitePlayerRepository  # noqa: E402
from src.usecase.player_interactor import PlayerInteractor  # noqa: E402


def test_gui_constructs_and_refreshes():
    """GUI が UseCase を注入されて構築でき、データ反映できる。"""
    interactor = PlayerInteractor(SqlitePlayerRepository(":memory:"))
    interactor.create_player("ShownInGUI")  # 1件作っておく

    root = tk.Tk()
    try:
        window = GameWindow(root, interactor, backend_label="test")
        root.update()  # ウィジェットを描画状態に
        # Treeview に1行入っていること
        rows = window._tree.get_children()
        assert len(rows) == 1
        values = window._tree.item(rows[0])["values"]
        assert values[2] == "ShownInGUI"  # name列
    finally:
        root.destroy()
