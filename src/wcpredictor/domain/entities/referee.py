"""Entidad Referee — árbitro con un factor de severidad."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Referee:
    """Árbitro del dominio.

    `strictness` es un multiplicador sobre la tasa base de tarjetas: 1.0 = media de
    la liga, > 1.0 más severo, < 1.0 más permisivo.
    """

    id: int
    name: str
    strictness: float = 1.0

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Referee.name no puede estar vacío")
        if self.strictness <= 0:
            raise ValueError("Referee.strictness debe ser > 0")
