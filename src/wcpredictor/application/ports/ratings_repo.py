"""Puerto de salida: repositorio de ratings de equipos.

Los ratings se identifican por **nombre de equipo**, no por id, para ser robustos
entre fuentes distintas (la fuente de fixtures y la de entrenamiento usan espacios
de ids diferentes, pero los nombres son comparables).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TeamRating:
    """Fuerzas de un equipo entrenadas para una competición.

    `attack`/`defense` son las fuerzas multiplicativas que consume el dominio
    (ver `Team`), identificadas por `team` (nombre) dentro de un namespace.
    """

    team: str
    attack: float
    defense: float


class RatingsRepository(ABC):
    """Fuente de ratings entrenados (JSON, base de datos, etc.)."""

    @abstractmethod
    def get_rating(self, namespace: str, team_name: str) -> TeamRating | None:
        """Devuelve el rating de un equipo por nombre, o `None` si no existe."""
        raise NotImplementedError

    @abstractmethod
    def get_all(self, namespace: str) -> dict[str, TeamRating]:
        """Devuelve todos los ratings de un namespace, indexados por nombre."""
        raise NotImplementedError
