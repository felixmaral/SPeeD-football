"""Fuerza de un equipo a partir de la calidad de su plantilla disponible.

Construye un factor de fuerza con los **11 mejores titulares + N suplentes** (fondo de
armario) disponibles: los titulares pesan pleno y los suplentes parcialmente. El factor
modula el ataque/defensa del equipo, de modo que las bajas de jugadores importantes lo
reducen. Servicio puro de dominio.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from wcpredictor.domain.entities.player import Position
from wcpredictor.domain.entities.team import Team


@dataclass(frozen=True, slots=True)
class PlayerRating:
    """Calidad relativa de un jugador (rating ~1.0 = jugador medio de selección)."""

    name: str
    position: Position
    rating: float
    available: bool = True

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("PlayerRating.name no puede estar vacío")
        if self.rating <= 0:
            raise ValueError("PlayerRating.rating debe ser > 0")


@dataclass(frozen=True, slots=True)
class SquadAggregator:
    """Agrega ratings de jugadores en un factor de fuerza de equipo.

    - `starters`/`bench`: nº de titulares y suplentes considerados.
    - `bench_weight`: peso de cada suplente respecto a un titular (0..1].
    - `sensitivity`: cuánto se traslada el factor al rating del equipo.
    - `floor`/`ceil`: recorte del factor aplicado.
    """

    starters: int = 11
    bench: int = 5
    bench_weight: float = 0.3
    sensitivity: float = 1.0
    floor: float = 0.7
    ceil: float = 1.4

    def __post_init__(self) -> None:
        if self.starters < 1:
            raise ValueError("starters debe ser >= 1")
        if self.bench < 0:
            raise ValueError("bench debe ser >= 0")
        if not 0 < self.bench_weight <= 1:
            raise ValueError("bench_weight debe estar en (0, 1]")
        if self.sensitivity < 0:
            raise ValueError("sensitivity debe ser >= 0")
        if not 0 < self.floor <= 1 <= self.ceil:
            raise ValueError("Debe cumplirse 0 < floor <= 1 <= ceil")

    def squad_factor(self, players: Iterable[PlayerRating]) -> float:
        """Factor de fuerza de la plantilla; una plantilla media da 1.0."""
        available = sorted(
            (p for p in players if p.available), key=lambda p: p.rating, reverse=True
        )
        if not available:
            return 1.0

        selected = available[: self.starters]
        bench = available[self.starters : self.starters + self.bench]
        weighted_sum = sum(p.rating for p in selected)
        total_weight = float(len(selected))
        for p in bench:
            weighted_sum += self.bench_weight * p.rating
            total_weight += self.bench_weight
        return weighted_sum / total_weight

    def adjust(self, team: Team, players: Iterable[PlayerRating]) -> Team:
        """Aplica el factor de plantilla: mejor plantilla = más ataque y mejor defensa."""
        factor = self.squad_factor(players) ** self.sensitivity
        factor = max(self.floor, min(self.ceil, factor))
        return Team(
            id=team.id,
            name=team.name,
            attack=team.attack * factor,
            defense=team.defense / factor,
        )
