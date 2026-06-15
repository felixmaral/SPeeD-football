"""Tests de las entidades del dominio."""

from datetime import UTC, datetime

import pytest

from wcpredictor.domain.entities import (
    Match,
    MatchStatus,
    Player,
    Position,
    Referee,
    Team,
)


def _team(team_id: int = 1, name: str = "Spain") -> Team:
    return Team(id=team_id, name=name, attack=1.3, defense=0.8)


# --- Team ---------------------------------------------------------------


def test_team_valid() -> None:
    t = _team()
    assert t.attack == 1.3
    assert t.defense == 0.8


def test_team_is_immutable() -> None:
    t = _team()
    with pytest.raises(AttributeError):
        t.attack = 2.0  # type: ignore[misc]


@pytest.mark.parametrize(
    ("kwargs", "msg"),
    [
        ({"name": "  "}, "name"),
        ({"attack": 0.0}, "attack"),
        ({"defense": -1.0}, "defense"),
    ],
)
def test_team_validation(kwargs: dict[str, object], msg: str) -> None:
    base: dict[str, object] = {"id": 1, "name": "Spain", "attack": 1.0, "defense": 1.0}
    base.update(kwargs)
    with pytest.raises(ValueError, match=msg):
        Team(**base)  # type: ignore[arg-type]


# --- Player -------------------------------------------------------------


def test_player_defaults() -> None:
    p = Player(id=10, name="Pedri", team_id=1, position=Position.MID)
    assert p.available is True
    assert p.importance == 0.0
    assert p.position is Position.MID


@pytest.mark.parametrize("field", ["importance", "card_risk"])
def test_player_range_validation(field: str) -> None:
    kwargs: dict[str, object] = {
        "id": 1,
        "name": "X",
        "team_id": 1,
        "position": Position.FWD,
        field: 1.5,
    }
    with pytest.raises(ValueError, match=field):
        Player(**kwargs)  # type: ignore[arg-type]


# --- Referee ------------------------------------------------------------


def test_referee_valid() -> None:
    r = Referee(id=1, name="Collina", strictness=1.2)
    assert r.strictness == 1.2


def test_referee_invalid_strictness() -> None:
    with pytest.raises(ValueError, match="strictness"):
        Referee(id=1, name="X", strictness=0)


# --- Match --------------------------------------------------------------


def test_match_valid_and_lineup_flag() -> None:
    kickoff = datetime(2026, 6, 15, 18, 0, tzinfo=UTC)
    m = Match(
        id=99,
        home=_team(1, "Spain"),
        away=_team(2, "Brazil"),
        kickoff=kickoff,
        league_id=1,
    )
    assert m.status is MatchStatus.SCHEDULED
    assert m.has_confirmed_lineup is False
    assert m.referee is None


def test_match_confirmed_lineup() -> None:
    m = Match(
        id=1,
        home=_team(1, "A"),
        away=_team(2, "B"),
        kickoff=datetime(2026, 6, 15, tzinfo=UTC),
        league_id=1,
        referee=Referee(id=5, name="Ref"),
        status=MatchStatus.LINEUP_CONFIRMED,
    )
    assert m.has_confirmed_lineup is True


def test_match_same_team_rejected() -> None:
    t = _team(1, "Spain")
    with pytest.raises(ValueError, match="mismo equipo"):
        Match(
            id=1,
            home=t,
            away=Team(id=1, name="Spain dup"),
            kickoff=datetime(2026, 6, 15, tzinfo=UTC),
            league_id=1,
        )
