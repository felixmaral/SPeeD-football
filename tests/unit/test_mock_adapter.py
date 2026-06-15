"""Tests del adaptador mock de fixtures."""

from datetime import UTC, date, datetime

from wcpredictor.application.ports.fixture_repo import LineupInfo
from wcpredictor.domain.entities.match import Match
from wcpredictor.domain.entities.team import Team
from wcpredictor.infrastructure.fixtures.mock import MockFixtureRepository
from wcpredictor.infrastructure.leagues.world_cup import WORLD_CUP_LEAGUE_ID


async def test_default_fixtures_for_today() -> None:
    repo = MockFixtureRepository()
    matches = await repo.get_fixtures_for_date(date(2026, 6, 15), WORLD_CUP_LEAGUE_ID)
    assert len(matches) == 3
    assert matches[0].home.name == "Spain"
    assert all(m.kickoff.date() == date(2026, 6, 15) for m in matches)


async def test_default_filters_by_league() -> None:
    repo = MockFixtureRepository()
    assert await repo.get_fixtures_for_date(date(2026, 6, 15), league_id=999) == []


async def test_default_lineup_confirmed() -> None:
    repo = MockFixtureRepository()
    info = await repo.get_lineup_availability(1)
    assert info.confirmed is True
    assert len(info.players) == 3


async def test_injected_fixtures_and_lineups() -> None:
    day = date(2026, 7, 1)
    match = Match(
        id=42,
        home=Team(id=1, name="A"),
        away=Team(id=2, name="B"),
        kickoff=datetime(2026, 7, 1, 20, tzinfo=UTC),
        league_id=WORLD_CUP_LEAGUE_ID,
    )
    repo = MockFixtureRepository(
        fixtures={day: [match]},
        lineups={42: LineupInfo(confirmed=True)},
    )
    matches = await repo.get_fixtures_for_date(day, WORLD_CUP_LEAGUE_ID)
    assert matches == [match]
    assert (await repo.get_lineup_availability(42)).confirmed is True
    # Sin lineup inyectado y con fixtures inyectados -> preliminar.
    assert (await repo.get_lineup_availability(7)).confirmed is False


async def test_injected_empty_day() -> None:
    repo = MockFixtureRepository(fixtures={})
    assert await repo.get_fixtures_for_date(date(2026, 1, 1), WORLD_CUP_LEAGUE_ID) == []
