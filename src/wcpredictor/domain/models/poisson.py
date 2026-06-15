"""Utilidad compartida: PMF de Poisson vectorizada."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


def poisson_pmf(lam: float, max_k: int) -> NDArray[np.float64]:
    """Vector PMF de Poisson para los valores 0..max_k (incluido)."""
    from scipy.special import gammaln

    k = np.arange(max_k + 1)
    log_pmf = -lam + k * np.log(lam) - gammaln(k + 1.0)
    pmf: NDArray[np.float64] = np.exp(log_pmf)
    return pmf
