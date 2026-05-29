# 02. コンポーネント設計

各モジュールの責務・依存・公開インタフェース・変更時の影響範囲を file-by-file で記述する。
影響範囲の理解は **保守性の核** である。

## 目次

- [Domain層](#domain層)
  - [src/domain/player.py](#srcdomainplayerpy)
- [UseCase層](#usecase層)
  - [src/usecase/repository.py](#srcusecaserepositorypy)
  - [src/usecase/errors.py](#srcusecaseerrorspy)
  - [src/usecase/player_interactor.py](#srcusecaseplayer_interactorpy)
- [Interface Adapter層](#interface-adapter層)
  - [src/adapter/controller.py](#srcadaptercontrollerpy)
  - [src/adapter/http_controller.py](#srcadapterhttp_controllerpy)
  - [src/adapter/gui_view.py](#srcadaptergui_viewpy)
- [Infrastructure層](#infrastructure層)
  - [src/infrastructure/sqlite_repository.py](#srcinfrastructuresqlite_repositorypy)
  - [src/infrastructure/json_repository.py](#srcinfrastructurejson_repositorypy)
- [合成ルート](#合成ルート)
  - [src/container.py](#srccontainerpy)
  - [main.py / api.py / gui.py](#mainpy--apipy--guipy)

---

## Domain層

### `src/domain/player.py`

| 項目 | 内容 |
|------|------|
| **層** | Domain |
| **責務** | プレイヤーのセーブデータ表現とゲーム規則（自己検証 / レベル曲線 / 経験値加算 / 戦闘力） |
| **依存先** | 標準ライブラリ `dataclasses` のみ |
| **公開** | `Player` (dataclass) |
| **公開メソッド** | `validate()`, `exp_to_next(level)`, `gain(exp, gold) -> int`, `power` (property) |

**フィールド**

| 名前 | 型 | デフォルト | 意味 |
|------|----|-----------|------|
| `name` | str | — | プレイヤー名（必須） |
| `level` | int | 1 | 現在のレベル（1以上） |
| `exp` | int | 0 | 経験値（非負） |
| `gold` | int | 0 | 所持ゴールド（非負） |
| `last_seen` | float | 0.0 | 最終プレイ時刻（epoch秒）。**放置報酬の計算に使う** |
| `id` | int \| None | None | 永続化時に採番される |

**変更時の影響範囲**

- フィールド追加 → SQLite/JSON 両 Repository のスキーマ・dict変換と、PlayerOut(DTO)、GUI Treeview列に伝播
- ゲーム規則変更（`gain` のレベル曲線）→ テスト `test_idle_reward_levels_up` / `test_levelup_logic_unit` の期待値修正

---

## UseCase層

### `src/usecase/repository.py`

| 項目 | 内容 |
|------|------|
| **層** | UseCase |
| **責務** | 永続化のポート（抽象）。CRUD のシグネチャを定義 |
| **依存先** | `src.domain.player` |
| **公開** | `PlayerRepository` (ABC) |

**メソッド**

| シグネチャ | 意味 |
|------------|------|
| `create(player: Player) -> Player` | 保存して id 付きで返す |
| `find_by_id(player_id: int) -> Player \| None` | 1件取得 |
| `list_all() -> list[Player]` | 全件取得 |
| `update(player: Player) -> Player` | 既存を更新 |
| `delete(player_id: int) -> None` | 削除 |

**変更時の影響範囲**

- メソッド追加/削除 → 全実装（SQLite/JSON）とインタラクタに伝播
- 引数/戻り値変更 → 同上

### `src/usecase/errors.py`

| 項目 | 内容 |
|------|------|
| **層** | UseCase |
| **責務** | アプリケーション固有の例外定義 |
| **依存先** | なし |
| **公開** | `PlayerNotFoundError`, `NameAlreadyExistsError` |

これらの例外を **HTTPステータスに対応させるのは Adapter の責務**（UseCase は HTTP を知らない）。

### `src/usecase/player_interactor.py`

| 項目 | 内容 |
|------|------|
| **層** | UseCase |
| **責務** | アプリケーション業務手順（ゲーム操作）の実装。CRUD ↔ ゲーム操作の対応を持つ |
| **依存先** | `src.domain.player`, `src.usecase.repository`, `src.usecase.errors`, `time`（注入可） |
| **公開** | `PlayerInteractor`, `IdleReward`, `AdventureResult` |

**コンストラクタの注入対象**

| 引数 | 型 | 用途 |
|------|----|------|
| `repository` | `PlayerRepository` | 保存先（実装は知らない） |
| `now` | `Callable[[], float]` | 時計。FakeClock を渡すことで放置時間をテスト可能に |
| `idle_exp_per_sec` | float | 放置経験値レート（バランス調整値） |
| `idle_gold_per_sec` | float | 放置ゴールドレート |
| `idle_cap_seconds` | float | 放置報酬上限（最大8時間ぶん） |

**公開メソッド ↔ CRUD 対応**

| メソッド | CRUD | 業務動作 |
|---------|------|----------|
| `create_player(name)` | Create | 同名チェック→`Player` 生成→保存 |
| `get(player_id)` | Read | 取得、無ければ例外 |
| `ranking()` | Read | レベル降順→経験値降順でソート |
| `login(player_id)` | Update | 放置報酬を精算し `last_seen` 更新 |
| `adventure(player_id)` | Update | 固定式で報酬を即時付与 |
| `rename(player_id, new_name)` | Update | 名前のみ変更 |
| `retire(player_id)` | Delete | 存在確認→削除 |

**変更時の影響範囲**

- メソッド追加 → 各 Adapter（CLI/HTTP/GUI）に呼び出しを追加できる（Adapter改変は任意）
- 業務規則の変更 → テストの期待値、ドキュメント04章の更新

---

## Interface Adapter層

### `src/adapter/controller.py`

| 項目 | 内容 |
|------|------|
| **層** | Adapter (CLI) |
| **責務** | CLI 用のプレゼンタ。`Player` を表示用文字列に変換し、Interactor を呼ぶ |
| **依存先** | `src.domain.player`, `src.usecase.player_interactor` |
| **公開** | `PlayerController` |

**メソッド ↔ Interactor**

| Controller | 呼ぶ Interactor | 戻り値 |
|-----------|----------------|--------|
| `create(name)` | `create_player` | 1行のステータス文字列 |
| `status(id)` | `get` | 同上 |
| `ranking()` | `ranking` | 複数行 |
| `login(id)` | `login` | 放置時間と報酬を整形 |
| `adventure(id)` | `adventure` | 報酬とLvアップ表示 |
| `rename(id, name)` | `rename` | ステータス文字列 |
| `retire(id)` | `retire` | 引退メッセージ |

### `src/adapter/http_controller.py`

| 項目 | 内容 |
|------|------|
| **層** | Adapter (HTTP) |
| **責務** | FastAPI ルート定義 / Pydantic DTO 変換 / UseCase 例外 → HTTPステータス マッピング |
| **依存先** | `fastapi`, `pydantic`, `src.domain.player`, `src.usecase.*` |
| **公開** | `create_app(interactor)`, `PlayerOut`, `CreatePlayerIn`, `RenameIn`, `IdleRewardOut`, `LoginOut`, `AdventureResultOut`, `AdventureOut` |

**ルート ↔ Interactor**

| Method | Path | 呼ぶ Interactor | 成功時ステータス |
|--------|------|----------------|-----------------|
| POST | `/players` | `create_player` | 201 |
| GET | `/players` | `ranking` | 200 |
| GET | `/players/{id}` | `get` | 200 |
| POST | `/players/{id}/login` | `login` | 200 |
| POST | `/players/{id}/adventure` | `adventure` | 200 |
| PATCH | `/players/{id}` | `rename` | 200 |
| DELETE | `/players/{id}` | `retire` | 204 |

**例外マッピング**

| 例外 | HTTPステータス |
|------|---------------|
| `PlayerNotFoundError` | 404 |
| `NameAlreadyExistsError` | 409 |
| `ValueError`（Domain検証エラー） | 400 |

### `src/adapter/gui_view.py`

| 項目 | 内容 |
|------|------|
| **層** | Adapter (GUI) |
| **責務** | Tkinter ウィンドウ。Treeview/ボタン/ダイアログから Interactor を呼ぶ |
| **依存先** | `tkinter`, `src.domain.player`, `src.usecase.*` |
| **公開** | `GameWindow(root, interactor, backend_label)` |

**ウィジェット構成**

| 領域 | 内容 |
|------|------|
| 上部 | backend表示、`新規作成 (Create)`, `更新 (Read)` ボタン |
| 中央 | プレイヤーランキング Treeview（順位 / id / 名前 / Lv / EXP / Gold / 戦闘力） |
| 下部 | 選択行への操作: `冒険`, `ログイン放置精算`, `改名`, `引退` |
| 最下部 | 操作ログ（Lvアップ等を表示） |

**例外マッピング**: `PlayerNotFoundError` / `NameAlreadyExistsError` / `ValueError` → `messagebox.showerror`

---

## Infrastructure層

### `src/infrastructure/sqlite_repository.py`

| 項目 | 内容 |
|------|------|
| **層** | Infrastructure |
| **責務** | `PlayerRepository` を SQLite で実装 |
| **依存先** | `sqlite3`, `src.domain.player`, `src.usecase.repository` |
| **公開** | `SqlitePlayerRepository(db_path)` |

**スキーマ**

```sql
CREATE TABLE players (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    name      TEXT NOT NULL UNIQUE,
    level     INTEGER NOT NULL,
    exp       INTEGER NOT NULL,
    gold      INTEGER NOT NULL,
    last_seen REAL NOT NULL
)
```

**変更時の影響範囲**

- スキーマ変更 → マイグレーションが必要（学習用には DB ファイル削除でも可）
- 他層は無変更

### `src/infrastructure/json_repository.py`

| 項目 | 内容 |
|------|------|
| **層** | Infrastructure |
| **責務** | `PlayerRepository` をローカル JSON ファイルで実装 |
| **依存先** | `json`, `os`, `src.domain.player`, `src.usecase.repository` |
| **公開** | `JsonPlayerRepository(file_path)` |

**ファイル形式**

```json
[
  { "id": 1, "name": "JsonHero", "level": 2, "exp": 40,
    "gold": 50, "last_seen": 1779936473.7 }
]
```

**アルゴリズム特性**

- 各操作は「全件読込 → 加工 → 全件保存」する単純実装
- 小規模学習用として十分。性能要件があれば差し替える設計

---

## 合成ルート

### `src/container.py`

| 項目 | 内容 |
|------|------|
| **層** | 合成ルートの部品 |
| **責務** | 文字列1つ（"sqlite" / "json"）から、依存を順に組み立てて 各 Adapter を返す |
| **依存先** | 全層（合成ルートだから許される） |
| **公開** | `build_repository`, `build_interactor`, `build_controller`, `build_app`, `build_gui` |

**関数階層**

```
build_repository(backend)         ── 実装を選ぶ
        │
        ▼
build_interactor(backend, now)    ── PlayerInteractor を作る
        │
        ├──────────────────────────► build_controller  (CLI)
        ├──────────────────────────► build_app         (HTTP)
        └──────────────────────────► build_gui         (Tkinter)
```

### `main.py` / `api.py` / `gui.py`

| ファイル | 役割 | 引数 |
|---------|------|------|
| `main.py` | CLI 対話 / `--demo` | `sqlite` or `json` + `--demo`オプション |
| `api.py` | uvicorn 起動 | `sqlite` or `json` |
| `gui.py` | Tk mainloop | `sqlite` or `json` |

3つの合成ルートはそれぞれ `container.build_*` を呼んで Adapter を取得し、起動する。
**ここだけが「具体実装」を意識する**。

---

## 関連ドキュメント

- 01_architecture.md — 設計原則と層構成
- 03_di.md — DI と依存グラフ
- 04_use_cases.md — ユースケース別仕様
- 05_testing.md — テスト戦略
