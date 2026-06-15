"""Adaptadores de resultados recientes / head-to-head.

`ApiFootballRecentResultsRepository` consulta API-Football; `MockRecentResultsRepository`
sirve datos en memoria para desarrollo/CI.
"""

from __future__ import annotations

import asyncio
from datetime import date
from typing import Any

import httpx

from wcpredictor.application.ports.recent_results_repo import (
    RecentResultsRepository,
    TeamMatchResult,
)

_FINISHED = frozenset({"FT", "AET", "PEN"})


def _to_result(item: dict[str, Any], team_id: int) -> TeamMatchResult | None:
    """Mapea un fixture a la perspectiva de `team_id`; None si no está finalizado."""
    fx = item["fixture"]
    if fx["status"]["short"] not in _FINISHED:
        return None
    teams, goals = item["teams"], item["goals"]
    is_home = teams["home"]["id"] == team_id
    if is_home:
        gf, ga, opponent = goals["home"], goals["away"], teams["away"]["name"]
    else:
        gf, ga, opponent = goals["away"], goals["home"], teams["home"]["name"]
    if gf is None or ga is None:
        return None
    return TeamMatchResult(
        when=date.fromisoformat(fx["date"][:10]),
        goals_for=int(gf),
        goals_against=int(ga),
        opponent_name=opponent,
    )


def _sorted_desc(results: list[TeamMatchResult]) -> list[TeamMatchResult]:
    return sorted(results, key=lambda r: r.when, reverse=True)


class ApiFootballRecentResultsRepository(RecentResultsRepository):
    """Resultados recientes y H2H desde API-Football."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://v3.football.api-sports.io",
        *,
        timeout: float = 30.0,
        max_retries: int = 3,
        backoff_base: float = 0.5,
        verify: bool | str = True,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._headers = {"x-apisports-key": api_key}
        self._timeout = timeout
        self._max_retries = max_retries
        self._backoff_base = backoff_base
        self._verify = verify

    async def get_recent_results(
        self, team_id: int, season: int, league_id: int | None = None
    ) -> list[TeamMatchResult]:
        params: dict[str, Any] = {"team": team_id, "season": season}
        if league_id is not None:
            params["league"] = league_id
        data = await self._get("/fixtures", params)
        results = [r for item in data.get("response", []) if (r := _to_result(item, team_id))]
        return _sorted_desc(results)

    async def get_head_to_head(self, home_id: int, away_id: int) -> list[TeamMatchResult]:
        data = await self._get("/fixtures/headtohead", {"h2h": f"{home_id}-{away_id}"})
        results = [r for item in data.get("response", []) if (r := _to_result(item, home_id))]
        return _sorted_desc(results)

    async def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        last_exc: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                return await self._request(path, params)
            except (httpx.HTTPError, _RetryableStatusError) as exc:
                last_exc = exc
                if attempt == self._max_retries - 1:
                    break
                await asyncio.sleep(self._backoff_base * (2**attempt))
        assert last_exc is not None
        raise last_exc

    async def _request(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self._timeout, verify=self._verify) as client:
            response = await client.get(
                f"{self._base_url}{path}", params=params, headers=self._headers
            )
        if response.status_code == 429 or response.status_code >= 500:
            raise _RetryableStatusError(response.status_code)
        response.raise_for_status()
        result: dict[str, Any] = response.json()
        return result


class MockRecentResultsRepository(RecentResultsRepository):
    """Resultados recientes / H2H en memoria."""

    def __init__(
        self,
        recent: dict[int, list[TeamMatchResult]] | None = None,
        h2h: dict[tuple[int, int], list[TeamMatchResult]] | None = None,
    ) -> None:
        self._recent = recent or {}
        self._h2h = h2h or {}

    async def get_recent_results(
        self, team_id: int, season: int, league_id: int | None = None
    ) -> list[TeamMatchResult]:
        return _sorted_desc(list(self._recent.get(team_id, [])))

    async def get_head_to_head(self, home_id: int, away_id: int) -> list[TeamMatchResult]:
        return _sorted_desc(list(self._h2h.get((home_id, away_id), [])))


class _RetryableStatusError(Exception):
    """Estado HTTP transitorio que justifica un reintento."""

    def __init__(self, status_code: int) -> None:
        super().__init__(f"estado transitorio: {status_code}")
        self.status_code = status_code
