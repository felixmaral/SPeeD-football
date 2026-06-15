"""Tests del ajuste por forma reciente."""

from datetime import date

import pytest

from wcpredictor.domain.entities.team import Team
from wcpredictor.domain.services.form import FormAdjuster, RecentResult

_AS_OF = date(2026, 6, 15)


def _team() -> Team:
    return Team(id=1, name="X", attack=1.0, defense=1.0)


def _avg_opponent(when: date, gf: int, ga: int) -> RecentResult:
    return RecentResult(
        when=when, goals_for=gf, goals_against=ga, opponent_attack=1.0, opponent_defense=1.0
    )


def test_no_results_keeps_team() -> None:
    team = _team()
    assert FormAdjuster().adjust(team, [], _AS_OF) == team


def test_good_form_raises_attack_and_improves_defense() -> None:
    team = _team()
    results = [_avg_opponent(date(2026, 6, 1), gf=4, ga=0) for _ in range(3)]
    adj = FormAdjuster().adjust(team, results, _AS_OF)
    assert adj.attack > team.attack
    assert adj.defense < team.defense  # encaja menos de lo esperado -> mejor defensa


def test_bad_form_lowers_attack_and_worsens_defense() -> None:
    team = _team()
    results = [_avg_opponent(date(2026, 6, 1), gf=0, ga=3) for _ in range(3)]
    adj = FormAdjuster().adjust(team, results, _AS_OF)
    assert adj.attack < team.attack
    assert adj.defense > team.defense


def test_recency_weights_more() -> None:
    team = _team()
    recent_good = [_avg_opponent(date(2026, 6, 14), gf=5, ga=0)]
    old_good = [_avg_opponent(date(2024, 1, 1), gf=5, ga=0)]
    recent = FormAdjuster().adjust(team, recent_good, _AS_OF)
    old = FormAdjuster().adjust(team, old_good, _AS_OF)
    assert recent.attack > old.attack  # el mismo resultado reciente pesa más


def test_opponent_quality_matters() -> None:
    team = _team()
    # Mismo 2-0, pero uno contra rival con gran defensa (def baja) -> más mérito.
    vs_strong = [RecentResult(date(2026, 6, 10), 2, 0, opponent_attack=1.0, opponent_defense=0.5)]
    vs_weak = [RecentResult(date(2026, 6, 10), 2, 0, opponent_attack=1.0, opponent_defense=1.6)]
    strong = FormAdjuster().adjust(team, vs_strong, _AS_OF)
    weak = FormAdjuster().adjust(team, vs_weak, _AS_OF)
    assert strong.attack > weak.attack


def test_clip_bounds_applied() -> None:
    team = _team()
    crush = [_avg_opponent(date(2026, 6, 14), gf=9, ga=0) for _ in range(5)]
    adj = FormAdjuster(ceil=1.5, sensitivity=1.0).adjust(team, crush, _AS_OF)
    assert adj.attack <= team.attack * 1.5 + 1e-9


def test_original_not_mutated() -> None:
    team = _team()
    FormAdjuster().adjust(team, [_avg_opponent(date(2026, 6, 1), 3, 0)], _AS_OF)
    assert team.attack == 1.0 and team.defense == 1.0


@pytest.mark.parametrize(
    "kwargs",
    [{"base_rate": 0}, {"half_life_days": 0}, {"sensitivity": -1}, {"floor": 0}, {"ceil": 0.9}],
)
def test_invalid_params(kwargs: dict[str, float]) -> None:
    with pytest.raises(ValueError):
        FormAdjuster(**kwargs)


def test_invalid_recent_result() -> None:
    with pytest.raises(ValueError):
        RecentResult(_AS_OF, -1, 0, 1.0, 1.0)
    with pytest.raises(ValueError):
        RecentResult(_AS_OF, 1, 0, 0.0, 1.0)
