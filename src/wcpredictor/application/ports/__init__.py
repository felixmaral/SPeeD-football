"""Puertos (interfaces) de la capa de aplicación."""

from wcpredictor.application.ports.cards_repo import CardsRepository, TeamCards
from wcpredictor.application.ports.fixture_repo import FixtureRepository, LineupInfo
from wcpredictor.application.ports.notifier import Notifier
from wcpredictor.application.ports.ratings_repo import RatingsRepository, TeamRating
from wcpredictor.application.ports.recent_results_repo import (
    RecentResultsRepository,
    TeamMatchResult,
)

__all__ = [
    "CardsRepository",
    "FixtureRepository",
    "LineupInfo",
    "Notifier",
    "RatingsRepository",
    "RecentResultsRepository",
    "TeamCards",
    "TeamMatchResult",
    "TeamRating",
]
