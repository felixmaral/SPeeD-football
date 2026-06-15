"""Puerto de salida: repositorio de ratings de equipos."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TeamRating:
    """Fuerzas de un equipo entrenadas para una competición.

    `attack`/`defense` son las fuerzas multiplicativas que consume el dominio
    (ver `Team`). Se identifican por `team_id` dentro de un `ratings_namespace`.
    """

    team_id: int
    attack: float
    defense: float


class RatingsRepository(ABC):
    """Fuente de ratings entrenados (JSON, base de datos, etc.)."""

    @abstractmethod
    def get_team_rating(self, namespace: str, team_id: int) -> TeamRating | None:
        """Devuelve el rating de un equipo, o `None` si no existe."""
        raise NotImplementedError

    @abstractmethod
    def get_all(self, namespace: str) -> dict[int, TeamRating]:
        """Devuelve todos los ratings de un namespace, indexados por `team_id`."""
        raise NotImplementedError
