"""Tests de los adaptadores de resultados recientes / H2H (martj42 + mock)."""

from datetime import date

from wcpredictor.application.ports.recent_results_repo import TeamMatchResult
from wcpredictor.infrastructure.fixtures.recent_results import (
    Martj42RecentResultsRepository,
    MockRecentResultsRepository,
)

_CSV = """date,home_team,away_team,home_score,away_score,tournament,city,country,neutral
2026-06-08,Peru,Spain,1,3,Friendly,Lima,Peru,FALSE
2026-06-04,Spain,Iraq,1,1,Friendly,Madrid,Spain,FALSE
2025-11-18,Spain,Turkey,2,2,FIFA World Cup qualification,Madrid,Spain,FALSE
2024-03-26,Spain,Brazil,3,3,Friendly,Madrid,Spain,TRUE
2013-06-30,Brazil,Spain,3,0,Confederations Cup,Rio,Brazil,FALSE
2026-06-01,France,Germany,2,0,Friendly,Paris,France,FALSE
2099-01-01,Spain,Mars,NA,NA,Friendly,X,Y,FALSE
"""


def _repo() -> Martj42RecentResultsRepository:
    return Martj42RecentResultsRepository(csv_text=_CSV)


async def test_recent_results_team_perspective_and_order() -> None:
    res = await _repo().get_recent_results("Spain", limit=10)
    # Orden desc por fecha; se ignora la fila con score NA.
    assert [r.when for r in res][:2] == [date(2026, 6, 8), date(2026, 6, 4)]
    # Peru 1-3 Spain -> desde Spain: 3-1 vs Peru.
    assert res[0].goals_for == 3 and res[0].goals_against == 1
    assert res[0].opponent_name == "Peru"
    assert all(r.when.year != 2099 for r in res)  # NA descartado


async def test_recent_results_limit() -> None:
    res = await _repo().get_recent_results("Spain", limit=2)
    assert len(res) == 2


async def test_alias_matches_name() -> None:
    # "Türkiye" (alias de Turkey) debe encontrar el partido Spain-Turkey.
    res = await _repo().get_recent_results("Türkiye")
    assert any(r.opponent_name == "Spain" for r in res)


async def test_head_to_head_from_home_perspective() -> None:
    res = await _repo().get_head_to_head("Spain", "Brazil", limit=5)
    assert [r.when for r in res] == [date(2024, 3, 26), date(2013, 6, 30)]
    assert res[0].goals_for == 3 and res[0].goals_against == 3
    assert res[1].goals_for == 0 and res[1].goals_against == 3  # 2013: Spain visitante 0-3


async def test_mock_repository() -> None:
    recent = {"Spain": [TeamMatchResult(date(2026, 6, 1), 2, 0, "Italy")]}
    h2h = {("Spain", "Brazil"): [TeamMatchResult(date(2024, 3, 26), 3, 3, "Brazil")]}
    repo = MockRecentResultsRepository(recent=recent, h2h=h2h)
    assert (await repo.get_recent_results("Spain"))[0].opponent_name == "Italy"
    assert (await repo.get_head_to_head("Spain", "Brazil"))[0].goals_for == 3
    assert await repo.get_recent_results("Narnia") == []
