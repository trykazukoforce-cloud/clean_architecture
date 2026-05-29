"""Interface Adapter層: HTTP コントローラ (FastAPI)

CLIコントローラ(controller.py)と同じ「もう1つのAdapter」。
内側(UseCase)はこのAdapterの存在を知らない。
ここでは:
  - HTTPリクエスト → UseCase呼び出し
  - エンティティ → 外向きDTO(Pydantic)に変換 (プレゼンタ役)
  - UseCase例外 → HTTPステータスへマッピング
を行う。インタラクタはコンストラクタ・インジェクションで受け取る。
"""
from __future__ import annotations

from typing import List

from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.domain.player import Player
from src.usecase.errors import NameAlreadyExistsError, PlayerNotFoundError
from src.usecase.player_interactor import PlayerInteractor


# ---- 外向きDTO (Pydantic) — ドメインを漏らさないために変換 -------------
class PlayerOut(BaseModel):
    id: int
    name: str
    level: int
    exp: int
    exp_to_next: int
    gold: int
    power: int
    last_seen: float

    @classmethod
    def from_player(cls, p: Player) -> "PlayerOut":
        assert p.id is not None
        return cls(
            id=p.id,
            name=p.name,
            level=p.level,
            exp=p.exp,
            exp_to_next=Player.exp_to_next(p.level),
            gold=p.gold,
            power=p.power,
            last_seen=p.last_seen,
        )


class CreatePlayerIn(BaseModel):
    name: str


class RenameIn(BaseModel):
    name: str


class IdleRewardOut(BaseModel):
    elapsed_seconds: float
    gained_exp: int
    gained_gold: int
    levelups: int


class LoginOut(BaseModel):
    player: PlayerOut
    reward: IdleRewardOut


class AdventureResultOut(BaseModel):
    gained_exp: int
    gained_gold: int
    levelups: int


class AdventureOut(BaseModel):
    player: PlayerOut
    result: AdventureResultOut


# ---- アプリ生成 (インタラクタを注入してFastAPIアプリを組み立てる) -------
def create_app(interactor: PlayerInteractor) -> FastAPI:
    app = FastAPI(title="放置型RPG API", version="1.0.0")

    # UseCase/Domain例外 → HTTPステータスのマッピング (Adapter層の責務)
    @app.exception_handler(PlayerNotFoundError)
    async def _not_found(_request, exc: PlayerNotFoundError):
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(NameAlreadyExistsError)
    async def _conflict(_request, exc: NameAlreadyExistsError):
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(ValueError)
    async def _bad_request(_request, exc: ValueError):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    # ---- Create ----
    @app.post("/players", response_model=PlayerOut, status_code=201)
    def create_player(body: CreatePlayerIn) -> PlayerOut:
        return PlayerOut.from_player(interactor.create_player(body.name))

    # ---- Read ----
    @app.get("/players", response_model=List[PlayerOut])
    def ranking() -> List[PlayerOut]:
        return [PlayerOut.from_player(p) for p in interactor.ranking()]

    @app.get("/players/{player_id}", response_model=PlayerOut)
    def get_player(player_id: int) -> PlayerOut:
        return PlayerOut.from_player(interactor.get(player_id))

    # ---- Update ----
    @app.post("/players/{player_id}/login", response_model=LoginOut)
    def login(player_id: int) -> LoginOut:
        player, reward = interactor.login(player_id)
        return LoginOut(
            player=PlayerOut.from_player(player),
            reward=IdleRewardOut(
                elapsed_seconds=reward.elapsed_seconds,
                gained_exp=reward.gained_exp,
                gained_gold=reward.gained_gold,
                levelups=reward.levelups,
            ),
        )

    @app.post("/players/{player_id}/adventure", response_model=AdventureOut)
    def adventure(player_id: int) -> AdventureOut:
        player, result = interactor.adventure(player_id)
        return AdventureOut(
            player=PlayerOut.from_player(player),
            result=AdventureResultOut(
                gained_exp=result.gained_exp,
                gained_gold=result.gained_gold,
                levelups=result.levelups,
            ),
        )

    @app.patch("/players/{player_id}", response_model=PlayerOut)
    def rename(player_id: int, body: RenameIn) -> PlayerOut:
        return PlayerOut.from_player(interactor.rename(player_id, body.name))

    # ---- Delete ----
    @app.delete("/players/{player_id}", status_code=204)
    def retire(player_id: int) -> Response:
        interactor.retire(player_id)
        return Response(status_code=204)

    return app
