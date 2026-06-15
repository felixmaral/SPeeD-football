"""Tests del lanzador CLI y el ConsoleNotifier."""

import io
from datetime import date

import pytest

from wcpredictor.config.settings import Settings
from wcpredictor.delivery.cli.launcher import (
    _parse_args,
    build_fixture_repository,
    build_use_case,
    run,
)
from wcpredictor.infrastructure.fixtures.api_football import ApiFootballFixtureRepository
from wcpredictor.infrastructure.fixtures.mock import MockFixtureRepository
from wcpredictor.infrastructure.notifiers.console import ConsoleNotifier


def _settings() -> Settings:
    return Settings(_env_file=None)  # type: ignore[call-arg]


async def test_console_notifier_writes_report() -> None:
    buffer = io.StringIO()
    await ConsoleNotifier(buffer).send_prediction("console", "INFORME")
    assert "INFORME" in buffer.getvalue()


def test_build_fixture_repository_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("API_FOOTBALL_KEY", raising=False)
    monkeypatch.setenv("WCPREDICTOR_USE_MOCK", "true")
    repo = build_fixture_repository(_settings())
    assert isinstance(repo, MockFixtureRepository)


def test_build_fixture_repository_api(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WCPREDICTOR_USE_MOCK", "false")
    monkeypatch.setenv("API_FOOTBALL_KEY", "abc123")
    repo = build_fixture_repository(_settings())
    assert isinstance(repo, ApiFootballFixtureRepository)


async def test_run_prints_predictions(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WCPREDICTOR_USE_MOCK", "true")
    use_case = build_use_case(_settings())
    buffer = io.StringIO()
    count = await run(use_case, ConsoleNotifier(buffer), day=date(2026, 6, 15))
    assert count == 3
    assert "vs" in buffer.getvalue()


async def test_run_handles_no_matches() -> None:
    from wcpredictor.application.ports.ratings_repo import RatingsRepository, TeamRating
    from wcpredictor.application.use_cases.predict_today import PredictTodayMatches
    from wcpredictor.infrastructure.leagues.world_cup import WorldCupLeague

    class _EmptyRatings(RatingsRepository):
        def get_rating(self, namespace: str, team_name: str) -> TeamRating | None:
            return None

        def get_all(self, namespace: str) -> dict[str, TeamRating]:
            return {}

    uc = PredictTodayMatches(
        fixture_repo=MockFixtureRepository(fixtures={}),
        ratings_repo=_EmptyRatings(),
        league=WorldCupLeague(),
        clock=lambda: date(2026, 6, 15),
    )
    buffer = io.StringIO()
    count = await run(uc, ConsoleNotifier(buffer))
    assert count == 0
    assert "No hay partidos" in buffer.getvalue()


def test_parse_args_date() -> None:
    assert _parse_args(["--date", "2026-06-15"]).date == "2026-06-15"
    assert _parse_args([]).date is None


async def test_explain_run_includes_breakdown_and_matrix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import io as _io
    from datetime import date as _date
    from pathlib import Path as _Path

    from wcpredictor.application.ports.recent_results_repo import TeamMatchResult
    from wcpredictor.application.use_cases.predict_today import PredictTodayMatches
    from wcpredictor.infrastructure.fixtures.recent_results import MockRecentResultsRepository
    from wcpredictor.infrastructure.leagues.world_cup import WorldCupLeague
    from wcpredictor.infrastructure.ratings.json_repo import JsonRatingsRepository

    data_dir = _Path(__file__).resolve().parents[2] / "data" / "ratings"
    recent = {"Spain": [TeamMatchResult(_date(2026, 6, 12), 4, 0, "Rival")]}
    uc = PredictTodayMatches(
        fixture_repo=MockFixtureRepository(),
        ratings_repo=JsonRatingsRepository(data_dir),
        league=WorldCupLeague(),
        recent_results_repo=MockRecentResultsRepository(recent=recent),
        clock=lambda: _date(2026, 6, 15),
    )
    from wcpredictor.delivery.cli.launcher import run

    buffer = _io.StringIO()
    count = await run(uc, ConsoleNotifier(buffer), day=_date(2026, 6, 15), explain=True)
    out = buffer.getvalue()
    assert count == 3
    assert "Desglose por variable" in out
    assert "Base (ratings)" in out
    assert "+ Forma reciente" in out
    assert "Matriz de marcador" in out  # sigue mostrando todo lo demás
