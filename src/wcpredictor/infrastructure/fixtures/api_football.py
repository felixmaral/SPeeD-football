"""Adaptador de fixtures contra API-Football (api-sports.io).

Implementa `FixtureRepository` con httpx async, reintentos con backoff y mapeo de
la respuesta real de la API a las entidades del dominio. La estructura de la
respuesta fue validada contra la API real (ver memoria del proyecto).
"""

from __future__ import annotations

import asyncio
from datetime import date
from typing import Any

import httpx

from wcpredictor.application.ports.fixture_repo import FixtureRepository, LineupInfo
from wcpredictor.domain.entities.match import Match, MatchStatus
from wcpredictor.domain.entities.player import Player, Position
from wcpredictor.domain.entities.referee import Referee
from wcpredictor.domain.entities.team import Team

_FINISHED = frozenset({"FT", "AET", "PEN"})
_POSITION_MAP = {"G": Position.GK, "D": Position.DEF, "M": Position.MID, "F": Position.FWD}


def parse_status(short: str) -> MatchStatus:
    """Mapea el estado corto de API-Football al estado del dominio."""
    if short in _FINISHED:
        return MatchStatus.FINISHED
    return MatchStatus.SCHEDULED


def parse_position(code: str | None) -> Position:
    """Mapea el código de posición (G/D/M/F) al enum del dominio (MID por defecto)."""
    return _POSITION_MAP.get((code or "").upper(), Position.MID)


def fixture_to_match(item: dict[str, Any]) -> Match:
    """Convierte un objeto fixture de API-Football en un `Match` del dominio.

    Los equipos se crean con fuerzas neutras (1.0); los ratings reales los aplica
    el caso de uso a partir del `RatingsRepository`.
    """
    fx = item["fixture"]
    teams = item["teams"]
    ref_name = fx.get("referee")
    referee = Referee(id=fx["id"], name=ref_name) if ref_name else None

    return Match(
        id=fx["id"],
        home=Team(id=teams["home"]["id"], name=teams["home"]["name"]),
        away=Team(id=teams["away"]["id"], name=teams["away"]["name"]),
        kickoff=_parse_datetime(fx["date"]),
        league_id=item["league"]["id"],
        referee=referee,
        status=parse_status(fx["status"]["short"]),
    )


def lineups_to_info(response: list[dict[str, Any]]) -> LineupInfo:
    """Convierte la respuesta de /fixtures/lineups en `LineupInfo`."""
    players: list[Player] = []
    for team in response:
        team_id = team["team"]["id"]
        for entry in team.get("startXI", []):
            p = entry["player"]
            players.append(
                Player(
                    id=p["id"],
                    name=p["name"],
                    team_id=team_id,
                    position=parse_position(p.get("pos")),
                    available=True,
                )
            )
    confirmed = len(players) > 0
    return LineupInfo(confirmed=confirmed, players=tuple(players))


def _parse_datetime(value: str) -> Any:
    from datetime import datetime

    return datetime.fromisoformat(value)


class ApiFootballFixtureRepository(FixtureRepository):
    """Repositorio de fixtures sobre API-Football."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://v3.football.api-sports.io",
        *,
        timeout: float = 30.0,
        max_retries: int = 3,
        backoff_base: float = 0.5,
        verify: bool | str = True,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._headers = {"x-apisports-key": api_key}
        self._timeout = timeout
        self._max_retries = max_retries
        self._backoff_base = backoff_base
        self._verify = verify
        self._client = client

    async def get_fixtures_for_date(self, day: date, league_id: int) -> list[Match]:
        data = await self._get("/fixtures", {"date": day.isoformat()})
        return [
            fixture_to_match(item)
            for item in data.get("response", [])
            if item["league"]["id"] == league_id
        ]

    async def get_lineup_availability(self, fixture_id: int) -> LineupInfo:
        data = await self._get("/fixtures/lineups", {"fixture": fixture_id})
        return lineups_to_info(data.get("response", []))

    async def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        """GET con reintentos y backoff exponencial ante 429/5xx/errores de red."""
        last_exc: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                payload = await self._request(path, params)
                return payload
            except (httpx.HTTPError, _RetryableStatusError) as exc:
                last_exc = exc
                if attempt == self._max_retries - 1:
                    break
                await asyncio.sleep(self._backoff_base * (2**attempt))
        assert last_exc is not None
        raise last_exc

    async def _request(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        if self._client is not None:
            response = await self._client.get(
                f"{self._base_url}{path}", params=params, headers=self._headers
            )
        else:
            async with httpx.AsyncClient(timeout=self._timeout, verify=self._verify) as client:
                response = await client.get(
                    f"{self._base_url}{path}", params=params, headers=self._headers
                )
        if response.status_code == 429 or response.status_code >= 500:
            raise _RetryableStatusError(response.status_code)
        response.raise_for_status()
        result: dict[str, Any] = response.json()
        return result


class _RetryableStatusError(Exception):
    """Estado HTTP transitorio que justifica un reintento."""

    def __init__(self, status_code: int) -> None:
        super().__init__(f"estado transitorio: {status_code}")
        self.status_code = status_code
