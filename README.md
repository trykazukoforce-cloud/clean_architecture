# clean_architecture — 放置型RPG

クリーンアーキテクチャを勉強するためのプロジェクト。

**User（＝プレイヤーのセーブデータ）** を **DB(SQLite)** と **ローカルJSON** の両方に
CRUD でき、**Dependency Injection (DI)** によってコード変更なしで切り替えられる
「放置型RPG」サンプルです。

## CRUD ↔ ゲーム操作 の対応

| CRUD | ゲーム操作 | 実装(UseCase) |
|------|-----------|---------------|
| **C**reate | キャラ作成 | `create_player` |
| **R**ead | ステータス確認 / ランキング | `get` / `ranking` |
| **U**pdate | 放置報酬の精算 / 冒険でLvアップ | `login` / `adventure` |
| **D**elete | 引退 | `retire` |

「放置報酬」は最後にプレイした時刻 `last_seen` からの経過時間で計算します。
**この時刻はセーブデータに永続化されてこそ成立する** ため、
DB/JSON どちらに保存しても同じ挙動になることが学習ポイントです。

## 依存の方向（最重要ルール）

矢印は常に **外側 → 内側** にのみ向きます。内側は外側を知りません。

```
   ┌─────────────────────────────────────────────┐
   │ Infrastructure (詳細)                        │  ← 外側
   │   sqlite_repository.py / json_repository.py  │
   │   ┌─────────────────────────────────────┐    │
   │   │ Interface Adapter                   │    │
   │   │   controller.py     (CLI)           │    │
   │   │   http_controller.py(FastAPI)       │    │
   │   │   gui_view.py       (Tkinter GUI)   │    │
   │   │   ┌─────────────────────────────┐   │    │
   │   │   │ UseCase (ゲーム手順)        │   │    │
   │   │   │  player_interactor.py       │   │    │
   │   │   │  repository.py (ポート/抽象)│   │    │
   │   │   │   ┌─────────────────────┐   │   │    │
   │   │   │   │ Domain (ゲーム規則) │   │   │    │  ← 内側
   │   │   │   │   player.py         │   │   │    │
   │   │   │   └─────────────────────┘   │   │    │
   │   │   └─────────────────────────────┘   │    │
   │   └─────────────────────────────────────┘    │
   └─────────────────────────────────────────────┘
```

## ディレクトリ構成

| パス | 層 | 役割 |
|------|-----|------|
| `src/domain/player.py` | Domain | Playerエンティティ・レベルアップ/経験値ルール |
| `src/usecase/repository.py` | UseCase | `PlayerRepository`抽象（**ポート**） |
| `src/usecase/player_interactor.py` | UseCase | login(放置)/adventure/ranking 等のゲーム手順 |
| `src/usecase/errors.py` | UseCase | アプリ固有例外 |
| `src/adapter/controller.py` | Adapter | CLI 入出力変換（ステータス文字列化） |
| `src/adapter/http_controller.py` | Adapter | HTTP (FastAPI) Adapter — ルート定義・DTO・例外マッピング |
| `src/adapter/gui_view.py` | Adapter | **GUI (Tkinter) Adapter** — Treeview+ボタン |
| `src/infrastructure/sqlite_repository.py` | Infrastructure | ポートのSQLite実装 |
| `src/infrastructure/json_repository.py` | Infrastructure | ポートのJSON実装 |
| `src/container.py` | 合成 | DIコンテナ（CLI・HTTP・GUI を共通の Interactor から組み立て） |
| `main.py` | 合成ルート | 対話ゲーム / `--demo` (CLI) |
| `api.py` | 合成ルート | REST API サーバ起動 (uvicorn) |
| `gui.py` | 合成ルート | **デスクトップGUI起動 (Tkinter)** |

## DI の肝（依存性逆転の原則 / DIP）

`PlayerInteractor` は抽象 `PlayerRepository`（保存先）と `now`（時計）の **2つを注入** され、
SQLite か JSON か、本物の時計か擬似時計かを **知りません**。

