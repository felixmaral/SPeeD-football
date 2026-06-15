"""Caso de uso: predecir los partidos de hoy de la liga activa."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field, replace
from datetime import date

from wcpredictor.application.ports.fixture_repo import FixtureRepository
from wcpredictor.application.ports.ratings_repo import RatingsRepository
from wcpredictor.application.ports.recent_results_repo import (
    RecentResultsRepository,
    TeamMatchResult,
)
from wcpredictor.domain.entities.match import Match
from wcpredictor.domain.entities.team import Team
from wcpredictor.domain.services.form import FormAdjuster, RecentResult
from wcpredictor.domain.services.predictor import MatchPrediction, Predictor
from wcpredictor.infrastructure.leagues.base import LeaguePlugin


def _today() -> date:
    return date.today()


@dataclass(frozen=True, slots=True)
class StageProbabilities:
    """Probabilidades 1X2 y goles esperados en una etapa del cálculo."""

    label: str
    home_win: float
    draw: float
    away_win: float
    lambda_home: float
    lambda_away: float


@dataclass(frozen=True, slots=True)
class ExplainedPrediction:
    """Predicción final más el desglose por variable (etapas)."""

    prediction: MatchPrediction
    stages: list[StageProbabilities]


@dataclass(frozen=True, slots=True)
class PredictTodayMatches:
    """Orquesta la predicción de todos los partidos de hoy de una liga.

    Es un adaptador de aplicación: combina los puertos (fixtures, ratings, forma
    reciente), el plugin de liga y el servicio de dominio `Predictor`, sin lógica
    estadística propia.

    Si se proporciona `recent_results_repo` (+ `form_adjuster` + `season`), la fuerza
    de cada equipo se ajusta por su forma reciente antes de predecir. Si no, el
    comportamiento es el de la beta (solo ratings entrenados).
    """

    fixture_repo: FixtureRepository
    ratings_repo: RatingsRepository
    league: LeaguePlugin
    predictor: Predictor = field(default_factory=Predictor)
    clock: Callable[[], date] = _today
    recent_results_repo: RecentResultsRepository | None = None
    form_adjuster: FormAdjuster = field(default_factory=FormAdjuster)
    recent_limit: int = 8
    # H2H: muestra pequeña -> baja sensibilidad, half-life largo y poca confianza.
    h2h_adjuster: FormAdjuster = field(
        default_factory=lambda: FormAdjuster(
            sensitivity=0.25, half_life_days=1095.0, confidence=3.0
        )
    )
    h2h_limit: int = 5

    async def execute(self, day: date | None = None) -> list[MatchPrediction]:
        """Devuelve las predicciones de los partidos de `day` (hoy por defecto)."""
        target = day or self.clock()
        matches = await self.fixture_repo.get_fixtures_for_date(target, self.league.league_id)

        predictions: list[MatchPrediction] = []
        for match in matches:
            enriched = self._enrich(match)
            enriched = await self._apply_form(enriched, target)
            enriched = await self._apply_h2h(enriched, target)
            lineup = await self.fixture_repo.get_lineup_availability(match.id)
            predictions.append(self.predictor.predict(enriched, lineup.players))
        return predictions

    async def execute_explained(self, day: date | None = None) -> list[ExplainedPrediction]:
        """Como `execute`, pero adjunta el desglose por etapas (Base → + Forma)."""
        target = day or self.clock()
        matches = await self.fixture_repo.get_fixtures_for_date(target, self.league.league_id)

        out: list[ExplainedPrediction] = []
        for match in matches:
            base = self._enrich(match)
            stages = [self._stage("Base (ratings)", base)]
            formed = await self._apply_form(base, target)
            if self.recent_results_repo is not None:
                stages.append(self._stage("+ Forma reciente", formed))
            with_h2h = await self._apply_h2h(formed, target)
            if self.recent_results_repo is not None:
                stages.append(self._stage("+ H2H", with_h2h))
            lineup = await self.fixture_repo.get_lineup_availability(match.id)
            prediction = self.predictor.predict(with_h2h, lineup.players)
            out.append(ExplainedPrediction(prediction=prediction, stages=stages))
        return out

    def _stage(self, label: str, match: Match) -> StageProbabilities:
        p = self.predictor.predict(match).probabilities
        return StageProbabilities(
            label=label,
            home_win=p.home_win,
            draw=p.draw,
            away_win=p.away_win,
            lambda_home=p.lambda_home,
            lambda_away=p.lambda_away,
        )

    def _enrich(self, match: Match) -> Match:
        """Aplica los ratings entrenados a los equipos del partido (por nombre)."""
        home = self._rated(match.home)
        away = self._rated(match.away)
        return replace(match, home=home, away=away)

    def _rated(self, team: Team) -> Team:
        rating = self.ratings_repo.get_rating(self.league.ratings_namespace(), team.name)
        if rating is None:
            return team
        return replace(team, attack=rating.attack, defense=rating.defense)

    async def _apply_form(self, match: Match, as_of: date) -> Match:
        """Ajusta la fuerza de cada equipo por su forma reciente, si está configurado."""
        if self.recent_results_repo is None:
            return match
        home = await self._form_for(match.home, as_of)
        away = await self._form_for(match.away, as_of)
        return replace(match, home=home, away=away)

    async def _apply_h2h(self, match: Match, as_of: date) -> Match:
        """Ajusta cada equipo por su historial directo frente al rival concreto."""
        if self.recent_results_repo is None:
            return match
        home = await self._h2h_for(match.home, match.away, as_of)
        away = await self._h2h_for(match.away, match.home, as_of)
        return replace(match, home=home, away=away)

    async def _h2h_for(self, team: Team, opponent: Team, as_of: date) -> Team:
        assert self.recent_results_repo is not None
        raw = await self.recent_results_repo.get_head_to_head(
            team.name, opponent.name, self.h2h_limit
        )
        results = [
            RecentResult(
                when=r.when,
                goals_for=r.goals_for,
                goals_against=r.goals_against,
                opponent_attack=opponent.attack,
                opponent_defense=opponent.defense,
            )
            for r in raw
        ]
        return self.h2h_adjuster.adjust(team, results, as_of)

    async def _form_for(self, team: Team, as_of: date) -> Team:
        assert self.recent_results_repo is not None
        raw = await self.recent_results_repo.get_recent_results(team.name, self.recent_limit)
        results = [self._to_recent(r) for r in raw]
        return self.form_adjuster.adjust(team, results, as_of)

    def _to_recent(self, result: TeamMatchResult) -> RecentResult:
        """Convierte un resultado en crudo en `RecentResult` con la fuerza del rival."""
        opp = self.ratings_repo.get_rating(self.league.ratings_namespace(), result.opponent_name)
        opp_attack = opp.attack if opp is not None else 1.0
        opp_defense = opp.defense if opp is not None else 1.0
        return RecentResult(
            when=result.when,
            goals_for=result.goals_for,
            goals_against=result.goals_against,
            opponent_attack=opp_attack,
            opponent_defense=opp_defense,
        )
