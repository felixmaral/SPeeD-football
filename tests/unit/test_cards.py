"""Tests del modelo de tarjetas."""

import pytest

from wcpredictor.domain.entities.player import Player, Position
from wcpredictor.domain.entities.referee import Referee
from wcpredictor.domain.models.cards import CardsModel


def test_distribution_normalized() -> None:
    pred = CardsModel().predict()
    assert pred.distribution.sum() == pytest.approx(1.0, abs=1e-9)
    assert (pred.distribution >= 0).all()


def test_no_referee_uses_average() -> None:
    model = CardsModel(base_rate=4.0)
    assert model.expected_cards() == pytest.approx(4.0)


def test_strict_referee_increases_cards() -> None:
    model = CardsModel(base_rate=4.0)
    strict = Referee(id=1, name="Strict", strictness=1.5)
    lenient = Referee(id=2, name="Lenient", strictness=0.7)
    assert model.expected_cards(strict) > model.expected_cards(lenient)
    assert model.expected_cards(strict) == pytest.approx(6.0)


def test_aggression_scales_cards() -> None:
    model = CardsModel(base_rate=4.0)
    assert model.expected_cards(aggression=1.5) == pytest.approx(6.0)


def test_player_risk_adds_cards() -> None:
    model = CardsModel(base_rate=4.0, player_weight=2.0)
    players = [
        Player(id=1, name="A", team_id=1, position=Position.DEF, card_risk=0.5),
        Player(id=2, name="B", team_id=1, position=Position.MID, card_risk=0.5),
    ]
    assert model.expected_cards(players=players) == pytest.approx(4.0 + 2.0 * 1.0)


def test_over_under_complementary() -> None:
    pred = CardsModel().predict()
    assert pred.over(4.5) + pred.under(4.5) == pytest.approx(1.0, abs=1e-9)


def test_invalid_aggression() -> None:
    with pytest.raises(ValueError, match="aggression"):
        CardsModel().expected_cards(aggression=0)


@pytest.mark.parametrize(
    "kwargs",
    [{"base_rate": 0}, {"player_weight": -1}, {"max_cards": 0}],
)
def test_invalid_params(kwargs: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        CardsModel(**kwargs)  # type: ignore[arg-type]
