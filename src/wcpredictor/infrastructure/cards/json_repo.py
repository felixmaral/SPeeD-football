"""Repositorio de tarjetas por equipo basado en JSON por namespace de liga.

Estructura de `data/cards/{namespace}.json` (generado por scripts/scrape_cards.py):

    [
        {"team": "Getafe", "cards_per_match": 3.08, "tendency": 1.31,
         "fouls_committed_per_match": 14.2, "fouls_drawn_per_match": 12.1},
        ...
    ]
"""

from __future__ import annotations

import json
from pathlib import Path

from wcpredictor.application.ports.cards_repo import CardsRepository, TeamCards
from wcpredictor.infrastructure.names import normalize_team_name as _normalize


class JsonCardsRepository(CardsRepository):
    """Lee estadísticas de tarjetas desde JSON, cacheando por namespace."""

    def __init__(self, base_dir: str | Path) -> None:
        self._base_dir = Path(base_dir)
        self._cache: dict[str, dict[str, TeamCards]] = {}

    def get_all(self, namespace: str) -> dict[str, TeamCards]:
        if namespace in self._cache:
            return self._cache[namespace]

        path = self._base_dir / f"{namespace}.json"
        cards: dict[str, TeamCards] = {}
        if path.is_file():
            raw = json.loads(path.read_text(encoding="utf-8"))
            for item in raw:
                tc = TeamCards(
                    team=str(item["team"]),
                    cards_per_match=float(item["cards_per_match"]),
                    tendency=float(item["tendency"]),
                    fouls_committed_per_match=float(item.get("fouls_committed_per_match", 0.0)),
                    fouls_drawn_per_match=float(item.get("fouls_drawn_per_match", 0.0)),
                )
                cards[_normalize(tc.team)] = tc

        self._cache[namespace] = cards
        return cards

    def get_team_cards(self, namespace: str, team_name: str) -> TeamCards | None:
        return self.get_all(namespace).get(_normalize(team_name))
