"""Tests del servicio Predictor (orquestación del dominio)."""

from datetime import UTC, datetime

import pytest

from wcpredictor.domain.entities.match import Match, MatchStatus
from wcpredictor.domain.entities.player import Player, Position
from wcpredictor.domain.entities.referee import Referee
from wcpredictor.domain.entities.team import Team
from wcpredictor.domain.services.predictor import Predictor


def _match(status: MatchStatus = MatchStatus.SCHEDULED) -> Match:
    return Match(
        id=7,
        home=Team(id=1, name="Spain", attack=1.5, defense=0.8),
        away=Team(id=2, name="Brazil", attack=1.3, defense=0.9),
        kickoff=datetime(2026, 6, 15, 18, 0, tzinfo=UTC),
        league_id=1,
        referee=Referee(id=3, name="Ref", strictness=1.2),
        status=status,
    )


def test_predict_produces_full_prediction() -> None:
    pred = Predictor().predict(_match())
    assert pred.match_id == 7
    total = pred.probabilities.home_win + pred.probabilities.draw + pred.probabilities.away_win
    assert total == pytest.approx(1.0, abs=1e-9)
    assert pred.cards.expected_cards > 0
    assert "Spain" in pred.report


def test_scheduled_is_not_confirmed() -> None:
    assert Predictor().predict(_match()).confirmed is False


def test_confirmed_lineup_marks_prediction() -> None:
    pred = Predictor().predict(_match(MatchStatus.LINEUP_CONFIRMED))
    assert pred.confirmed is True


def test_version_stable_for_same_lineup() -> None:
    match = _match()
    players = [
        Player(id=1, name="A", team_id=1, position=Position.FWD, available=True),
        Player(id=2, name="B", team_id=2, position=Position.DEF, available=False),
    ]
    v1 = Predictor().predict(match, players).version
    v2 = Predictor().predict(match, list(reversed(players))).version
    assert v1 == v2


def test_version_changes_with_availability() -> None:
    match = _match()
    p_avail = [Player(id=1, name="A", team_id=1, position=Position.FWD, available=True)]
    p_out = [Player(id=1, name="A", team_id=1, position=Position.FWD, available=False)]
    assert Predictor().predict(match, p_avail).version != Predictor().predict(match, p_out).version


def test_absence_of_key_attacker_lowers_home_win() -> None:
    match = _match()
    star = Player(
        id=10, name="Star", team_id=1, position=Position.FWD, importance=0.6, available=False
    )
    base = Predictor().predict(match)
    weakened = Predictor().predict(match, [star])
    assert weakened.probabilities.home_win < base.probabilities.home_win
