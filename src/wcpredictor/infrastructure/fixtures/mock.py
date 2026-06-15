"""Adaptador mock de fixtures para desarrollo/CI sin red ni API key.

Permite inyectar datos propios o usar un conjunto por defecto de partidos del
Mundial generados para la fecha consultada (para que el lanzador funcione offline).
"""

from __future__ import annotations

from datetime import UTC, date, datetime, time

from wcpredictor.application.ports.fixture_repo import FixtureRepository, LineupInfo
from wcpredictor.domain.entities.match import Match, MatchStatus
from wcpredictor.domain.entities.player import Player, Position
from wcpredictor.domain.entities.referee import Referee
from wcpredictor.domain.entities.team import Team
from wcpredictor.infrastructure.leagues.world_cup import WORLD_CUP_LEAGUE_ID

# (home_name, away_name, hour). Los equipos se crean con fuerza neutra (1.0/1.0);
# los ratings reales los aplica el caso de uso por nombre. Así no se mezclan escalas.
_SAMPLE = [
    ("Spain", "Cape Verde Islands", 16),
    ("Belgium", "Egypt", 19),
    ("Saudi Arabia", "Uruguay", 22),
]


def default_world_cup_fixtures(day: date) -> list[Match]:
    """Genera los partidos de muestra del Mundial para `day`."""
    matches: list[Match] = []
    for i, (h, a, hour) in enumerate(_SAMPLE, start=1):
        matches.append(
            Match(
                id=i,
                home=Team(id=i * 2 - 1, name=h),
                away=Team(id=i * 2, name=a),
                kickoff=datetime.combine(day, time(hour, 0), tzinfo=UTC),
                league_id=WORLD_CUP_LEAGUE_ID,
                referee=Referee(id=100 + i, name=f"Referee {i}", strictness=1.0 + 0.1 * i),
                status=MatchStatus.SCHEDULED,
            )
        )
    return matches


def _default_lineup(team_id: int) -> LineupInfo:
    players = (
        Player(id=team_id * 100 + 1, name="GK", team_id=team_id, position=Position.GK),
        Player(id=team_id * 100 + 2, name="DF", team_id=team_id, position=Position.DEF),
        Player(id=team_id * 100 + 3, name="FW", team_id=team_id, position=Position.FWD),
    )
    return LineupInfo(confirmed=True, players=players)


class MockFixtureRepository(FixtureRepository):
    """Repositorio de fixtures en memoria."""

    def __init__(
        self,
        fixtures: dict[date, list[Match]] | None = None,
        lineups: dict[int, LineupInfo] | None = None,
    ) -> None:
        self._fixtures = fixtures
        self._lineups = lineups or {}

    async def get_fixtures_for_date(self, day: date, league_id: int) -> list[Match]:
        if self._fixtures is not None:
            matches = self._fixtures.get(day, [])
        else:
            matches = default_world_cup_fixtures(day)
        return [m for m in matches if m.league_id == league_id]

    async def get_lineup_availability(self, fixture_id: int) -> LineupInfo:
        if fixture_id in self._lineups:
            return self._lineups[fixture_id]
        if self._fixtures is None:
            # Datos por defecto: alineación confirmada de muestra.
            return _default_lineup(fixture_id)
        return LineupInfo(confirmed=False)
