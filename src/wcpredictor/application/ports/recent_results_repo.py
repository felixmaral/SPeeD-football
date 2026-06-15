"""Puerto de salida: resultados recientes de un equipo y head-to-head.

Devuelve resultados "en crudo" desde la perspectiva del equipo (goles a favor/contra
y nombre del rival). La conversión a `RecentResult` del dominio —que necesita la fuerza
del rival— la hace la capa de aplicación combinando con el `RatingsRepository`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class TeamMatchResult:
    """Un partido ya jugado, visto desde el equipo consultado."""

    when: date
    goals_for: int
    goals_against: int
    opponent_name: str


class RecentResultsRepository(ABC):
    """Fuente de resultados recientes y enfrentamientos directos."""

    @abstractmethod
    async def get_recent_results(
        self, team_id: int, season: int, league_id: int | None = None
    ) -> list[TeamMatchResult]:
        """Resultados finalizados del equipo, ordenados de más reciente a más antiguo."""
        raise NotImplementedError

    @abstractmethod
    async def get_head_to_head(self, home_id: int, away_id: int) -> list[TeamMatchResult]:
        """Enfrentamientos directos vistos desde `home_id`, de más reciente a más antiguo."""
        raise NotImplementedError
