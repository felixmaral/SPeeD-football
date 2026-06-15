"""Entidad Player — jugador con posición, riesgo de tarjeta y disponibilidad."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Position(StrEnum):
    """Posición demarcada del jugador."""

    GK = "GK"
    DEF = "DEF"
    MID = "MID"
    FWD = "FWD"


@dataclass(frozen=True, slots=True)
class Player:
    """Jugador del dominio.

    `importance` (0..1) modela cuánto aporta el jugador a la fuerza del equipo;
    se usa en el ajuste por disponibilidad. `card_risk` (0..1) es la propensión
    individual a ver tarjeta, usada por el modelo de tarjetas.
    """

    id: int
    name: str
    team_id: int
    position: Position
    importance: float = 0.0
    card_risk: float = 0.0
    available: bool = True

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Player.name no puede estar vacío")
        if not 0.0 <= self.importance <= 1.0:
            raise ValueError("Player.importance debe estar en [0, 1]")
        if not 0.0 <= self.card_risk <= 1.0:
            raise ValueError("Player.card_risk debe estar en [0, 1]")
