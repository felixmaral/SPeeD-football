"""Servicio Predictor: orquesta el modelo de resultado para predecir un partido.

v0: predice resultado/marcador con Dixon-Coles tras ajustar la fuerza por la
disponibilidad de jugadores. Tarjetas y rendimiento quedan fuera del v0 (sus
modelos siguen en el código para futuras versiones).
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from dataclasses import dataclass, field

from wcpredictor.domain.entities.match import Match
from wcpredictor.domain.entities.player import Player
from wcpredictor.domain.models.dixon_coles import DixonColesModel, MatchProbabilities
from wcpredictor.domain.services.availability import AvailabilityAdjuster
from wcpredictor.domain.services.explainer import Explainer


@dataclass(frozen=True, slots=True)
class MatchPrediction:
    """Predicción explicada de un partido (v0: resultado/marcador).

    `version` es un identificador estable derivado del partido y de la alineación
    usada (idempotencia para el refresco por alineaciones). `confirmed` distingue
    preliminar de confirmada.
    """

    match_id: int
    probabilities: MatchProbabilities
    report: str
    confirmed: bool
    version: str


@dataclass(frozen=True, slots=True)
class Predictor:
    """Orquesta el ajuste por disponibilidad y el modelo de resultado."""

    dixon_coles: DixonColesModel = field(default_factory=DixonColesModel)
    availability: AvailabilityAdjuster = field(default_factory=AvailabilityAdjuster)
    explainer: Explainer = field(default_factory=Explainer)

    def predict(self, match: Match, players: Sequence[Player] = ()) -> MatchPrediction:
        """Predice el partido, ajustando por las bajas presentes en `players`."""
        home = self.availability.adjust(match.home, players)
        away = self.availability.adjust(match.away, players)

        probabilities = self.dixon_coles.predict(home, away)
        report = self.explainer.explain(match, probabilities)

        return MatchPrediction(
            match_id=match.id,
            probabilities=probabilities,
            report=report,
            confirmed=match.has_confirmed_lineup,
            version=self._version(match, players),
        )

    @staticmethod
    def _version(match: Match, players: Sequence[Player]) -> str:
        """Hash estable del partido + disponibilidad de la alineación."""
        availability = ",".join(
            f"{p.id}:{int(p.available)}" for p in sorted(players, key=lambda p: p.id)
        )
        payload = f"{match.id}|{match.status.value}|{availability}"
        return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]