```python
# src/container.py — ここだけが「どの実装か」を知る (合成ルート)
def build_repository(backend: str) -> PlayerRepository:
    if backend == "sqlite":
        return SqlitePlayerRepository(db_path="players.db")
    if backend == "json":
        return JsonPlayerRepository(file_path="players.json")
```

backend を変えても UseCase / Controller のコードは **一行も変わりません**。

## REST API (FastAPI) — 「もう1つのAdapter」

CLI と並列に、HTTP からも同じ UseCase を呼べます。**UseCase/Domain は一切変更していません** ——
新しい Adapter (`http_controller.py`) を足しただけです。これが「入出力チャネルを差し替え可能にする」効果。

```bash
python -m pip install fastapi "uvicorn[standard]" httpx
python api.py            # 既定 sqlite (players.db) で起動
python api.py json       # JSON セーブで起動
# → http://127.0.0.1:8000/docs で Swagger UI
```

### エンドポイント

| メソッド | パス | CRUD | 説明 |
|----------|------|------|------|
| POST | `/players` | Create | キャラ作成 |
| GET | `/players` | Read | ランキング |
| GET | `/players/{id}` | Read | ステータス確認 |
| POST | `/players/{id}/login` | Update | 放置報酬を精算 |
| POST | `/players/{id}/adventure` | Update | 冒険して報酬獲得 |
| PATCH | `/players/{id}` | Update | 改名 |
| DELETE | `/players/{id}` | Delete | 引退 |

UseCase 例外は Adapter 層で HTTP ステータスにマップされます：
- `PlayerNotFoundError` → **404**
- `NameAlreadyExistsError` → **409**
- ドメインの `ValueError` → **400**

## デスクトップGUI (Tkinter) — 3つめのAdapter

CLI / HTTP に続く 3つめの入出力チャネル。`Tkinter` は Python 標準同梱なので追加インストール不要。
ここでも **UseCase/Domain は一切変更していません** — `GameWindow` が `PlayerInteractor` を
コンストラクタで受け取るだけ。

```bash
python gui.py            # 既定 sqlite (players.db)
python gui.py json       # JSON セーブ (players.json)
```

ウィンドウには:
- 上部: backend表示・**新規作成 (Create)** ・**更新 (Read)** ボタン
- 中央: プレイヤーランキング Treeview
- 下部: 選択行に対する **冒険 / ログイン放置精算 / 改名 / 引退 (Update / Delete)**
- 最下部: 操作ログ

## 遊び方

```bash
python main.py                 # 既定sqlite で対話プレイ (CLI)
python main.py json            # JSONセーブで対話プレイ (CLI)
python main.py sqlite --demo   # スクリプト化デモ（時計を進めて放置を再現）
python api.py                  # REST API サーバ
python gui.py                  # デスクトップGUI
```

対話モードでは、いったん終了して時間を空けて再度 `login` すると放置報酬が貯まっています
（セーブデータ `players.db` / `players.json` に `last_seen` が保存されているため）。

## テスト

```bash
python -m pip install pytest fastapi httpx
python -m pytest -q          # 22 passed  (CLI 17 + HTTP API 4 + GUI smoke 1)
```

放置時間は注入した **擬似時計(FakeClock)** で固定するので、実時間を待たずにテストできます。
これが「時計もDIする」最大の利点です。

## 学習ポイント

1. **依存は内側へのみ** — `domain/player.py` は何も import しない（ゲーム規則の置き場）。
2. **ポートとアダプタ** — UseCaseが定義した抽象を Infrastructure が実装（依存の逆転）。
3. **合成ルートの集約** — `new`（具体生成）を `container.py`/`main.py` に閉じ込める。
4. **置換可能性** — 保存先(DB↔JSON)も時計(本物↔擬似)も、入出力(CLI↔HTTP↔GUI)も、
   内側を変えずに差し替えられる。ゲーム化しても、API化しても、GUI化しても、原則は崩れない。
