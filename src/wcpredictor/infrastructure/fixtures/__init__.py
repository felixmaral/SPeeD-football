"""Adaptadores de fixtures (fuentes de partidos)."""

from wcpredictor.infrastructure.fixtures.api_football import ApiFootballFixtureRepository
from wcpredictor.infrastructure.fixtures.mock import MockFixtureRepository
from wcpredictor.infrastructure.fixtures.recent_results import (
    Martj42RecentResultsRepository,
    MockRecentResultsRepository,
)

__all__ = [
    "ApiFootballFixtureRepository",
    "Martj42RecentResultsRepository",
    "MockFixtureRepository",
    "MockRecentResultsRepository",
]
