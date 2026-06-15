"""Plugins de liga e infraestructura de registro."""

from wcpredictor.infrastructure.leagues.base import LeaguePlugin, LeagueRegistry
from wcpredictor.infrastructure.leagues.champions_league import (
    CHAMPIONS_LEAGUE_ID,
    ChampionsLeague,
)
from wcpredictor.infrastructure.leagues.la_liga import LA_LIGA_LEAGUE_ID, LaLigaLeague
from wcpredictor.infrastructure.leagues.world_cup import (
    WORLD_CUP_LEAGUE_ID,
    WorldCupLeague,
)

__all__ = [
    "CHAMPIONS_LEAGUE_ID",
    "LA_LIGA_LEAGUE_ID",
    "WORLD_CUP_LEAGUE_ID",
    "ChampionsLeague",
    "LaLigaLeague",
    "LeaguePlugin",
    "LeagueRegistry",
    "WorldCupLeague",
]
