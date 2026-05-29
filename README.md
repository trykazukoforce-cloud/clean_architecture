# clean_architecture

クリーンアーキテクチャを勉強するためのプロジェクト。

User データを **DB(SQLite)** と **ローカルJSON** の両方に CRUD でき、
**Dependency Injection (DI)** によってコード変更なしで切り替えられるサンプルです。

## 依存の方向（最重要ルール）

矢印は常に **外側 → 内側** にのみ向きます。内側は外側を知りません。

```
   ┌─────────────────────────────────────────────┐
   │ Infrastructure (詳細)                        │  ← 外側
   │   sqlite_repository.py / json_repository.py  │
   │   ┌─────────────────────────────────────┐    │
   │   │ Interface Adapter                   │    │
   │   │   controller.py                     │    │
   │   │   ┌─────────────────────────────┐   │    │
   │   │   │ UseCase (業務手順)          │   │    │
   │   │   │  user_interactor.py         │   │    │
   │   │   │  repository.py (ポート/抽象)│   │    │
   │   │   │   ┌─────────────────────┐   │   │    │
   │   │   │   │ Domain (エンティティ)│  │   │    │  ← 内側
   │   │   │   │   user.py           │   │   │    │
   │   │   │   └─────────────────────┘   │   │    │
   │   │   └─────────────────────────────┘   │    │
   │   └─────────────────────────────────────┘    │
   └─────────────────────────────────────────────┘
```

## ディレクトリ構成

| パス | 層 | 役割 | 依存先 |
|------|-----|------|--------|
| `src/domain/user.py` | Domain | Userエンティティ・ドメイン検証 | なし（標準ライブラリのみ） |
| `src/usecase/repository.py` | UseCase | `UserRepository`抽象（**ポート**） | domain |
| `src/usecase/user_interactor.py` | UseCase | CRUD業務手順・email重複禁止 | domain, ポート |
| `src/usecase/errors.py` | UseCase | アプリ固有例外 | なし |
| `src/adapter/controller.py` | Adapter | 入出力変換（DTO化） | usecase |
| `src/infrastructure/sqlite_repository.py` | Infrastructure | ポートのSQLite実装 | usecase, domain, sqlite3 |
| `src/infrastructure/json_repository.py` | Infrastructure | ポートのJSON実装 | usecase, domain, json |
| `src/container.py` | 合成 | DIコンテナ（実装の選択） | 全層 |
| `main.py` | 合成ルート | エントリポイント | container |

## DI の肝（依存性逆転の原則 / DIP）

- `UserInteractor` は **抽象 `UserRepository` にだけ** 依存し、
  SQLite か JSON かを **知らない**（`__init__`で受け取るだけ＝コンストラクタ・インジェクション）。
- 具体実装を選ぶのは `src/container.py` ただ一箇所（合成ルート）。
- backend を変えても UseCase / Controller のコードは **一行も変わらない**。

```python
# src/container.py — ここだけが「どの実装か」を知る
def build_repository(backend: str) -> UserRepository:
    if backend == "sqlite":
        return SqliteUserRepository(db_path="users.db")
    if backend == "json":
        return JsonUserRepository(file_path="users.json")
```

## 実行方法

```bash
python main.py sqlite   # SQLite(users.db) に CRUD
python main.py json     # ローカル users.json に CRUD
python main.py          # 既定: sqlite
```

同じデモ手順が、backend を変えるだけで両方で同一に動きます。

## テスト

```bash
python -m pip install pytest
python -m pytest -q
```

テストでは本番DBの代わりにインメモリSQLite/一時JSONを **注入** しています。
「差し替え可能だからテストしやすい」というクリーンアーキテクチャの利点が体感できます。

## 学習ポイント

1. **依存は内側へのみ** — `domain` は何も import しない。
2. **ポートとアダプタ** — UseCase が定義した抽象を Infrastructure が実装する（依存の逆転）。
3. **合成ルートの集約** — `new`（具体生成）を `container.py`/`main.py` に閉じ込める。
4. **置換可能性** — DB↔JSON↔モックを、内側のコードを変えずに差し替えられる。
