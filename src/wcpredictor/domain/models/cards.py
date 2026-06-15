"""Modelo de tarjetas de un partido.

Estima las tarjetas esperadas combinando: una tasa base de la liga, la severidad
del árbitro, la agresividad de los equipos y, opcionalmente, el riesgo individual
de los jugadores. La distribución del número de tarjetas se modela como Poisson.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from wcpredictor.domain.entities.player import Player
from wcpredictor.domain.entities.referee import Referee
from wcpredictor.domain.models.poisson import poisson_pmf


@dataclass(frozen=True, slots=True)
class CardsPrediction:
    """Resultado del modelo de tarjetas."""

    expected_cards: float
    distribution: NDArray[np.float64]

    def over(self, line: float = 4.5) -> float:
        counts = np.arange(self.distribution.shape[0])
        return float(self.distribution[counts > line].sum())

    def under(self, line: float = 4.5) -> float:
        return 1.0 - self.over(line)


@dataclass(frozen=True, slots=True)
class CardsModel:
    """Modelo de tarjetas parametrizado.

    - `base_rate`: tarjetas medias por partido en la liga.
    - `player_weight`: cuánto suma el riesgo individual agregado de los jugadores.
    - `max_cards`: truncamiento de la distribución.
    """

    base_rate: float = 4.0
    player_weight: float = 1.0
    max_cards: int = 15

    def __post_init__(self) -> None:
        if self.base_rate <= 0:
            raise ValueError("base_rate debe ser > 0")
        if self.player_weight < 0:
            raise ValueError("player_weight debe ser >= 0")
        if self.max_cards < 1:
            raise ValueError("max_cards debe ser >= 1")

    def expected_cards(
        self,
        referee: Referee | None = None,
        aggression: float = 1.0,
        players: Iterable[Player] = (),
    ) -> float:
        """Tarjetas esperadas del partido.

        `aggression` es un multiplicador combinado de los equipos (1.0 = media).
        Sin árbitro se asume severidad media (1.0).
        """
        if aggression <= 0:
            raise ValueError("aggression debe ser > 0")
        strictness = referee.strictness if referee is not None else 1.0
        team_component = self.base_rate * strictness * aggression
        player_component = self.player_weight * sum(p.card_risk for p in players)
        return team_component + player_component

    def predict(
        self,
        referee: Referee | None = None,
        aggression: float = 1.0,
        players: Iterable[Player] = (),
    ) -> CardsPrediction:
        """Calcula tarjetas esperadas y su distribución de Poisson."""
        lam = self.expected_cards(referee, aggression, players)
        dist = poisson_pmf(lam, self.max_cards)
        dist /= dist.sum()
        return CardsPrediction(expected_cards=lam, distribution=dist)
