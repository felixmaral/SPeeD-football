"""Caso de uso: predecir los partidos de hoy de la liga activa."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field, replace
from datetime import date

from wcpredictor.application.ports.fixture_repo import FixtureRepository
from wcpredictor.application.ports.ratings_repo import RatingsRepository
from wcpredictor.domain.entities.match import Match
from wcpredictor.domain.services.predictor import MatchPrediction, Predictor
from wcpredictor.infrastructure.leagues.base import LeaguePlugin


def _today() -> date:
    return date.today()


@dataclass(frozen=True, slots=True)
class PredictTodayMatches:
    """Orquesta la predicción de todos los partidos de hoy de una liga.

    Es un adaptador de aplicación: combina los puertos (fixtures, ratings), el
    plugin de liga y el servicio de dominio `Predictor`, sin lógica estadística
    propia.
    """

    fixture_repo: FixtureRepository
    ratings_repo: RatingsRepository
    league: LeaguePlugin
    predictor: Predictor = field(default_factory=Predictor)
    clock: Callable[[], date] = _today

    async def execute(self, day: date | None = None) -> list[MatchPrediction]:
        """Devuelve las predicciones de los partidos de `day` (hoy por defecto)."""
        target = day or self.clock()
        matches = await self.fixture_repo.get_fixtures_for_date(target, self.league.league_id)

        predictions: list[MatchPrediction] = []
        for match in matches:
            enriched = self._enrich(match)
            lineup = await self.fixture_repo.get_lineup_availability(match.id)
            predictions.append(self.predictor.predict(enriched, lineup.players))
        return predictions

    def _enrich(self, match: Match) -> Match:
        """Aplica los ratings entrenados a los equipos del partido."""
        namespace = self.league.ratings_namespace()
        home, away = match.home, match.away
        rh = self.ratings_repo.get_team_rating(namespace, home.id)
        ra = self.ratings_repo.get_team_rating(namespace, away.id)
        if rh is not None:
            home = replace(home, attack=rh.attack, defense=rh.defense)
        if ra is not None:
            away = replace(away, attack=ra.attack, defense=ra.defense)
        return replace(match, home=home, away=away)
