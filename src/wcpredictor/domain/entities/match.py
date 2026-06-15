"""Entidad Match — un partido entre dos equipos."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from wcpredictor.domain.entities.referee import Referee
from wcpredictor.domain.entities.team import Team


class MatchStatus(StrEnum):
    """Estado del partido respecto a la disponibilidad de información."""

    SCHEDULED = "SCHEDULED"
    LINEUP_CONFIRMED = "LINEUP_CONFIRMED"
    FINISHED = "FINISHED"


@dataclass(frozen=True, slots=True)
class Match:
    """Partido del dominio.

    Núcleo de entrada para la predicción: dos equipos, fecha de inicio (kickoff),
    liga, árbitro (opcional hasta designación) y estado.
    """

    id: int
    home: Team
    away: Team
    kickoff: datetime
    league_id: int
    referee: Referee | None = None
    status: MatchStatus = MatchStatus.SCHEDULED

    def __post_init__(self) -> None:
        if self.home.id == self.away.id:
            raise ValueError("Match: home y away no pueden ser el mismo equipo")

    @property
    def has_confirmed_lineup(self) -> bool:
        return self.status is MatchStatus.LINEUP_CONFIRMED
