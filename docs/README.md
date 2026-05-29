# 設計書

本プロジェクトの設計書を、トピック別に5つの文書に分けて管理する。
特に「**クリーンアーキテクチャがどのように実装されているか**」を明確にすることを目的とする。

## 構成

| No. | ファイル | 内容 |
|-----|---------|------|
| 01 | [01_architecture.md](01_architecture.md) | クリーンアーキテクチャの設計原則・4層構成・依存ルール |
| 02 | [02_components.md](02_components.md) | 各モジュール（ファイル）の責務・依存・影響範囲 |
| 03 | [03_di.md](03_di.md) | Dependency Injection の方式・合成ルート・依存グラフ |
| 04 | [04_use_cases.md](04_use_cases.md) | CRUD ↔ ゲーム操作の対応、業務規則、シーケンス |
| 05 | [05_testing.md](05_testing.md) | テスト戦略（パラメータ化・FakeClock・TestClient） |

## 読む順序ガイド

### A. 全体像を掴みたい（初読）
1. `01_architecture.md` — クリーンアーキテクチャの原則と4層
2. `03_di.md` — どうやって層をつなぐか
3. `04_use_cases.md` — 何ができるアプリか

### B. 改修・追加機能を入れる前
1. `02_components.md` — 触る予定のファイルの影響範囲を確認
2. `04_use_cases.md` — 既存業務規則を確認
3. `05_testing.md` — どこにテストを追加すべきか

### C. テストが落ちた・期待値を変えたい
1. `04_use_cases.md` — 業務規則の意図確認
2. `05_testing.md` — テストの構造とパラメータ化の仕組み

### D. クリーンアーキテクチャの実装が知りたい
1. `01_architecture.md` の §2「設計原則」と §6「依存方向の検証」
2. `02_components.md` の **Domain層 / UseCase層** セクション
3. `03_di.md` 全体

## 設計原則のサマリ

- **依存ルール**: ソースコードの依存は内側にのみ向く
- **依存性逆転**: UseCase が抽象（ポート）を定義し、Infrastructure が実装する
- **関心の分離**: 4層（Domain / UseCase / Adapter / Infrastructure）に責務を分割
- **置換可能性**: 保存先（DB/JSON）・時計（本物/擬似）・入出力（CLI/HTTP/GUI）を内側を変えず差し替え可能

## 3条件との対応

| 条件 | 設計上の実現 | 詳細 |
|------|------------|------|
| DB に CRUD | `SqlitePlayerRepository` | 02_components.md §Infrastructure層 |
| JSON にローカル CRUD | `JsonPlayerRepository` | 同上 |
| DI で切替 | `container.build_*` 群 | 03_di.md §4 |

## プロジェクト構成（ファイル木）

```
clean_architecture/
├── docs/                       ← 本設計書
│   ├── README.md (本ファイル)
│   ├── 01_architecture.md
│   ├── 02_components.md
│   ├── 03_di.md
│   ├── 04_use_cases.md
│   └── 05_testing.md
├── src/
│   ├── domain/
│   │   └── player.py           ← Domain層
│   ├── usecase/
│   │   ├── repository.py       ← ポート(抽象)
│   │   ├── errors.py
│   │   └── player_interactor.py
│   ├── adapter/
│   │   ├── controller.py       ← CLI
│   │   ├── http_controller.py  ← REST API
│   │   └── gui_view.py         ← GUI
│   ├── infrastructure/
│   │   ├── sqlite_repository.py
│   │   └── json_repository.py
│   └── container.py            ← DIコンテナ
├── main.py                     ← CLI エントリ
├── api.py                      ← REST API エントリ
├── gui.py                      ← GUI エントリ
├── tests/
│   ├── test_player.py          ← UseCase+Infra (2backend × 9件)
│   ├── test_api.py             ← HTTP (2backend × 2件)
│   └── test_gui_smoke.py
└── README.md                   ← 利用者向けトップREADME
```
