"""Ajuste de la fuerza de un equipo según la disponibilidad de sus jugadores.

Las bajas (lesiones, sanciones, no convocados) degradan la fuerza del equipo en
proporción a la importancia de los jugadores ausentes y a su rol: las bajas
ofensivas (MID/FWD) reducen el ataque; las defensivas (GK/DEF) empeoran la
defensa (sube el rating, que representa goles encajados).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, replace

from wcpredictor.domain.entities.player import Player, Position
from wcpredictor.domain.entities.team import Team

_OFFENSIVE = frozenset({Position.MID, Position.FWD})
_DEFENSIVE = frozenset({Position.GK, Position.DEF})


@dataclass(frozen=True, slots=True)
class AvailabilityAdjuster:
    """Ajusta `Team.attack`/`Team.defense` según las bajas.

    - `sensitivity`: cuánto pesa la importancia perdida (1.0 = directo).
    - `floor`: factor mínimo aplicado al ataque para que no se anule (0..1].
    - `ceil`: factor máximo aplicado a la defensa (penalización máxima).
    """

    sensitivity: float = 1.0
    floor: float = 0.5
    ceil: float = 2.0

    def __post_init__(self) -> None:
        if self.sensitivity < 0:
            raise ValueError("sensitivity debe ser >= 0")
        if not 0.0 < self.floor <= 1.0:
            raise ValueError("floor debe estar en (0, 1]")
        if self.ceil < 1.0:
            raise ValueError("ceil debe ser >= 1")

    def adjust(self, team: Team, players: Iterable[Player]) -> Team:
        """Devuelve un nuevo `Team` con la fuerza ajustada por las bajas.

        Solo se consideran jugadores de `team`. Los disponibles no afectan.
        """
        missing_off = 0.0
        missing_def = 0.0
        for p in players:
            if p.team_id != team.id or p.available:
                continue
            if p.position in _OFFENSIVE:
                missing_off += p.importance
            elif p.position in _DEFENSIVE:
                missing_def += p.importance

        attack_factor = max(self.floor, 1.0 - self.sensitivity * missing_off)
        defense_factor = min(self.ceil, 1.0 + self.sensitivity * missing_def)

        return replace(
            team,
            attack=team.attack * attack_factor,
            defense=team.defense * defense_factor,
        )
