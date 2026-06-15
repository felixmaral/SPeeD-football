"""Tests del servicio Explainer (v0: resultado/marcador)."""

from datetime import UTC, datetime

from wcpredictor.domain.entities.match import Match
from wcpredictor.domain.entities.team import Team
from wcpredictor.domain.models.dixon_coles import DixonColesModel
from wcpredictor.domain.services.explainer import Explainer, _pct


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
    return Explainer().explain(match, probs)


def test_report_contains_team_names() -> None:
    report = _report()
    assert "Spain" in report
    assert "Brazil" in report


def test_report_has_sections() -> None:
    report = _report()
    for section in ["Pronóstico:", "Resultado (1X2):", "Goles esperados:", "Over 2.5"]:
        assert section in report


def test_report_excludes_v0_removed_sections() -> None:
    report = _report()
    assert "Tarjetas" not in report
    assert "Posesión" not in report
    assert "xG" not in report


def test_headline_picks_favourite() -> None:
    report = _report()
    assert report.splitlines()[1].startswith("Pronóstico: Spain")


def test_report_is_deterministic() -> None:
    assert _report() == _report()


def test_report_includes_score_matrix() -> None:
    match = _match()
    probs = DixonColesModel().predict(match.home, match.away)
    report = Explainer(matrix_max_goals=6).explain(match, probs)
    assert "Matriz de marcador" in report
    # 7 columnas (0..6) en la cabecera.
    assert all(str(i) in report for i in range(7))
    # Las filas 0..6 del visitante deben existir (7 filas de datos).
    data_rows = [ln for ln in report.splitlines() if ln.strip()[:1].isdigit() and "." in ln]
    assert len(data_rows) >= 7


def test_pct_never_zero() -> None:
    assert _pct(0.0) == "<0.1%"
    assert _pct(0.0004) == "<0.1%"
    assert _pct(0.523) == "52.3%"
