"""Servicio Predictor: orquesta los modelos del dominio para predecir un partido."""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from dataclasses import dataclass, field

from wcpredictor.domain.entities.match import Match
from wcpredictor.domain.entities.player import Player
from wcpredictor.domain.models.cards import CardsModel, CardsPrediction
from wcpredictor.domain.models.dixon_coles import DixonColesModel, MatchProbabilities
from wcpredictor.domain.models.performance import MatchPerformance, PerformanceModel
from wcpredictor.domain.services.availability import AvailabilityAdjuster
from wcpredictor.domain.services.explainer import Explainer


@dataclass(frozen=True, slots=True)
class MatchPrediction:
    """Predicción completa y explicada de un partido.

    `version` es un identificador estable derivado del partido y de la alineación
    usada: con la misma disponibilidad produce la misma versión (idempotencia para
    el refresco por alineaciones). `confirmed` distingue preliminar de confirmada.
    """

    match_id: int
    probabilities: MatchProbabilities
    cards: CardsPrediction
    performance: MatchPerformance
    report: str
    confirmed: bool
    version: str


@dataclass(frozen=True, slots=True)
class Predictor:
    """Orquesta el ajuste por disponibilidad y los modelos estadísticos."""

    dixon_coles: DixonColesModel = field(default_factory=DixonColesModel)
    cards_model: CardsModel = field(default_factory=CardsModel)
    performance_model: PerformanceModel = field(default_factory=PerformanceModel)
    availability: AvailabilityAdjuster = field(default_factory=AvailabilityAdjuster)
    explainer: Explainer = field(default_factory=Explainer)

    def predict(
        self,
        match: Match,
        players: Sequence[Player] = (),
        aggression: float = 1.0,
    ) -> MatchPrediction:
        """Predice el partido, ajustando por las bajas presentes en `players`."""
        home = self.availability.adjust(match.home, players)
        away = self.availability.adjust(match.away, players)

        probabilities = self.dixon_coles.predict(home, away)
        cards = self.cards_model.predict(
            referee=match.referee, aggression=aggression, players=players
        )
        performance = self.performance_model.predict(home, away)
        report = self.explainer.explain(match, probabilities, cards, performance)

        return MatchPrediction(
            match_id=match.id,
            probabilities=probabilities,
            cards=cards,
            performance=performance,
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
