"""Entidades puras del dominio."""

from wcpredictor.domain.entities.match import Match, MatchStatus
from wcpredictor.domain.entities.player import Player, Position
from wcpredictor.domain.entities.referee import Referee
from wcpredictor.domain.entities.team import Team

__all__ = [
    "Match",
    "MatchStatus",
    "Player",
    "Position",
    "Referee",
    "Team",
]
