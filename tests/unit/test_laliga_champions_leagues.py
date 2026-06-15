"""Tests de los plugins de LaLiga y Champions League."""

import pytest

from wcpredictor.infrastructure.leagues.base import LeagueRegistry
from wcpredictor.infrastructure.leagues.champions_league import (
    CHAMPIONS_LEAGUE_ID,
    ChampionsLeague,
)
from wcpredictor.infrastructure.leagues.la_liga import LA_LIGA_LEAGUE_ID, LaLigaLeague


def test_laliga_metadata() -> None:
    lg = LaLigaLeague()
    assert lg.league_id == LA_LIGA_LEAGUE_ID == 140
    assert lg.name == "La Liga"
    assert lg.ratings_namespace() == "la_liga"


def test_laliga_has_no_knockout() -> None:
    lg = LaLigaLeague()
    assert lg.is_knockout("Regular Season - 5") is False
    assert lg.is_knockout("Final") is False  # liga doméstica


def test_champions_metadata() -> None:
    lg = ChampionsLeague()
    assert lg.league_id == CHAMPIONS_LEAGUE_ID == 2
    assert lg.name == "UEFA Champions League"
    assert lg.ratings_namespace() == "champions_league"


@pytest.mark.parametrize(
    "stage", ["Round of 16", "Quarter-finals", "Semi-finals", "Final", "Knockout Round Play-offs"]
)
def test_champions_knockout_stages(stage: str) -> None:
    assert ChampionsLeague().is_knockout(stage) is True


@pytest.mark.parametrize("stage", ["League Phase", "Group Stage - 1", "Group A"])
def test_champions_group_not_knockout(stage: str) -> None:
    assert ChampionsLeague().is_knockout(stage) is False


def test_registry_holds_both() -> None:
    reg = LeagueRegistry()
    laliga, champions = LaLigaLeague(), ChampionsLeague()
    reg.register(laliga)
    reg.register(champions)
    assert reg.get(140) is laliga
    assert reg.get_by_name("UEFA Champions League") is champions
    assert len(reg.all()) == 2
