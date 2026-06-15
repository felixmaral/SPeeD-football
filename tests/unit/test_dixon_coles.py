"""Tests del modelo Dixon-Coles."""

import numpy as np
import pytest

from wcpredictor.domain.entities.team import Team
from wcpredictor.domain.models.dixon_coles import DixonColesModel


def _even_teams() -> tuple[Team, Team]:
    home = Team(id=1, name="A", attack=1.0, defense=1.0)
    away = Team(id=2, name="B", attack=1.0, defense=1.0)
    return home, away


def test_score_matrix_normalized() -> None:
    model = DixonColesModel()
    home, away = _even_teams()
    probs = model.predict(home, away)
    assert probs.score_matrix.sum() == pytest.approx(1.0, abs=1e-9)
    assert np.all(probs.score_matrix >= 0.0)


def test_outcomes_sum_to_one() -> None:
    model = DixonColesModel()
    home, away = _even_teams()
    p = model.predict(home, away)
    assert p.home_win + p.draw + p.away_win == pytest.approx(1.0, abs=1e-9)


def test_home_advantage_increases_home_win() -> None:
    home, away = _even_teams()
    with_adv = DixonColesModel(home_advantage=1.4).predict(home, away)
    no_adv = DixonColesModel(home_advantage=1.0).predict(home, away)
    assert with_adv.home_win > no_adv.home_win
    assert with_adv.lambda_home > no_adv.lambda_home


def test_symmetry_without_home_advantage() -> None:
    """Sin ventaja de campo y equipos idénticos, P(local) == P(visitante)."""
    model = DixonColesModel(home_advantage=1.0)
    home, away = _even_teams()
    p = model.predict(home, away)
    assert p.home_win == pytest.approx(p.away_win, abs=1e-9)


def test_stronger_attack_raises_expected_goals() -> None:
    model = DixonColesModel(home_advantage=1.0)
    weak = Team(id=1, name="W", attack=1.0, defense=1.0)
    strong = Team(id=2, name="S", attack=2.0, defense=1.0)
    lam_strong, _ = model.expected_goals(strong, weak)
    lam_weak, _ = model.expected_goals(weak, weak)
    assert lam_strong > lam_weak


def test_over_under_complementary() -> None:
    model = DixonColesModel()
    home, away = _even_teams()
    p = model.predict(home, away)
    assert p.over(2.5) + p.under(2.5) == pytest.approx(1.0, abs=1e-9)
    assert 0.0 <= p.over(2.5) <= 1.0


def test_most_likely_score_returns_pair() -> None:
    model = DixonColesModel()
    home, away = _even_teams()
    i, j = model.predict(home, away).most_likely_score
    assert isinstance(i, int)
    assert isinstance(j, int)


@pytest.mark.parametrize(
    "kwargs",
    [{"home_advantage": 0}, {"base_rate": -1}, {"max_goals": 0}],
)
def test_invalid_params(kwargs: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        DixonColesModel(**kwargs)  # type: ignore[arg-type]
