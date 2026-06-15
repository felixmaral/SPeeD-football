"""Plugins de liga e infraestructura de registro."""

from wcpredictor.infrastructure.leagues.base import LeaguePlugin, LeagueRegistry
from wcpredictor.infrastructure.leagues.world_cup import (
    WORLD_CUP_LEAGUE_ID,
    WorldCupLeague,
)

__all__ = [
    "WORLD_CUP_LEAGUE_ID",
    "LeaguePlugin",
    "LeagueRegistry",
    "WorldCupLeague",
]
