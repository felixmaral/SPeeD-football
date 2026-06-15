"""Tests del caso de uso PredictTodayMatches."""

from datetime import date

from wcpredictor.application.ports.ratings_repo import RatingsRepository, TeamRating
from wcpredictor.application.use_cases.predict_today import PredictTodayMatches
from wcpredictor.infrastructure.fixtures.mock import MockFixtureRepository
from wcpredictor.infrastructure.leagues.world_cup import WorldCupLeague
from wcpredictor.infrastructure.ratings.json_repo import JsonRatingsRepository


class _RatingsStub(RatingsRepository):
    def __init__(self, ratings: dict[str, TeamRating]) -> None:
        self._r = ratings

    def get_rating(self, namespace: str, team_name: str) -> TeamRating | None:
        return self._r.get(team_name)

    def get_all(self, namespace: str) -> dict[str, TeamRating]:
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
    # El primer partido por defecto es Spain vs Cape Verde Islands.
    strong = _RatingsStub({"Spain": TeamRating(team="Spain", attack=3.0, defense=0.4)})
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


async def test_recent_form_changes_prediction() -> None:
    from wcpredictor.application.ports.recent_results_repo import TeamMatchResult
    from wcpredictor.infrastructure.fixtures.recent_results import MockRecentResultsRepository

    ratings = _RatingsStub(
        {
            "Spain": TeamRating(team="Spain", attack=1.3, defense=0.9),
            "Cape Verde Islands": TeamRating(team="Cape Verde Islands", attack=0.9, defense=1.2),
        }
    )
    # Spain (mock) llega con una gran racha reciente vs rival medio.
    recent = {
        "Spain": [
            TeamMatchResult(date(2026, 6, 12), 4, 0, "Rival"),
            TeamMatchResult(date(2026, 6, 8), 3, 0, "Rival"),
            TeamMatchResult(date(2026, 6, 4), 3, 1, "Rival"),
        ]
    }
    base = await _use_case(ratings).execute(date(2026, 6, 15))
    with_form = await PredictTodayMatches(
        fixture_repo=MockFixtureRepository(),
        ratings_repo=ratings,
        league=WorldCupLeague(),
        recent_results_repo=MockRecentResultsRepository(recent=recent),
        clock=lambda: date(2026, 6, 15),
    ).execute(date(2026, 6, 15))
    assert with_form[0].probabilities.home_win > base[0].probabilities.home_win


async def test_no_recent_repo_keeps_behaviour() -> None:
    ratings = _RatingsStub({"Spain": TeamRating(team="Spain", attack=1.3, defense=0.9)})
    a = await _use_case(ratings).execute(date(2026, 6, 15))
    b = await _use_case(ratings).execute(date(2026, 6, 15))
    assert a[0].probabilities.home_win == b[0].probabilities.home_win


async def test_h2h_changes_prediction() -> None:
    from datetime import date as _date

    from wcpredictor.application.ports.recent_results_repo import TeamMatchResult
    from wcpredictor.infrastructure.fixtures.recent_results import MockRecentResultsRepository

    ratings = _RatingsStub(
        {
            "Spain": TeamRating(team="Spain", attack=1.2, defense=1.0),
            "Cape Verde Islands": TeamRating(team="Cape Verde Islands", attack=1.0, defense=1.0),
        }
    )
    # Spain domina el historial directo (goleadas recientes al rival).
    h2h = {
        ("Spain", "Cape Verde Islands"): [
            TeamMatchResult(_date(2025, 9, 1), 4, 0, "Cape Verde Islands"),
            TeamMatchResult(_date(2024, 9, 1), 3, 0, "Cape Verde Islands"),
        ]
    }
    base = await _use_case(ratings).execute(_date(2026, 6, 15))
    with_h2h = await PredictTodayMatches(
        fixture_repo=MockFixtureRepository(),
        ratings_repo=ratings,
        league=WorldCupLeague(),
        recent_results_repo=MockRecentResultsRepository(h2h=h2h),
        clock=lambda: _date(2026, 6, 15),
    ).execute(_date(2026, 6, 15))
    assert with_h2h[0].probabilities.home_win > base[0].probabilities.home_win
