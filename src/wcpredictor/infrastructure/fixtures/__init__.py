"""Adaptadores de fixtures (fuentes de partidos)."""

from wcpredictor.infrastructure.fixtures.api_football import ApiFootballFixtureRepository
from wcpredictor.infrastructure.fixtures.mock import MockFixtureRepository
from wcpredictor.infrastructure.fixtures.recent_results import (
    ApiFootballRecentResultsRepository,
    MockRecentResultsRepository,
)

__all__ = [
    "ApiFootballFixtureRepository",
    "ApiFootballRecentResultsRepository",
    "MockFixtureRepository",
    "MockRecentResultsRepository",
]
