"""Tests del plugin de liga WorldCup."""

import pytest

from wcpredictor.infrastructure.leagues.base import LeagueRegistry
from wcpredictor.infrastructure.leagues.world_cup import (
    WORLD_CUP_LEAGUE_ID,
    WorldCupLeague,
)


def test_basic_metadata() -> None:
    wc = WorldCupLeague()
    assert wc.league_id == WORLD_CUP_LEAGUE_ID == 1
    assert wc.name == "World Cup"
    assert wc.ratings_namespace() == "world_cup"


@pytest.mark.parametrize(
    "stage",
    ["Round of 16", "Quarter-finals", "Semi-finals", "Final", "3rd Place Final"],
)
def test_knockout_stages(stage: str) -> None:
    assert WorldCupLeague().is_knockout(stage) is True


@pytest.mark.parametrize("stage", ["Group Stage", "Group Stage - 1", "Group A"])
def test_group_stages_not_knockout(stage: str) -> None:
    assert WorldCupLeague().is_knockout(stage) is False


def test_registrable_in_registry() -> None:
    reg = LeagueRegistry()
    wc = WorldCupLeague()
    reg.register(wc)
    assert reg.get(1) is wc
    assert reg.get_by_name("World Cup") is wc
