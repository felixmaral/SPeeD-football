"""Tests de los puertos (interfaces ABC y value objects)."""

import pytest

from wcpredictor.application.ports.fixture_repo import FixtureRepository, LineupInfo
from wcpredictor.application.ports.ratings_repo import RatingsRepository, TeamRating
from wcpredictor.domain.entities.player import Player, Position


def test_fixture_repository_is_abstract() -> None:
    with pytest.raises(TypeError):
        FixtureRepository()  # type: ignore[abstract]


def test_ratings_repository_is_abstract() -> None:
    with pytest.raises(TypeError):
        RatingsRepository()  # type: ignore[abstract]


def test_incomplete_fixture_subclass_cannot_instantiate() -> None:
    class Partial(FixtureRepository):
        async def get_fixtures_for_date(self, day, league_id):  # type: ignore[no-untyped-def]
            return []

        # falta get_lineup_availability

    with pytest.raises(TypeError):
        Partial()  # type: ignore[abstract]


def test_lineup_info_available_players() -> None:
    p1 = Player(id=1, name="A", team_id=1, position=Position.FWD, available=True)
    p2 = Player(id=2, name="B", team_id=1, position=Position.DEF, available=False)
    info = LineupInfo(confirmed=True, players=(p1, p2))
    assert info.confirmed is True
    assert info.available_players() == (p1,)


def test_team_rating_value_object() -> None:
    r = TeamRating(team="Spain", attack=1.4, defense=0.8)
    assert (r.team, r.attack, r.defense) == ("Spain", 1.4, 0.8)
