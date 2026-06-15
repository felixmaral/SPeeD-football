"""Tests del servicio Explainer."""

from datetime import UTC, datetime

from wcpredictor.domain.entities.match import Match
from wcpredictor.domain.entities.team import Team
from wcpredictor.domain.models.cards import CardsModel
from wcpredictor.domain.models.dixon_coles import DixonColesModel
from wcpredictor.domain.models.performance import PerformanceModel
from wcpredictor.domain.services.explainer import Explainer


def _match() -> Match:
    return Match(
        id=1,
        home=Team(id=1, name="Spain", attack=1.6, defense=0.7),
        away=Team(id=2, name="Brazil", attack=1.2, defense=0.9),
        kickoff=datetime(2026, 6, 15, 18, 0, tzinfo=UTC),
        league_id=1,
    )


def _report() -> str:
    match = _match()
    probs = DixonColesModel().predict(match.home, match.away)
    cards = CardsModel().predict()
    perf = PerformanceModel().predict(match.home, match.away)
    return Explainer().explain(match, probs, cards, perf)


def test_report_contains_team_names() -> None:
    report = _report()
    assert "Spain" in report
    assert "Brazil" in report


def test_report_has_sections() -> None:
    report = _report()
    for section in ["Pronóstico:", "Resultado (1X2):", "Tarjetas:", "Rendimiento:"]:
        assert section in report


def test_headline_picks_favourite() -> None:
    report = _report()
    # Spain es claramente más fuerte -> debe encabezar el pronóstico.
    assert report.splitlines()[1].startswith("Pronóstico: Spain")


def test_report_is_deterministic() -> None:
    assert _report() == _report()
