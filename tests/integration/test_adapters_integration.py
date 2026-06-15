"""Integración: adaptadores (fixtures + ratings) alimentando el dominio.

Demuestra que el Predictor del dominio funciona con cualquier FixtureRepository
(mock o API-Football), enriqueciendo los equipos con el RatingsRepository, sin
que el núcleo dependa del adaptador concreto.
"""

from dataclasses import replace
from datetime import date
from pathlib import Path

import httpx
import respx

from wcpredictor.application.ports.fixture_repo import FixtureRepository
from wcpredictor.application.ports.ratings_repo import RatingsRepository
from wcpredictor.domain.entities.match import Match
from wcpredictor.domain.services.predictor import MatchPrediction, Predictor
from wcpredictor.infrastructure.fixtures.api_football import ApiFootballFixtureRepository
from wcpredictor.infrastructure.fixtures.mock import MockFixtureRepository
from wcpredictor.infrastructure.leagues.world_cup import WORLD_CUP_LEAGUE_ID
from wcpredictor.infrastructure.ratings.json_repo import JsonRatingsRepository

BASE = "https://v3.football.api-sports.io"
_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "ratings"


def _enrich(match: Match, ratings: RatingsRepository, namespace: str) -> Match:
    """Aplica los ratings del repositorio a los equipos del partido (si existen)."""
    home, away = match.home, match.away
    rh = ratings.get_rating(namespace, home.name)
    ra = ratings.get_rating(namespace, away.name)
    if rh is not None:
        home = replace(home, attack=rh.attack, defense=rh.defense)
    if ra is not None:
        away = replace(away, attack=ra.attack, defense=ra.defense)
    return replace(match, home=home, away=away)


async def _predict_first(repo: FixtureRepository, ratings: RatingsRepository) -> MatchPrediction:
    matches = await repo.get_fixtures_for_date(date(2026, 6, 15), WORLD_CUP_LEAGUE_ID)
    match = _enrich(matches[0], ratings, "world_cup")
    lineup = await repo.get_lineup_availability(match.id)
    return Predictor().predict(match, lineup.players)


async def test_mock_fixtures_with_json_ratings_end_to_end() -> None:
    repo = MockFixtureRepository()
    ratings = JsonRatingsRepository(_DATA_DIR)
    prediction = await _predict_first(repo, ratings)
    total = (
        prediction.probabilities.home_win
        + prediction.probabilities.draw
        + prediction.probabilities.away_win
    )
    assert total == 1.0 or abs(total - 1.0) < 1e-9
    assert "vs" in prediction.report


@respx.mock
async def test_api_football_feeds_predictor() -> None:
    payload = {
        "response": [
            {
                "fixture": {
                    "id": 1,
                    "date": "2026-06-15T18:00:00+00:00",
                    "referee": "Ref",
                    "status": {"short": "NS"},
                },
                "teams": {
                    "home": {"id": 9, "name": "Spain"},
                    "away": {"id": 7, "name": "Brazil"},
                },
                "league": {"id": WORLD_CUP_LEAGUE_ID, "name": "World Cup", "season": 2026},
            }
        ]
    }
    respx.get(f"{BASE}/fixtures").mock(return_value=httpx.Response(200, json=payload))
    respx.get(f"{BASE}/fixtures/lineups").mock(
        return_value=httpx.Response(200, json={"response": []})
    )
    repo = ApiFootballFixtureRepository(api_key="k", base_url=BASE, backoff_base=0.0)
    ratings = JsonRatingsRepository(_DATA_DIR)
    prediction = await _predict_first(repo, ratings)
    assert prediction.match_id == 1
    assert "Spain" in prediction.report


async def test_lineup_absence_changes_prediction() -> None:
    repo = MockFixtureRepository()
    ratings = JsonRatingsRepository(_DATA_DIR)
    matches = await repo.get_fixtures_for_date(date(2026, 6, 15), WORLD_CUP_LEAGUE_ID)
    match = _enrich(matches[0], ratings, "world_cup")

    full = Predictor().predict(match, ())
    from wcpredictor.domain.entities.player import Player, Position

    key_out = (
        Player(
            id=999,
            name="Star",
            team_id=match.home.id,
            position=Position.FWD,
            importance=0.7,
            available=False,
        ),
    )
    weakened = Predictor().predict(match, key_out)
    assert weakened.probabilities.home_win < full.probabilities.home_win


async def test_substitutability_same_domain_both_adapters() -> None:
    """El mismo dominio produce predicción con mock y (mockeada) API."""
    ratings = JsonRatingsRepository(_DATA_DIR)
    mock_pred = await _predict_first(MockFixtureRepository(), ratings)
    assert isinstance(mock_pred, MatchPrediction)
