# 05. テスト戦略

## 1. 方針

クリーンアーキテクチャの恩恵は、テスト戦略に明確に表れる：

- **Domain** はピュアな関数の集合 → ユニットテストが最も書きやすい
- **UseCase** はポートを抽象に持つ → Fake 実装を注入すれば、本物のDB不要でテスト可能
- **Adapter** は薄く、UseCase に委譲 → 統合テストで「外部表現変換」の正しさを確認

テストピラミッド：

```
              ┌─────────────────┐
              │   GUI smoke (1) │     ← 構築できるか確認のみ
              └─────────────────┘
            ┌─────────────────────┐
            │  HTTP integration   │   ← TestClient で API 全層を叩く
            │   (2 backends × 2)  │
            └─────────────────────┘
        ┌─────────────────────────────┐
        │  UseCase + Infrastructure   │ ← 両 backend を統合パラメータ化
        │     (2 backends × 9)        │
        └─────────────────────────────┘
    ┌─────────────────────────────────────┐
    │       Domain unit (1)               │ ← 純粋関数の検証
    └─────────────────────────────────────┘
```

全 22 件パスする状態を保つ。

---

## 2. テストファイル構成

| ファイル | 対象 | 件数 |
|---------|------|------|
| `tests/test_player.py` | Domain + UseCase + Infrastructure 統合 | 17 (16パラメータ化 + 1ドメイン単体) |
| `tests/test_api.py` | HTTP Adapter (TestClient) | 4 (2テスト × 2backend) |
| `tests/test_gui_smoke.py` | GUI Adapter (構築のみ) | 1 |

---

## 3. パラメータ化テスト — 両 backend 同時検証

クリーンアーキテクチャの「**保存先を切り替えても挙動は同じ**」を機械的に保証する手法。

```python
# tests/test_player.py 抜粋

@pytest.fixture(params=["sqlite", "json"])
def uc(request):
    clock = FakeClock()
    sqlite_uc, json_uc = make_interactors(clock)
    uc = sqlite_uc if request.param == "sqlite" else json_uc
    uc._clock = clock
    return uc


def test_create_and_read(uc):
    p = uc.create_player("Alice")
    assert uc.get(p.id).name == "Alice"
```

1つのテスト関数が、SQLite版とJSON版それぞれで実行される。
**期待値が同じ** ということは、「Repository実装の振る舞いが等価」ということが
テストで担保されていることを意味する。

---

## 4. FakeClock — 時計の注入によるテスト容易性

放置型RPG は時間に依存する。実時間を待つテストは遅く、不安定。
**時計をDIする**ことで、テスト時には任意の値を返す擬似時計に差し替える。

```python
class FakeClock:
    def __init__(self, start: float = 1000.0) -> None:
        self.t = start

    def __call__(self) -> float:
        return self.t

    def tick(self, seconds: float) -> None:
        self.t += seconds
```

使用例：

```python
def test_idle_reward_levels_up(uc):
    p = uc.create_player("Idler")
    uc._clock.tick(100)                    # 100秒進める
    p2, reward = uc.login(p.id)
    assert reward.gained_exp == 500        # 100s * 5exp/s
    assert reward.gained_gold == 200       # 100s * 2gold/s
    assert p2.level == 3
    assert p2.exp == 200
    assert reward.levelups == 2
```

実時間を1秒も待たずに「100秒放置の結果」を検証できる。
この設計が無ければ、放置型RPGのテストは現実的に書けない。

---

## 5. UseCase の業務規則テスト

| テスト関数 | 検証内容 |
|-----------|---------|
| `test_create_and_read` | Create と Read の基本動作 |
| `test_idle_reward_levels_up` | 放置精算による経験値・ゴールド・レベル変化 |
| `test_idle_persists_across_reload` | last_seen が永続化される（再取得しても整合） |
| `test_adventure` | 冒険の固定報酬計算 |
| `test_ranking_order` | Lv→exp 降順ソート |
| `test_retire` | Delete と「存在確認」 |
| `test_duplicate_name` | NameAlreadyExistsError |
| `test_domain_validation` | name 空のドメイン検証エラー |
| `test_levelup_logic_unit` | Player.gain のレベル計算（ドメイン単体） |

これらすべてが両 backend で実行される。**ロジックの正しさと、永続化実装の差異の両方を同時にテスト**できる。

---

## 6. HTTP統合テスト — `TestClient`

`fastapi.testclient.TestClient` を使い、実HTTPサーバを起動せずに API を検証する。
ここでも 2 backend をパラメータ化する。

```python
@pytest.fixture(params=["sqlite", "json"])
def client_and_clock(request):
    return _make(request.param)


def test_full_crud_via_http(client_and_clock):
    client, clock = client_and_clock

    r = client.post("/players", json={"name": "Alice"})
    assert r.status_code == 201

    clock.tick(100)
    r = client.post(f"/players/1/login")
    assert r.json()["reward"]["gained_exp"] == 500
```

検証内容：
- 201 Created, 200 OK, 204 No Content の正しい返却
- 404 (`PlayerNotFoundError`), 409 (`NameAlreadyExistsError`), 400 (`ValueError`) のマッピング
- Pydantic DTO の正しい組み立て
- 両 backend で API 応答が同一

---

## 7. GUI スモークテスト

GUI のクリック操作を自動化すると、テストが脆くなりやすい。本プロジェクトでは
「**GUI が UseCase を正しく注入されて構築でき、Treeview にデータが反映される**」
ことだけを保証する。

```python
tk = pytest.importorskip("tkinter")
try:
    _probe = tk.Tk()
    _probe.destroy()
except Exception as e:
    pytest.skip(f"GUI不可: {e}", allow_module_level=True)
```

ヘッドレス環境（CI など）では自動 skip され、ローカルでは構築検証が走る。

---

## 8. テスト実行

```bash
python -m pip install pytest fastapi httpx
python -m pytest -q              # 22 passed
python -m pytest tests/test_player.py -v    # UseCase詳細
python -m pytest tests/test_api.py -v       # HTTP詳細
```

---

## 9. テスト設計の総括

| クリーンアーキテクチャの恩恵 | 本プロジェクトでの実例 |
|--------------------------|---------------------|
| Domain は依存ゼロ → 純粋関数テスト | `test_levelup_logic_unit` |
| UseCase はポート抽象に依存 → Fake差し込み | パラメータ化フィクスチャ `uc` |
| 時計を注入 → 時間依存処理を瞬時に検証 | `FakeClock`, `test_idle_*` |
| Adapter は薄い → TestClient で全体検証 | `test_full_crud_via_http` |
| 入出力差し替え可能 → GUI/CLI/APIで同じ業務ルール | 同じテストデータが3チャネル全部に通用 |

「テスト容易性」を犠牲にする設計を採用すると、テストは書けたとしても遅く・脆く・保守が大変になる。
クリーンアーキテクチャは、テストが**書きやすく、速く、安定する**ことを設計から強制する。

---

## 関連ドキュメント

- 01_architecture.md — 設計原則
- 03_di.md — 注入される依存
- 04_use_cases.md — テスト対象の業務規則
