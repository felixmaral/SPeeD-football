"""Tests del repositorio y modelo de tarjetas por equipo."""

import json
from pathlib import Path

import pytest

from wcpredictor.domain.models.team_cards import TeamCardsModel
from wcpredictor.infrastructure.cards.json_repo import JsonCardsRepository


def _write(base: Path, ns: str, data: list[dict[str, object]]) -> None:
    (base / f"{ns}.json").write_text(json.dumps(data), encoding="utf-8")


# --- repo ---------------------------------------------------------------


def test_repo_loads_and_normalizes(tmp_path: Path) -> None:
    _write(tmp_path, "la_liga", [{"team": "Getafe", "cards_per_match": 3.0, "tendency": 1.3}])
    repo = JsonCardsRepository(tmp_path)
    getafe = repo.get_team_cards("la_liga", "getafe")
    assert getafe is not None
    assert getafe.tendency == 1.3
    assert repo.get_team_cards("la_liga", "Nope") is None


def test_repo_missing_namespace(tmp_path: Path) -> None:
    repo = JsonCardsRepository(tmp_path)
    assert repo.get_all("x") == {}
    assert repo.get_team_cards("x", "Getafe") is None


def test_bundled_laliga_cards() -> None:
    data_dir = Path(__file__).resolve().parents[2] / "data" / "cards"
    repo = JsonCardsRepository(data_dir)
    cards = repo.get_all("la_liga")
    assert len(cards) >= 18


# --- model --------------------------------------------------------------


def test_strict_referee_increases_cards() -> None:
    model = TeamCardsModel()
    lenient = model.predict(1.0, 1.0, referee_strictness=0.8).total
    strict = model.predict(1.0, 1.0, referee_strictness=1.4).total
    assert strict > lenient


def test_aggressive_team_gets_more_cards() -> None:
    model = TeamCardsModel()
    est = model.predict(home_tendency=1.5, away_tendency=0.8)
    assert est.home_cards > est.away_cards


def test_distribution_normalized_and_over() -> None:
    est = TeamCardsModel().predict(1.0, 1.0)
    assert est.distribution.sum() == pytest.approx(1.0, abs=1e-9)
    assert 0.0 <= est.over(4.5) <= 1.0


@pytest.mark.parametrize("kwargs", [{"base_per_team": 0}, {"max_cards": 0}])
def test_invalid_params(kwargs: dict[str, float]) -> None:
    with pytest.raises(ValueError):
        TeamCardsModel(**kwargs)  # type: ignore[arg-type]


def test_invalid_inputs() -> None:
    with pytest.raises(ValueError):
        TeamCardsModel().predict(0.0, 1.0)
    with pytest.raises(ValueError):
        TeamCardsModel().predict(1.0, 1.0, referee_strictness=0)
