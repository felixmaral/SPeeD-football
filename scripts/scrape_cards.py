"""Genera el JSON de tarjetas/faltas por equipo desde FBref (offline).

La app NO scrapea: este script (con el extra `scrape`) descarga las estadísticas
"misc" de FBref y vuelca un JSON que el repositorio de tarjetas consumirá. Se puede
re-ejecutar por jornada para mantenerlo actualizado.

Uso:
    pip install -e ".[scrape]"
    python scripts/scrape_cards.py --league "ESP-La Liga" --season 2526 \
        --namespace la_liga --out data/cards/la_liga.json
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any


def build_cards_payload(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Transforma filas crudas (por equipo) en el payload de tarjetas.

    Cada fila: team, matches, yellow, red, fouls_committed, fouls_drawn.
    Devuelve por equipo las medias por partido y la `tendency` de tarjetas relativa a
    la media de la liga (≈1.0 = media; >1 más tarjetero).
    """
    teams = []
    for r in rows:
        matches = max(float(r["matches"]), 1e-9)
        bookings = float(r["yellow"]) + float(r["red"])
        teams.append(
            {
                "team": str(r["team"]),
                "cards_per_match": round(bookings / matches, 3),
                "fouls_committed_per_match": round(float(r["fouls_committed"]) / matches, 3),
                "fouls_drawn_per_match": round(float(r["fouls_drawn"]) / matches, 3),
            }
        )

    league_avg = sum(t["cards_per_match"] for t in teams) / max(len(teams), 1)
    league_avg = league_avg or 1.0
    for t in teams:
        t["tendency"] = round(t["cards_per_match"] / league_avg, 3)
    return sorted(teams, key=lambda t: t["tendency"], reverse=True)


def _scrape_rows(league: str, season: str) -> list[dict[str, Any]]:
    import soccerdata as sd

    fb = sd.FBref(league, season)
    df = fb.read_team_season_stats(stat_type="misc").reset_index()
    rows: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        rows.append(
            {
                "team": row[("team", "")] if ("team", "") in df.columns else row["team"],
                "matches": float(row[("90s", "")]),
                "yellow": float(row[("Performance", "CrdY")]),
                "red": float(row[("Performance", "CrdR")]),
                "fouls_committed": float(row[("Performance", "Fls")]),
                "fouls_drawn": float(row[("Performance", "Fld")]),
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrapea tarjetas de FBref a JSON.")
    parser.add_argument("--league", default="ESP-La Liga")
    parser.add_argument("--season", default="2526")
    parser.add_argument("--out", default="data/cards/la_liga.json")
    args = parser.parse_args()

    import truststore

    truststore.inject_into_ssl()

    rows = _scrape_rows(args.league, args.season)
    payload = build_cards_payload(rows)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"{len(payload)} equipos -> {out}")
    for t in payload[:5]:
        print(
            f"  {t['team']:<18} cards/match={t['cards_per_match']:.2f} tendency={t['tendency']:.2f}"
        )


if __name__ == "__main__":
    main()
