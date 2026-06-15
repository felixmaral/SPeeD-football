"""Plugin de liga para la Copa Mundial de la FIFA."""

from __future__ import annotations

from wcpredictor.infrastructure.leagues.base import LeaguePlugin

# Id de la competición "World Cup" en API-Football.
WORLD_CUP_LEAGUE_ID = 1

# Palabras clave que identifican una fase eliminatoria (case-insensitive).
_KNOCKOUT_KEYWORDS = (
    "round of 16",
    "8th finals",
    "quarter",
    "semi",
    "final",
    "3rd place",
    "third place",
)


class WorldCupLeague(LeaguePlugin):
    """Copa Mundial de la FIFA."""

    @property
    def league_id(self) -> int:
        return WORLD_CUP_LEAGUE_ID

    @property
    def name(self) -> str:
        return "World Cup"

    def is_knockout(self, stage: str) -> bool:
        s = stage.lower()
        if "group" in s:
            return False
        return any(keyword in s for keyword in _KNOCKOUT_KEYWORDS)

    def ratings_namespace(self) -> str:
        return "world_cup"

    @property
    def neutral_venue(self) -> bool:
        return True
