"""Tests del adaptador API-Football con HTTP mockeado (respx)."""

from datetime import date
from typing import Any

import httpx
import pytest
import respx

from wcpredictor.domain.entities.match import MatchStatus
from wcpredictor.domain.entities.player import Position
from wcpredictor.infrastructure.fixtures.api_football import (
    ApiFootballFixtureRepository,
    _RetryableStatusError,
    parse_position,
    parse_status,
)

BASE = "https://v3.football.api-sports.io"


def _fixtures_payload() -> dict[str, Any]:
    return {
        "response": [
            {
                "fixture": {
                    "id": 1489380,
                    "date": "2026-06-15T18:00:00+00:00",
                    "referee": None,
                    "status": {"short": "NS"},
                },
                "teams": {
                    "home": {"id": 9, "name": "Spain"},
                    "away": {"id": 6385, "name": "Cape Verde Islands"},
                },
                "league": {"id": 1, "name": "World Cup", "season": 2026},
            },
            {
                "fixture": {
                    "id": 999,
                    "date": "2026-06-15T20:00:00+00:00",
                    "referee": "Some Ref",
                    "status": {"short": "FT"},
                },
                "teams": {
                    "home": {"id": 50, "name": "Other"},
                    "away": {"id": 51, "name": "Team"},
                },
                "league": {"id": 256, "name": "USL League Two", "season": 2026},
            },
        ]
    }


def _lineups_payload() -> dict[str, Any]:
    return {
        "response": [
            {
                "team": {"id": 9, "name": "Spain"},
                "formation": "4-3-3",
                "startXI": [
                    {"player": {"id": 1, "name": "GK", "pos": "G"}},
                    {"player": {"id": 2, "name": "Def", "pos": "D"}},
                    {"player": {"id": 3, "name": "Fwd", "pos": "F"}},
                ],
            }
        ]
    }


def _repo() -> ApiFootballFixtureRepository:
    return ApiFootballFixtureRepository(api_key="k", base_url=BASE, backoff_base=0.0)


@respx.mock
async def test_get_fixtures_filters_by_league() -> None:
    respx.get(f"{BASE}/fixtures").mock(return_value=httpx.Response(200, json=_fixtures_payload()))
    matches = await _repo().get_fixtures_for_date(date(2026, 6, 15), league_id=1)
    assert len(matches) == 1
    m = matches[0]
    assert m.home.name == "Spain"
    assert m.away.name == "Cape Verde Islands"
    assert m.referee is None
    assert m.status is MatchStatus.SCHEDULED


@respx.mock
async def test_get_lineup_confirmed() -> None:
    respx.get(f"{BASE}/fixtures/lineups").mock(
        return_value=httpx.Response(200, json=_lineups_payload())
    )
    info = await _repo().get_lineup_availability(1489380)
    assert info.confirmed is True
    assert len(info.players) == 3
    assert info.players[0].position is Position.GK
    assert all(p.team_id == 9 for p in info.players)


@respx.mock
async def test_get_lineup_not_confirmed_when_empty() -> None:
    respx.get(f"{BASE}/fixtures/lineups").mock(
        return_value=httpx.Response(200, json={"response": []})
    )
    info = await _repo().get_lineup_availability(1)
    assert info.confirmed is False
    assert info.players == ()


@respx.mock
async def test_retries_on_server_error_then_succeeds() -> None:
    route = respx.get(f"{BASE}/fixtures").mock(
        side_effect=[
            httpx.Response(500),
            httpx.Response(200, json=_fixtures_payload()),
        ]
    )
    matches = await _repo().get_fixtures_for_date(date(2026, 6, 15), league_id=1)
    assert route.call_count == 2
    assert len(matches) == 1


@respx.mock
async def test_gives_up_after_max_retries() -> None:
    respx.get(f"{BASE}/fixtures").mock(return_value=httpx.Response(503))
    repo = ApiFootballFixtureRepository(api_key="k", base_url=BASE, max_retries=2, backoff_base=0.0)
    with pytest.raises(_RetryableStatusError):
        await repo.get_fixtures_for_date(date(2026, 6, 15), league_id=1)


def test_parse_status() -> None:
    assert parse_status("NS") is MatchStatus.SCHEDULED
    assert parse_status("FT") is MatchStatus.FINISHED
    assert parse_status("1H") is MatchStatus.SCHEDULED


def test_parse_position() -> None:
    assert parse_position("G") is Position.GK
    assert parse_position("D") is Position.DEF
    assert parse_position("M") is Position.MID
    assert parse_position("F") is Position.FWD
    assert parse_position(None) is Position.MID
