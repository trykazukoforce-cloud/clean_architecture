"""Interface Adapter層: Tkinter デスクトップ GUI

CLI(controller.py)、HTTP(http_controller.py) と並列のもう1つの Adapter。
内側(UseCase)はこのAdapterの存在を知らない。
PlayerInteractor をコンストラクタ・インジェクションで受け取り、
ボタン操作 → UseCase呼び出し → エンティティ→GUI表示の変換 を行う。
"""
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

from src.domain.player import Player
from src.usecase.errors import NameAlreadyExistsError, PlayerNotFoundError
from src.usecase.player_interactor import PlayerInteractor


class GameWindow:
    """放置型RPGのGUI。PlayerInteractor を注入して使う。"""

    COLUMNS = ("rank", "id", "name", "level", "exp", "gold", "power")
    HEADINGS = {
        "rank": "順位", "id": "ID", "name": "名前", "level": "Lv",
        "exp": "EXP", "gold": "Gold", "power": "戦闘力",
    }

    def __init__(
        self,
        root: tk.Tk,
        interactor: PlayerInteractor,
        backend_label: str = "",
    ) -> None:
        self._interactor = interactor       # 抽象的なUseCase。中身は知らない
        self._root = root
        self._root.title("放置型RPG")
        self._root.geometry("780x520")

        self._build_widgets(backend_label)
        self.refresh()

    # ---- ウィジェット構築 -------------------------------------------
    def _build_widgets(self, backend_label: str) -> None:
        top = ttk.Frame(self._root, padding=8)
        top.pack(fill=tk.X)
        ttk.Label(
            top, text=f"セーブ先: {backend_label}", font=("", 10, "bold")
        ).pack(side=tk.LEFT)
        ttk.Button(top, text="新規作成 (Create)", command=self._on_create).pack(
            side=tk.RIGHT, padx=4
        )
        ttk.Button(top, text="更新 (Read)", command=self.refresh).pack(side=tk.RIGHT)

        # ランキング Treeview (Read)
        tree_frame = ttk.Frame(self._root, padding=(8, 0))
        tree_frame.pack(fill=tk.BOTH, expand=True)
        self._tree = ttk.Treeview(
            tree_frame, columns=self.COLUMNS, show="headings", height=12
        )
        for col in self.COLUMNS:
            self._tree.heading(col, text=self.HEADINGS[col])
            self._tree.column(col, width=80, anchor=tk.CENTER)
        self._tree.column("name", width=180, anchor=tk.W)
        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self._tree.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self._tree.configure(yscrollcommand=sb.set)

        # 操作ボタン (Update/Delete)
        action = ttk.Frame(self._root, padding=8)
        action.pack(fill=tk.X)
        ttk.Label(action, text="選択中のプレイヤーへの操作:").pack(side=tk.LEFT)
        ttk.Button(action, text="冒険 (Update)", command=self._on_adventure).pack(
            side=tk.LEFT, padx=4
        )
        ttk.Button(action, text="ログイン/放置精算 (Update)", command=self._on_login).pack(
            side=tk.LEFT, padx=4
        )
        ttk.Button(action, text="改名 (Update)", command=self._on_rename).pack(
            side=tk.LEFT, padx=4
        )
        ttk.Button(action, text="引退 (Delete)", command=self._on_retire).pack(
            side=tk.LEFT, padx=4
        )

        # ログ表示エリア
        log_frame = ttk.LabelFrame(self._root, text="ログ", padding=4)
        log_frame.pack(fill=tk.BOTH, padx=8, pady=(0, 8))
        self._log = tk.Text(log_frame, height=8, state=tk.DISABLED, wrap=tk.WORD)
        self._log.pack(fill=tk.BOTH, expand=True)

    # ---- プレゼンタ補助 ---------------------------------------------
    @staticmethod
    def _player_row(rank: int, p: Player) -> tuple:
        need = Player.exp_to_next(p.level)
        return (rank, p.id, p.name, p.level, f"{p.exp}/{need}", p.gold, p.power)

    def _append_log(self, text: str) -> None:
        self._log.configure(state=tk.NORMAL)
        self._log.insert(tk.END, text + "\n")
        self._log.see(tk.END)
        self._log.configure(state=tk.DISABLED)

    def _selected_id(self) -> int | None:
        sel = self._tree.selection()
        if not sel:
            messagebox.showinfo("情報", "プレイヤーを選択してください。")
            return None
        return int(self._tree.item(sel[0])["values"][1])

    def _run(self, fn, *args, **kwargs):
        """UseCase 呼び出し共通: 例外をダイアログにマップする。"""
        try:
            return fn(*args, **kwargs)
        except PlayerNotFoundError as e:
            messagebox.showerror("見つかりません", str(e))
        except NameAlreadyExistsError as e:
            messagebox.showerror("名前重複", str(e))
        except ValueError as e:
            messagebox.showerror("入力エラー", str(e))
        return None

    # ---- イベントハンドラ -------------------------------------------
    def refresh(self) -> None:
        self._tree.delete(*self._tree.get_children())
        for rank, p in enumerate(self._interactor.ranking(), 1):
            self._tree.insert("", tk.END, values=self._player_row(rank, p))

    def _on_create(self) -> None:
        name = simpledialog.askstring("新規作成", "名前:")
        if name is None:
            return
        p = self._run(self._interactor.create_player, name)
        if p:
            self._append_log(f"キャラ作成: [id={p.id}] {p.name}")
            self.refresh()

    def _on_adventure(self) -> None:
        pid = self._selected_id()
        if pid is None:
            return
        result = self._run(self._interactor.adventure, pid)
        if result:
            p, res = result
            self._append_log(
                f"冒険: {p.name} EXP+{res.gained_exp} Gold+{res.gained_gold}"
                + (f"  ★Lvアップx{res.levelups}" if res.levelups else "")
            )
            self.refresh()

    def _on_login(self) -> None:
        pid = self._selected_id()
        if pid is None:
            return
        result = self._run(self._interactor.login, pid)
        if result:
            p, reward = result
            self._append_log(
                f"ログイン: {p.name} 放置{reward.elapsed_seconds:.0f}秒"
                f" EXP+{reward.gained_exp} Gold+{reward.gained_gold}"
                + (f"  ★Lvアップx{reward.levelups}" if reward.levelups else "")
            )
            self.refresh()

    def _on_rename(self) -> None:
        pid = self._selected_id()
        if pid is None:
            return
        new_name = simpledialog.askstring("改名", "新しい名前:")
        if new_name is None:
            return
        p = self._run(self._interactor.rename, pid, new_name)
        if p:
            self._append_log(f"改名: id={p.id} -> {p.name}")
            self.refresh()

    def _on_retire(self) -> None:
        pid = self._selected_id()
        if pid is None:
            return
        if not messagebox.askyesno("確認", f"id={pid} を引退させますか？"):
            return
        # retire は戻り値が None のため _run ヘルパは使わずインライン処理。
        try:
            self._interactor.retire(pid)
            self._append_log(f"引退: id={pid}")
        except PlayerNotFoundError as e:
            messagebox.showerror("見つかりません", str(e))
        except ValueError as e:
            messagebox.showerror("入力エラー", str(e))
        self.refresh()
