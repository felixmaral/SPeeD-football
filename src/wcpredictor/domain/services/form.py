"""Ajuste dinámico de la fuerza de un equipo según su forma reciente.

La forma se mide como sobre/infra-rendimiento respecto a lo esperado **dado el rival**
(no es lo mismo golear a un débil que a un fuerte), ponderando cada partido por su
recencia (decaimiento exponencial). Es un servicio puro de dominio: los resultados los
proporciona un puerto en otra capa.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date

from wcpredictor.domain.entities.team import Team


@dataclass(frozen=True, slots=True)
class RecentResult:
    """Un resultado reciente del equipo frente a un rival con fuerza conocida."""

    when: date
    goals_for: int
    goals_against: int
    opponent_attack: float
    opponent_defense: float

    def __post_init__(self) -> None:
        if self.goals_for < 0 or self.goals_against < 0:
            raise ValueError("Los goles no pueden ser negativos")
        if self.opponent_attack <= 0 or self.opponent_defense <= 0:
            raise ValueError("Las fuerzas del rival deben ser > 0")


@dataclass(frozen=True, slots=True)
class FormAdjuster:
    """Ajusta `Team.attack`/`Team.defense` según la forma reciente.

    - `base_rate`: goles medios por equipo (misma escala que el modelo de resultado).
    - `half_life_days`: a mayor antigüedad, menos peso (peso 0.5 por cada half-life).
    - `sensitivity`: cuánto se traslada la forma al rating (0 = nada, 1 = directo).
    - `confidence`: peso (≈nº de partidos recientes) para efecto pleno; así un único
      partido —y más si es antiguo— mueve poco, y la recencia/volumen importan en
      términos absolutos.
    - `floor`/`ceil`: recorte de los multiplicadores resultantes.
    """

    base_rate: float = 1.35
    half_life_days: float = 180.0
    sensitivity: float = 0.5
    confidence: float = 5.0
    floor: float = 0.6
    ceil: float = 1.6

    def __post_init__(self) -> None:
        if self.base_rate <= 0:
            raise ValueError("base_rate debe ser > 0")
        if self.half_life_days <= 0:
            raise ValueError("half_life_days debe ser > 0")
        if self.sensitivity < 0:
            raise ValueError("sensitivity debe ser >= 0")
        if self.confidence <= 0:
            raise ValueError("confidence debe ser > 0")
        if not 0 < self.floor <= 1 <= self.ceil:
            raise ValueError("Debe cumplirse 0 < floor <= 1 <= ceil")

    def adjust(self, team: Team, results: Iterable[RecentResult], as_of: date) -> Team:
        """Devuelve un `Team` ajustado por la forma reciente (sin mutar el original)."""
        results = list(results)
        if not results:
            return team

        log_att = 0.0  # acumulado ponderado de log(rendimiento ofensivo)
        log_def = 0.0
        for r in results:
            age = max((as_of - r.when).days, 0)
            w = 0.5 ** (age / self.half_life_days)
            exp_for = self.base_rate * team.attack * r.opponent_defense
            exp_against = self.base_rate * r.opponent_attack * team.defense
            # +0.5 suaviza marcadores 0 (evita log(0)); ratio>1 => mejor de lo esperado.
            perf_att = (r.goals_for + 0.5) / (exp_for + 0.5)
            perf_def = (r.goals_against + 0.5) / (exp_against + 0.5)
            log_att += w * math.log(perf_att)
            log_def += w * math.log(perf_def)

        # Normalizar por una confianza fija (no por la suma de pesos): así un único
        # partido mueve poco y la recencia/volumen cuentan en términos absolutos.
        norm = max(self.confidence, 1e-9)
        att_form = math.exp(self.sensitivity * log_att / norm)
        def_form = math.exp(self.sensitivity * log_def / norm)

        attack = self._clip(team.attack * att_form, team.attack)
        # Mejor defensa = encajar menos de lo esperado (def_form < 1) => baja el rating.
        defense = self._clip(team.defense * def_form, team.defense)
        return Team(id=team.id, name=team.name, attack=attack, defense=defense)

    def _clip(self, value: float, base: float) -> float:
        return max(base * self.floor, min(base * self.ceil, value))
