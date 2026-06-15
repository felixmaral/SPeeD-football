"""Tests del caso de uso PredictTodayMatches."""

from datetime import date

from wcpredictor.application.ports.ratings_repo import RatingsRepository, TeamRating
from wcpredictor.application.use_cases.predict_today import PredictTodayMatches
from wcpredictor.infrastructure.fixtures.mock import MockFixtureRepository
from wcpredictor.infrastructure.leagues.world_cup import WorldCupLeague
from wcpredictor.infrastructure.ratings.json_repo import JsonRatingsRepository


class _RatingsStub(RatingsRepository):
    def __init__(self, ratings: dict[int, TeamRating]) -> None:
        self._r = ratings

    def get_team_rating(self, namespace: str, team_id: int) -> TeamRating | None:
        return self._r.get(team_id)

    def get_all(self, namespace: str) -> dict[int, TeamRating]:
        return self._r


def _use_case(ratings: RatingsRepository) -> PredictTodayMatches:
    return PredictTodayMatches(
        fixture_repo=MockFixtureRepository(),
        ratings_repo=ratings,
        league=WorldCupLeague(),
        clock=lambda: date(2026, 6, 15),
    )


async def test_predicts_today_matches() -> None:
    uc = _use_case(_RatingsStub({}))
    predictions = await uc.execute()
    assert len(predictions) == 3
    assert all(p.report for p in predictions)


async def test_uses_explicit_day() -> None:
    uc = _use_case(_RatingsStub({}))
    predictions = await uc.execute(date(2026, 7, 1))
    assert len(predictions) == 3


async def test_ratings_enrichment_changes_strength() -> None:
    # El primer partido por defecto es Spain (team_id=1) vs Cape Verde (team_id=2).
    strong = _RatingsStub({1: TeamRating(team_id=1, attack=3.0, defense=0.4)})
    base = _RatingsStub({})
    p_strong = (await _use_case(strong).execute())[0]
    p_base = (await _use_case(base).execute())[0]
    assert p_strong.probabilities.home_win > p_base.probabilities.home_win


async def test_no_matches_returns_empty() -> None:
    uc = PredictTodayMatches(
        fixture_repo=MockFixtureRepository(fixtures={}),
        ratings_repo=_RatingsStub({}),
        league=WorldCupLeague(),
        clock=lambda: date(2026, 6, 15),
    )
    assert await uc.execute() == []


async def test_with_bundled_json_ratings() -> None:
    from pathlib import Path

    data_dir = Path(__file__).resolve().parents[2] / "data" / "ratings"
    uc = _use_case(JsonRatingsRepository(data_dir))
    predictions = await uc.execute()
    assert len(predictions) == 3
