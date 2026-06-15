"""Puerto de salida: resultados recientes de un equipo y head-to-head.

Devuelve resultados "en crudo" desde la perspectiva del equipo (goles a favor/contra
y nombre del rival), identificados por **nombre** de equipo. La conversión a
`RecentResult` del dominio —que necesita la fuerza del rival— la hace la capa de
aplicación combinando con el `RatingsRepository`.
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
    """Fuente de resultados recientes y enfrentamientos directos (por nombre)."""

    @abstractmethod
    async def get_recent_results(self, team_name: str, limit: int = 10) -> list[TeamMatchResult]:
        """Últimos resultados del equipo, de más reciente a más antiguo (máx. `limit`)."""
        raise NotImplementedError

    @abstractmethod
    async def get_head_to_head(
        self, home_name: str, away_name: str, limit: int = 5
    ) -> list[TeamMatchResult]:
        """Enfrentamientos directos vistos desde `home_name`, de más reciente a más antiguo."""
        raise NotImplementedError
