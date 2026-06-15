"""Puerto de salida: repositorio de tarjetas por equipo (identidad por nombre)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TeamCards:
    """Estadísticas de tarjetas/faltas de un equipo (medias por partido).

    `tendency` es la propensión a tarjetas relativa a la media de la liga (≈1.0).
    """

    team: str
    cards_per_match: float
    tendency: float
    fouls_committed_per_match: float = 0.0
    fouls_drawn_per_match: float = 0.0


class CardsRepository(ABC):
    """Fuente de estadísticas de tarjetas por equipo (JSON, base de datos, etc.)."""

    @abstractmethod
    def get_team_cards(self, namespace: str, team_name: str) -> TeamCards | None:
        """Devuelve las tarjetas del equipo por nombre, o `None` si no existe."""
        raise NotImplementedError

    @abstractmethod
    def get_all(self, namespace: str) -> dict[str, TeamCards]:
        """Devuelve todas las estadísticas de tarjetas de un namespace, por nombre."""
        raise NotImplementedError
