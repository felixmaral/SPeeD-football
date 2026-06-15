"""Modelo Dixon-Coles para predecir el marcador de un partido.

Implementación determinista y pura (solo numpy). Dada la fuerza de ataque/defensa
de cada equipo, calcula los goles esperados (lambda) de local y visitante mediante
un modelo de Poisson bivariante con la corrección de Dixon & Coles (1997) para los
marcadores bajos, controlada por el parámetro `rho`.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from wcpredictor.domain.entities.team import Team


@dataclass(frozen=True, slots=True)
class MatchProbabilities:
    """Resultado del modelo: probabilidades 1X2 y la matriz de marcador.

    `score_matrix[i, j]` es la probabilidad de que el local marque `i` goles y el
    visitante `j`. `lambda_home`/`lambda_away` son los goles esperados.
    """

    lambda_home: float
    lambda_away: float
    score_matrix: NDArray[np.float64]

    @property
    def home_win(self) -> float:
        return float(np.tril(self.score_matrix, -1).sum())

    @property
    def draw(self) -> float:
        return float(np.trace(self.score_matrix))

    @property
    def away_win(self) -> float:
        return float(np.triu(self.score_matrix, 1).sum())

    def over(self, line: float = 2.5) -> float:
        """Probabilidad de que el total de goles supere `line`."""
        size = self.score_matrix.shape[0]
        totals = np.add.outer(np.arange(size), np.arange(size))
        return float(self.score_matrix[totals > line].sum())

    def under(self, line: float = 2.5) -> float:
        return 1.0 - self.over(line)

    @property
    def most_likely_score(self) -> tuple[int, int]:
        i, j = np.unravel_index(int(np.argmax(self.score_matrix)), self.score_matrix.shape)
        return int(i), int(j)


def _poisson_pmf(lam: float, max_goals: int) -> NDArray[np.float64]:
    """Vector PMF de Poisson para 0..max_goals."""
    k = np.arange(max_goals + 1)
    log_pmf = -lam + k * np.log(lam) - _log_factorial(k)
    pmf: NDArray[np.float64] = np.exp(log_pmf)
    return pmf


def _log_factorial(k: NDArray[np.int_]) -> NDArray[np.float64]:
    from scipy.special import gammaln

    result: NDArray[np.float64] = gammaln(k + 1.0)
    return result


@dataclass(frozen=True, slots=True)
class DixonColesModel:
    """Modelo Dixon-Coles parametrizado.

    - `home_advantage`: multiplicador (>1) aplicado a los goles esperados del local.
    - `rho`: parámetro de dependencia para la corrección de marcadores bajos.
    - `base_rate`: goles medios por equipo en la liga (escala).
    - `max_goals`: truncamiento de la matriz de marcador.
    """

    home_advantage: float = 1.35
    rho: float = -0.05
    base_rate: float = 1.35
    max_goals: int = 10

    def __post_init__(self) -> None:
        if self.home_advantage <= 0:
            raise ValueError("home_advantage debe ser > 0")
        if self.base_rate <= 0:
            raise ValueError("base_rate debe ser > 0")
        if self.max_goals < 1:
            raise ValueError("max_goals debe ser >= 1")

    def expected_goals(self, home: Team, away: Team) -> tuple[float, float]:
        """Goles esperados (lambda local, lambda visitante)."""
        lambda_home = self.base_rate * home.attack * away.defense * self.home_advantage
        lambda_away = self.base_rate * away.attack * home.defense
        return lambda_home, lambda_away

    def _tau(self, lambda_home: float, lambda_away: float) -> NDArray[np.float64]:
        """Matriz de corrección Dixon-Coles para las celdas (0,0),(0,1),(1,0),(1,1)."""
        tau = np.ones((self.max_goals + 1, self.max_goals + 1))
        tau[0, 0] = 1.0 - lambda_home * lambda_away * self.rho
        tau[0, 1] = 1.0 + lambda_home * self.rho
        tau[1, 0] = 1.0 + lambda_away * self.rho
        tau[1, 1] = 1.0 - self.rho
        return tau

    def predict(self, home: Team, away: Team) -> MatchProbabilities:
        """Calcula la matriz de marcador y las probabilidades derivadas."""
        lambda_home, lambda_away = self.expected_goals(home, away)
        home_pmf = _poisson_pmf(lambda_home, self.max_goals)
        away_pmf = _poisson_pmf(lambda_away, self.max_goals)

        matrix = np.outer(home_pmf, away_pmf) * self._tau(lambda_home, lambda_away)
        # tau puede introducir valores negativos minúsculos por rho; recortar y normalizar.
        matrix = np.clip(matrix, 0.0, None)
        matrix /= matrix.sum()

        return MatchProbabilities(
            lambda_home=lambda_home,
            lambda_away=lambda_away,
            score_matrix=matrix,
        )
