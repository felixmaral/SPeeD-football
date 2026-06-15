"""Entidad Team — equipo con fuerzas ofensiva y defensiva (ratings del modelo)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Team:
    """Equipo del dominio.

    Los ratings son fuerzas relativas usadas por el modelo Dixon-Coles:
    `attack` > 1 indica un ataque por encima de la media de la liga; `defense` < 1
    indica una defensa mejor que la media (encaja menos).
    """

    id: int
    name: str
    attack: float = 1.0
    defense: float = 1.0

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Team.name no puede estar vacío")
        if self.attack <= 0:
            raise ValueError("Team.attack debe ser > 0")
        if self.defense <= 0:
            raise ValueError("Team.defense debe ser > 0")
