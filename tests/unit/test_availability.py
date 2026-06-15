"""Tests del ajuste por disponibilidad."""

import pytest

from wcpredictor.domain.entities.player import Player, Position
from wcpredictor.domain.entities.team import Team
from wcpredictor.domain.services.availability import AvailabilityAdjuster


def _team() -> Team:
    return Team(id=1, name="Spain", attack=1.5, defense=0.8)


def _player(pos: Position, importance: float, available: bool, pid: int = 1) -> Player:
    return Player(
        id=pid, name=f"P{pid}", team_id=1, position=pos, importance=importance, available=available
    )


def test_no_absences_keeps_strength() -> None:
    adj = AvailabilityAdjuster()
    team = _team()
    players = [_player(Position.FWD, 0.9, available=True)]
    result = adj.adjust(team, players)
    assert result.attack == pytest.approx(team.attack)
    assert result.defense == pytest.approx(team.defense)


def test_offensive_absence_reduces_attack() -> None:
    adj = AvailabilityAdjuster()
    team = _team()
    result = adj.adjust(team, [_player(Position.FWD, 0.3, available=False)])
    assert result.attack < team.attack
    assert result.defense == pytest.approx(team.defense)
    assert result.attack == pytest.approx(1.5 * 0.7)


def test_defensive_absence_worsens_defense() -> None:
    adj = AvailabilityAdjuster()
    team = _team()
    result = adj.adjust(team, [_player(Position.DEF, 0.4, available=False)])
    assert result.defense > team.defense
    assert result.attack == pytest.approx(team.attack)
    assert result.defense == pytest.approx(0.8 * 1.4)


def test_attack_floor_applies() -> None:
    adj = AvailabilityAdjuster(floor=0.5)
    team = _team()
    absent = [
        _player(Position.FWD, 1.0, available=False, pid=1),
        _player(Position.MID, 1.0, available=False, pid=2),
    ]
    result = adj.adjust(team, absent)
    assert result.attack == pytest.approx(1.5 * 0.5)


def test_defense_ceiling_applies() -> None:
    adj = AvailabilityAdjuster(ceil=2.0)
    team = _team()
    absent = [
        _player(Position.GK, 1.0, available=False, pid=1),
        _player(Position.DEF, 1.0, available=False, pid=2),
    ]
    result = adj.adjust(team, absent)
    assert result.defense == pytest.approx(0.8 * 2.0)


def test_ignores_other_team_players() -> None:
    adj = AvailabilityAdjuster()
    team = _team()
    other = Player(
        id=9, name="X", team_id=2, position=Position.FWD, importance=1.0, available=False
    )
    result = adj.adjust(team, [other])
    assert result.attack == pytest.approx(team.attack)


def test_original_team_not_mutated() -> None:
    adj = AvailabilityAdjuster()
    team = _team()
    adj.adjust(team, [_player(Position.FWD, 0.5, available=False)])
    assert team.attack == 1.5


@pytest.mark.parametrize(
    "kwargs",
    [{"sensitivity": -1.0}, {"floor": 0.0}, {"floor": 1.5}, {"ceil": 0.5}],
)
def test_invalid_params(kwargs: dict[str, float]) -> None:
    with pytest.raises(ValueError):
        AvailabilityAdjuster(**kwargs)
