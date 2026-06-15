"""Modelo de tarjetas por equipo basado en tendencias reales.

Estima las tarjetas esperadas de cada equipo en un partido combinando su tendencia
(propensión relativa a la media de la liga) con la severidad del árbitro. Es puro:
recibe floats (las tendencias las aporta el `CardsRepository`).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from wcpredictor.domain.models.poisson import poisson_pmf


@dataclass(frozen=True, slots=True)
class TeamCardsEstimate:
    """Tarjetas esperadas por equipo y su distribución total."""

    home_cards: float
    away_cards: float
    distribution: NDArray[np.float64]

    @property
    def total(self) -> float:
        return self.home_cards + self.away_cards

    def over(self, line: float) -> float:
        counts = np.arange(self.distribution.shape[0])
        return float(self.distribution[counts > line].sum())


@dataclass(frozen=True, slots=True)
class TeamCardsModel:
    """Modelo de tarjetas por equipo.

    - `base_per_team`: tarjetas medias por equipo y partido en la liga.
    - `max_cards`: truncamiento de la distribución del total.
    """

    base_per_team: float = 2.0
    max_cards: int = 16

    def __post_init__(self) -> None:
        if self.base_per_team <= 0:
            raise ValueError("base_per_team debe ser > 0")
        if self.max_cards < 1:
            raise ValueError("max_cards debe ser >= 1")

    def predict(
        self,
        home_tendency: float,
        away_tendency: float,
        referee_strictness: float = 1.0,
    ) -> TeamCardsEstimate:
        """Tarjetas esperadas de cada equipo y distribución del total del partido."""
        if home_tendency <= 0 or away_tendency <= 0:
            raise ValueError("Las tendencias deben ser > 0")
        if referee_strictness <= 0:
            raise ValueError("referee_strictness debe ser > 0")

        home = self.base_per_team * home_tendency * referee_strictness
        away = self.base_per_team * away_tendency * referee_strictness
        distribution = poisson_pmf(home + away, self.max_cards)
        distribution /= distribution.sum()
        return TeamCardsEstimate(home_cards=home, away_cards=away, distribution=distribution)
