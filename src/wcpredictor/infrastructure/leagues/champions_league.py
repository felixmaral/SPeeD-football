"""Plugin de liga para la UEFA Champions League."""

from __future__ import annotations

from wcpredictor.infrastructure.leagues.base import LeaguePlugin

# Id de la Champions League en API-Football.
CHAMPIONS_LEAGUE_ID = 2

_KNOCKOUT_KEYWORDS = (
    "round of 16",
    "8th finals",
    "quarter",
    "semi",
    "final",
    "play-off",
    "knockout",
)


class ChampionsLeague(LeaguePlugin):
    """UEFA Champions League: fase de liga/grupos + eliminatorias."""

    @property
    def league_id(self) -> int:
        return CHAMPIONS_LEAGUE_ID

    @property
    def name(self) -> str:
        return "UEFA Champions League"

    def is_knockout(self, stage: str) -> bool:
        s = stage.lower()
        if "group" in s or "league phase" in s:
            return False
        return any(keyword in s for keyword in _KNOCKOUT_KEYWORDS)

    def ratings_namespace(self) -> str:
        return "champions_league"
