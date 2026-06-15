"""Repositorio de ratings basado en ficheros JSON por namespace de liga.

Estructura esperada de `data/ratings/{namespace}.json`:

    [
        {"team_id": 9, "attack": 1.6, "defense": 0.7},
        ...
    ]
"""

from __future__ import annotations

import json
from pathlib import Path

from wcpredictor.application.ports.ratings_repo import RatingsRepository, TeamRating


class JsonRatingsRepository(RatingsRepository):
    """Lee ratings de equipos desde JSON, cacheando por namespace."""

    def __init__(self, base_dir: str | Path) -> None:
        self._base_dir = Path(base_dir)
        self._cache: dict[str, dict[int, TeamRating]] = {}

    def get_all(self, namespace: str) -> dict[int, TeamRating]:
        if namespace in self._cache:
            return self._cache[namespace]

        path = self._base_dir / f"{namespace}.json"
        ratings: dict[int, TeamRating] = {}
        if path.is_file():
            raw = json.loads(path.read_text(encoding="utf-8"))
            for item in raw:
                rating = TeamRating(
                    team_id=int(item["team_id"]),
                    attack=float(item["attack"]),
                    defense=float(item["defense"]),
                )
                ratings[rating.team_id] = rating

        self._cache[namespace] = ratings
        return ratings

    def get_team_rating(self, namespace: str, team_id: int) -> TeamRating | None:
        return self.get_all(namespace).get(team_id)
