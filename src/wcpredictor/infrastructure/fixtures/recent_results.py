"""Adaptadores de resultados recientes / head-to-head.

`Martj42RecentResultsRepository` usa el dataset abierto de resultados internacionales
(gratis, sin key, actualizado a diario), identificando equipos por nombre.
`MockRecentResultsRepository` sirve datos en memoria para desarrollo/CI.
"""

from __future__ import annotations

import csv
import io
from datetime import date

import httpx

from wcpredictor.application.ports.recent_results_repo import (
    RecentResultsRepository,
    TeamMatchResult,
)
from wcpredictor.infrastructure.names import normalize_team_name

_URL = "https://raw.githubusercontent.com/martj42/international_results/master/results.csv"


def _sorted_desc(results: list[TeamMatchResult]) -> list[TeamMatchResult]:
    return sorted(results, key=lambda r: r.when, reverse=True)


class Martj42RecentResultsRepository(RecentResultsRepository):
    """Resultados recientes y H2H desde el dataset martj42 (por nombre)."""

    def __init__(
        self,
        url: str = _URL,
        *,
        timeout: float = 120.0,
        verify: bool | str = True,
        csv_text: str | None = None,
    ) -> None:
        self._url = url
        self._timeout = timeout
        self._verify = verify
        self._rows: list[dict[str, str]] | None = None
        if csv_text is not None:
            self._rows = self._parse(csv_text)

    async def get_recent_results(self, team_name: str, limit: int = 10) -> list[TeamMatchResult]:
        key = normalize_team_name(team_name)
        rows = await self._load()
        out = [
            r
            for row in rows
            if key in (normalize_team_name(row["home_team"]), normalize_team_name(row["away_team"]))
            and (r := _row_to_result(row, key)) is not None
        ]
        return _sorted_desc(out)[:limit]

    async def get_head_to_head(
        self, home_name: str, away_name: str, limit: int = 5
    ) -> list[TeamMatchResult]:
        home_key, away_key = normalize_team_name(home_name), normalize_team_name(away_name)
        rows = await self._load()
        out = [
            r
            for row in rows
            if {normalize_team_name(row["home_team"]), normalize_team_name(row["away_team"])}
            == {home_key, away_key}
            and (r := _row_to_result(row, home_key)) is not None
        ]
        return _sorted_desc(out)[:limit]

    async def _load(self) -> list[dict[str, str]]:
        if self._rows is None:
            async with httpx.AsyncClient(timeout=self._timeout, verify=self._verify) as client:
                resp = await client.get(self._url)
            resp.raise_for_status()
            self._rows = self._parse(resp.text)
        return self._rows

    @staticmethod
    def _parse(text: str) -> list[dict[str, str]]:
        return list(csv.DictReader(io.StringIO(text)))


def _row_to_result(row: dict[str, str], team_key: str) -> TeamMatchResult | None:
    """Mapea una fila del CSV a la perspectiva del equipo `team_key`."""
    hs, as_ = row["home_score"], row["away_score"]
    if not hs.isdigit() or not as_.isdigit():
        return None
    is_home = normalize_team_name(row["home_team"]) == team_key
    if is_home:
        gf, ga, opponent = int(hs), int(as_), row["away_team"]
    else:
        gf, ga, opponent = int(as_), int(hs), row["home_team"]
    return TeamMatchResult(
        when=date.fromisoformat(row["date"]),
        goals_for=gf,
        goals_against=ga,
        opponent_name=opponent,
    )


class MockRecentResultsRepository(RecentResultsRepository):
    """Resultados recientes / H2H en memoria (por nombre)."""

    def __init__(
        self,
        recent: dict[str, list[TeamMatchResult]] | None = None,
        h2h: dict[tuple[str, str], list[TeamMatchResult]] | None = None,
    ) -> None:
        self._recent = recent or {}
        self._h2h = h2h or {}

    async def get_recent_results(self, team_name: str, limit: int = 10) -> list[TeamMatchResult]:
        return _sorted_desc(list(self._recent.get(team_name, [])))[:limit]

    async def get_head_to_head(
        self, home_name: str, away_name: str, limit: int = 5
    ) -> list[TeamMatchResult]:
        return _sorted_desc(list(self._h2h.get((home_name, away_name), [])))[:limit]
