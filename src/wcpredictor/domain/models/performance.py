"""Modelo de rendimiento esperado de un partido.

Estima métricas por equipo —goles esperados (xG), posesión y toques en el área—
a partir de las fuerzas de ataque/defensa de los equipos. Determinista y puro.
"""

from __future__ import annotations

from dataclasses import dataclass

from wcpredictor.domain.entities.team import Team


@dataclass(frozen=True, slots=True)
class TeamPerformance:
    """Métricas de rendimiento esperadas de un equipo en el partido."""

    xg: float
    possession: float
    box_touches: float


@dataclass(frozen=True, slots=True)
class MatchPerformance:
    """Rendimiento esperado de ambos equipos."""

    home: TeamPerformance
    away: TeamPerformance


@dataclass(frozen=True, slots=True)
class PerformanceModel:
    """Modelo de rendimiento parametrizado.

    - `base_xg`: xG medio de un equipo en la liga.
    - `home_advantage`: multiplicador del xG local.
    - `touches_per_xg`: toques en el área esperados por unidad de xG.
    """

    base_xg: float = 1.35
    home_advantage: float = 1.2
    touches_per_xg: float = 18.0

    def __post_init__(self) -> None:
        if self.base_xg <= 0:
            raise ValueError("base_xg debe ser > 0")
        if self.home_advantage <= 0:
            raise ValueError("home_advantage debe ser > 0")
        if self.touches_per_xg <= 0:
            raise ValueError("touches_per_xg debe ser > 0")

    def predict(self, home: Team, away: Team) -> MatchPerformance:
        """Calcula el rendimiento esperado de ambos equipos."""
        xg_home = self.base_xg * home.attack * away.defense * self.home_advantage
        xg_away = self.base_xg * away.attack * home.defense

        # Posesión: cuota de dominio ofensivo, normalizada a 100%.
        dominance_home = home.attack / away.defense * self.home_advantage
        dominance_away = away.attack / home.defense
        total = dominance_home + dominance_away
        possession_home = 100.0 * dominance_home / total
        possession_away = 100.0 - possession_home

        return MatchPerformance(
            home=TeamPerformance(
                xg=xg_home,
                possession=possession_home,
                box_touches=xg_home * self.touches_per_xg,
            ),
            away=TeamPerformance(
                xg=xg_away,
                possession=possession_away,
                box_touches=xg_away * self.touches_per_xg,
            ),
        )
