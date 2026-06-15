"""Tests del adaptador de resultados recientes / H2H (respx)."""

from datetime import date
from typing import Any

import httpx
import respx

from wcpredictor.application.ports.recent_results_repo import TeamMatchResult
from wcpredictor.infrastructure.fixtures.recent_results import (
    ApiFootballRecentResultsRepository,
    MockRecentResultsRepository,
)

BASE = "https://v3.football.api-sports.io"


def _fixture(
    date_str: str,
    hid: int,
    hn: str,
    aid: int,
    an: str,
    hg: int | None,
    ag: int | None,
    short: str,
) -> dict[str, Any]:
    return {
        "fixture": {"date": date_str, "status": {"short": short}},
        "teams": {"home": {"id": hid, "name": hn}, "away": {"id": aid, "name": an}},
        "goals": {"home": hg, "away": ag},
    }


def _repo() -> ApiFootballRecentResultsRepository:
    return ApiFootballRecentResultsRepository(api_key="k", base_url=BASE, backoff_base=0.0)


@respx.mock
async def test_recent_results_team_perspective_and_order() -> None:
    payload = {
        "response": [
            _fixture("2026-06-01T18:00:00+00:00", 9, "Spain", 5, "Italy", 2, 1, "FT"),
            _fixture("2026-06-10T18:00:00+00:00", 4, "Brazil", 9, "Spain", 0, 3, "FT"),
            _fixture("2026-06-12T18:00:00+00:00", 9, "Spain", 7, "France", None, None, "NS"),
        ]
    }
    respx.get(f"{BASE}/fixtures").mock(return_value=httpx.Response(200, json=payload))
    res = await _repo().get_recent_results(team_id=9, season=2024, league_id=1)

    assert [r.when for r in res] == [date(2026, 6, 10), date(2026, 6, 1)]  # desc, sin el NS
    # Más reciente: Spain visitante ganó 3-0 a Brazil.
    assert res[0].goals_for == 3 and res[0].goals_against == 0
    assert res[0].opponent_name == "Brazil"
    # Como local: 2-1 a Italy.
    assert res[1].goals_for == 2 and res[1].opponent_name == "Italy"


@respx.mock
async def test_head_to_head_from_home_perspective() -> None:
    payload = {
        "response": [
            _fixture("2024-03-26T20:00:00+00:00", 9, "Spain", 6, "Brazil", 3, 3, "FT"),
            _fixture("2013-06-30T20:00:00+00:00", 6, "Brazil", 9, "Spain", 3, 0, "FT"),
        ]
    }
    respx.get(f"{BASE}/fixtures/headtohead").mock(return_value=httpx.Response(200, json=payload))
    res = await _repo().get_head_to_head(home_id=9, away_id=6)
    assert res[0].when == date(2024, 3, 26)
    assert res[0].goals_for == 3 and res[0].goals_against == 3
    # El 2013 Spain fue visitante y perdió 0-3.
    assert res[1].goals_for == 0 and res[1].goals_against == 3


@respx.mock
async def test_retry_then_success() -> None:
    payload: dict[str, Any] = {"response": []}
    route = respx.get(f"{BASE}/fixtures").mock(
        side_effect=[httpx.Response(500), httpx.Response(200, json=payload)]
    )
    res = await _repo().get_recent_results(team_id=9, season=2024)
    assert route.call_count == 2
    assert res == []


async def test_mock_repository() -> None:
    recent = {9: [TeamMatchResult(date(2026, 6, 1), 2, 0, "Italy")]}
    h2h = {(9, 6): [TeamMatchResult(date(2024, 3, 26), 3, 3, "Brazil")]}
    repo = MockRecentResultsRepository(recent=recent, h2h=h2h)
    assert (await repo.get_recent_results(9, 2024))[0].opponent_name == "Italy"
    assert (await repo.get_head_to_head(9, 6))[0].goals_for == 3
    assert await repo.get_recent_results(1, 2024) == []
