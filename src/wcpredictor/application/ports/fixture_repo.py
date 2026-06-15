"""Puerto de salida: repositorio de fixtures (partidos y alineaciones)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date

from wcpredictor.domain.entities.match import Match
from wcpredictor.domain.entities.player import Player


@dataclass(frozen=True, slots=True)
class LineupInfo:
    """Disponibilidad de la alineación de un partido.

    `confirmed` indica si el once ya está confirmado (vs. preliminar/estimado).
    `players` son los jugadores con su disponibilidad (`Player.available`).
    """

    confirmed: bool
    players: tuple[Player, ...] = ()

    def available_players(self) -> tuple[Player, ...]:
        return tuple(p for p in self.players if p.available)


class FixtureRepository(ABC):
    """Fuente de partidos y alineaciones (API real, mock, etc.)."""

    @abstractmethod
    async def get_fixtures_for_date(self, day: date, league_id: int) -> list[Match]:
        """Devuelve los partidos de `league_id` programados para `day`."""
        raise NotImplementedError

    @abstractmethod
    async def get_lineup_availability(self, fixture_id: int) -> LineupInfo:
        """Devuelve la disponibilidad de alineación de un partido."""
        raise NotImplementedError
