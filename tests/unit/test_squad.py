"""Tests de la fuerza por plantilla (SquadAggregator)."""

import pytest

from wcpredictor.domain.entities.player import Position
from wcpredictor.domain.entities.team import Team
from wcpredictor.domain.services.squad import PlayerRating, SquadAggregator


def _squad(rating: float, n: int = 16, available: bool = True) -> list[PlayerRating]:
    return [
        PlayerRating(name=f"P{i}", position=Position.MID, rating=rating, available=available)
        for i in range(n)
    ]


def test_average_squad_is_neutral() -> None:
    agg = SquadAggregator()
    assert agg.squad_factor(_squad(1.0)) == pytest.approx(1.0)


def test_no_players_neutral() -> None:
    assert SquadAggregator().squad_factor([]) == pytest.approx(1.0)


def test_better_squad_raises_factor() -> None:
    agg = SquadAggregator()
    assert agg.squad_factor(_squad(1.3)) > 1.0


def test_star_absence_lowers_factor() -> None:
    agg = SquadAggregator()
    base = _squad(1.0, n=16)
    stars = [
        PlayerRating(name="Star", position=Position.FWD, rating=2.0, available=True)
        for _ in range(2)
    ]
    full = agg.squad_factor(base + stars)
    without = agg.squad_factor(
        base
        + [
            PlayerRating(name="Star", position=Position.FWD, rating=2.0, available=False)
            for _ in range(2)
        ]
    )
    assert without < full


def test_bench_weight_matters() -> None:
    # XI fuerte (2.0) + banquillo flojo (1.0): a mayor peso del banquillo, más baja el factor.
    squad = [PlayerRating(f"S{i}", Position.MID, 2.0) for i in range(11)] + [
        PlayerRating(f"B{i}", Position.MID, 1.0) for i in range(5)
    ]
    low_bench = SquadAggregator(bench_weight=0.3).squad_factor(squad)
    high_bench = SquadAggregator(bench_weight=1.0).squad_factor(squad)
    assert high_bench < low_bench  # el banquillo flojo pesa más y arrastra el factor


def test_adjust_applies_factor() -> None:
    agg = SquadAggregator()
    team = Team(id=1, name="X", attack=1.2, defense=0.9)
    strong = agg.adjust(team, _squad(1.3))
    assert strong.attack > team.attack
    assert strong.defense < team.defense  # mejor plantilla = mejor defensa


def test_adjust_clip() -> None:
    agg = SquadAggregator(ceil=1.2)
    team = Team(id=1, name="X", attack=1.0, defense=1.0)
    adj = agg.adjust(team, _squad(5.0))
    assert adj.attack <= 1.0 * 1.2 + 1e-9


def test_original_not_mutated() -> None:
    team = Team(id=1, name="X", attack=1.0, defense=1.0)
    SquadAggregator().adjust(team, _squad(1.5))
    assert team.attack == 1.0 and team.defense == 1.0


@pytest.mark.parametrize(
    "kwargs",
    [
        {"starters": 0},
        {"bench": -1},
        {"bench_weight": 0},
        {"bench_weight": 1.5},
        {"sensitivity": -1},
        {"floor": 0},
        {"ceil": 0.5},
    ],
)
def test_invalid_params(kwargs: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        SquadAggregator(**kwargs)  # type: ignore[arg-type]


def test_invalid_player_rating() -> None:
    with pytest.raises(ValueError):
        PlayerRating(name=" ", position=Position.MID, rating=1.0)
    with pytest.raises(ValueError):
        PlayerRating(name="X", position=Position.MID, rating=0)
