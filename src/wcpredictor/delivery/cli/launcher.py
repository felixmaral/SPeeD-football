"""Lanzador por CLI: imprime las predicciones del día.

Uso:
    python -m wcpredictor.delivery.cli.launcher [--date YYYY-MM-DD]
"""

from __future__ import annotations

import argparse
import asyncio
from datetime import date
from pathlib import Path

from wcpredictor.application.ports.fixture_repo import FixtureRepository
from wcpredictor.application.ports.notifier import Notifier
from wcpredictor.application.use_cases.predict_today import PredictTodayMatches
from wcpredictor.config.settings import Settings
from wcpredictor.infrastructure.fixtures.api_football import ApiFootballFixtureRepository
from wcpredictor.infrastructure.fixtures.mock import MockFixtureRepository
from wcpredictor.infrastructure.fixtures.recent_results import Martj42RecentResultsRepository
from wcpredictor.infrastructure.leagues.world_cup import WorldCupLeague
from wcpredictor.infrastructure.notifiers.console import ConsoleNotifier
from wcpredictor.infrastructure.ratings.json_repo import JsonRatingsRepository

_DEFAULT_RATINGS_DIR = Path("data/ratings")


def build_fixture_repository(settings: Settings) -> FixtureRepository:
    """Selecciona el adaptador de fixtures según la configuración."""
    if settings.effective_use_mock:
        return MockFixtureRepository()
    return ApiFootballFixtureRepository(
        api_key=settings.api_football_key,
        base_url=settings.api_football_base_url,
    )


def build_use_case(
    settings: Settings, ratings_dir: Path = _DEFAULT_RATINGS_DIR
) -> PredictTodayMatches:
    """Construye el caso de uso con sus dependencias (raíz de composición)."""
    # La forma reciente (martj42) es gratuita y sin red solo en modo real; en mock se omite.
    recent_repo = None if settings.effective_use_mock else Martj42RecentResultsRepository()
    return PredictTodayMatches(
        fixture_repo=build_fixture_repository(settings),
        ratings_repo=JsonRatingsRepository(ratings_dir),
        league=WorldCupLeague(),
        recent_results_repo=recent_repo,
    )


async def run(
    use_case: PredictTodayMatches,
    notifier: Notifier,
    day: date | None = None,
) -> int:
    """Ejecuta el caso de uso y notifica las predicciones. Devuelve el nº de partidos."""
    predictions = await use_case.execute(day)
    if not predictions:
        await notifier.send_prediction("console", "No hay partidos para la fecha indicada.")
        return 0
    for prediction in predictions:
        await notifier.send_prediction("console", prediction.report)
    return len(predictions)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Predicciones del día (wcpredictor).")
    parser.add_argument("--date", help="Fecha en formato YYYY-MM-DD (por defecto: hoy)")
    return parser.parse_args(argv)


def _enable_system_trust() -> None:
    """Usa el almacén de certificados del sistema operativo para la validación TLS."""
    try:
        import truststore

        truststore.inject_into_ssl()
    except Exception:
        pass


def main(argv: list[str] | None = None) -> int:
    _enable_system_trust()
    args = _parse_args(argv)
    day = date.fromisoformat(args.date) if args.date else None
    settings = Settings()
    use_case = build_use_case(settings)
    return asyncio.run(run(use_case, ConsoleNotifier(), day))


if __name__ == "__main__":
    raise SystemExit(main())
