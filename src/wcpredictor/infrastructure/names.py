"""Normalización de nombres de equipo entre fuentes de datos.

Las fuentes usan grafías distintas (la de fixtures vs. la de ratings/resultados). Esta
utilidad normaliza a una clave común (minúsculas + alias) para poder cruzarlas.
"""

from __future__ import annotations

# Clave y valor en minúsculas. Mapea grafías de la fuente de fixtures (API-Football)
# a las del dataset de resultados/ratings (martj42).
_ALIASES = {
    "cape verde islands": "cape verde",
    "korea republic": "south korea",
    "korea dpr": "north korea",
    "ir iran": "iran",
    "usa": "united states",
    "czechia": "czech republic",
    "côte d'ivoire": "ivory coast",
    "cote d'ivoire": "ivory coast",
    "china pr": "china",
    "turkey": "türkiye",
}


def normalize_team_name(name: str) -> str:
    """Devuelve la clave canónica de un nombre de equipo (minúsculas + alias)."""
    key = name.strip().lower()
    return _ALIASES.get(key, key)
