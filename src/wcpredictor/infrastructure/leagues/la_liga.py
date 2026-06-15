"""Plugin de liga para LaLiga (Primera División española)."""

from __future__ import annotations

from wcpredictor.infrastructure.leagues.base import LeaguePlugin

# Id de LaLiga en API-Football.
LA_LIGA_LEAGUE_ID = 140


class LaLigaLeague(LeaguePlugin):
    """LaLiga: liga doméstica de ida y vuelta (sin eliminatorias)."""

    @property
    def league_id(self) -> int:
        return LA_LIGA_LEAGUE_ID

    @property
    def name(self) -> str:
        return "La Liga"

    def is_knockout(self, stage: str) -> bool:
        return False

    def ratings_namespace(self) -> str:
        return "la_liga"
