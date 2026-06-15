"""Repositorio de ratings basado en ficheros JSON por namespace de liga.

Estructura esperada de `data/ratings/{namespace}.json`:

    [
        {"team": "Spain", "attack": 1.62, "defense": 0.70},
        ...
    ]

La identidad es por nombre de equipo (case-insensitive).
"""

from __future__ import annotations

import json
from pathlib import Path

from wcpredictor.application.ports.ratings_repo import RatingsRepository, TeamRating
from wcpredictor.infrastructure.names import normalize_team_name as _normalize


class JsonRatingsRepository(RatingsRepository):
    """Lee ratings de equipos desde JSON, cacheando por namespace."""

    def __init__(self, base_dir: str | Path) -> None:
        self._base_dir = Path(base_dir)
        self._cache: dict[str, dict[str, TeamRating]] = {}

    def get_all(self, namespace: str) -> dict[str, TeamRating]:
        if namespace in self._cache:
            return self._cache[namespace]

        path = self._base_dir / f"{namespace}.json"
        ratings: dict[str, TeamRating] = {}
        if path.is_file():
            raw = json.loads(path.read_text(encoding="utf-8"))
            for item in raw:
                rating = TeamRating(
                    team=str(item["team"]),
                    attack=float(item["attack"]),
                    defense=float(item["defense"]),
                )
                ratings[_normalize(rating.team)] = rating

        self._cache[namespace] = ratings
        return ratings

    def get_rating(self, namespace: str, team_name: str) -> TeamRating | None:
        return self.get_all(namespace).get(_normalize(team_name))
