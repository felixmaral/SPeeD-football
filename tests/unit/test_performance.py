"""Tests del modelo de rendimiento."""

import pytest

from wcpredictor.domain.entities.team import Team
from wcpredictor.domain.models.performance import PerformanceModel


def _even() -> tuple[Team, Team]:
    return (
        Team(id=1, name="A", attack=1.0, defense=1.0),
        Team(id=2, name="B", attack=1.0, defense=1.0),
    )


def test_possession_sums_to_100() -> None:
    home, away = _even()
    perf = PerformanceModel().predict(home, away)
    assert perf.home.possession + perf.away.possession == pytest.approx(100.0)


def test_home_advantage_gives_more_possession_and_xg() -> None:
    home, away = _even()
    perf = PerformanceModel(home_advantage=1.3).predict(home, away)
    assert perf.home.possession > perf.away.possession
    assert perf.home.xg > perf.away.xg


def test_symmetry_without_home_advantage() -> None:
    home, away = _even()
    perf = PerformanceModel(home_advantage=1.0).predict(home, away)
    assert perf.home.possession == pytest.approx(50.0)
    assert perf.home.xg == pytest.approx(perf.away.xg)


def test_stronger_attack_increases_xg() -> None:
    model = PerformanceModel(home_advantage=1.0)
    strong = Team(id=1, name="S", attack=2.0, defense=1.0)
    weak = Team(id=2, name="W", attack=1.0, defense=1.0)
    perf = model.predict(strong, weak)
    assert perf.home.xg > perf.away.xg


def test_box_touches_proportional_to_xg() -> None:
    home, away = _even()
    model = PerformanceModel(touches_per_xg=20.0)
    perf = model.predict(home, away)
    assert perf.home.box_touches == pytest.approx(perf.home.xg * 20.0)


@pytest.mark.parametrize(
    "kwargs",
    [{"base_xg": 0}, {"home_advantage": -1}, {"touches_per_xg": 0}],
)
def test_invalid_params(kwargs: dict[str, float]) -> None:
    with pytest.raises(ValueError):
        PerformanceModel(**kwargs)
