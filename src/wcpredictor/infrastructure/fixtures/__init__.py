"""Adaptadores de fixtures (fuentes de partidos)."""

from wcpredictor.infrastructure.fixtures.api_football import ApiFootballFixtureRepository
from wcpredictor.infrastructure.fixtures.mock import MockFixtureRepository

__all__ = ["ApiFootballFixtureRepository", "MockFixtureRepository"]
