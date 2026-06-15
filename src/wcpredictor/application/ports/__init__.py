"""Puertos (interfaces) de la capa de aplicación."""

from wcpredictor.application.ports.fixture_repo import FixtureRepository, LineupInfo
from wcpredictor.application.ports.ratings_repo import RatingsRepository, TeamRating

__all__ = [
    "FixtureRepository",
    "LineupInfo",
    "RatingsRepository",
    "TeamRating",
]
