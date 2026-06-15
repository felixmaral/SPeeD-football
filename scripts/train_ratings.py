"""Entrena ratings de ataque/defensa por selección desde resultados internacionales.

Fuente: dataset abierto de **todos los partidos internacionales** (amistosos,
clasificatorios y torneos de todas las confederaciones), que mantiene el grafo de
rivales **conectado** entre continentes. Eso permite que el MLE normalice por el
nivel real del rival (fuerza de calendario) y evita inflar a dominadores de una
confederación con nivel medio más bajo.

Ajuste: Poisson bivariante por MLE con tres ponderaciones por partido:
- **recencia** (decaimiento exponencial): lo más cercano a hoy pesa más;
- **importancia del torneo**: un amistoso pesa menos que un clasificatorio o un Mundial;
- **campo neutral**: la ventaja de local solo se aplica si el partido no es neutral.
Más regularización L2 (shrinkage) hacia la media global.

Uso:
    python scripts/train_ratings.py [--out data/ratings/world_cup.json]
        [--since 2019-01-01] [--half-life-days 900]

Salida JSON: lista de {"team": <nombre>, "attack": <float>, "defense": <float>}.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
from datetime import date
from pathlib import Path

import httpx
import numpy as np
from numpy.typing import NDArray
from scipy.optimize import minimize

_URL = "https://raw.githubusercontent.com/martj42/international_results/master/results.csv"
_RIDGE = 0.5
_DEFAULT_SINCE = "2019-01-01"
_DEFAULT_HALF_LIFE_DAYS = 900.0
# Compresión del spread (shrinkage) y recorte de rango para fuerzas realistas:
# evita λ absurdas (8-0) y valores extremos en equipos con pocos datos.
_DEFAULT_SHRINK = 1.0
_CLIP_MIN, _CLIP_MAX = 0.30, 3.50

# Peso por importancia del partido (según la columna `tournament`). Subcadena en minúsculas.
_IMPORTANCE = {
    "fifa world cup qualification": 0.8,
    "fifa world cup": 1.0,
    "uefa euro qualification": 0.65,
    "uefa euro": 0.85,
    "copa américa": 0.85,
    "copa america": 0.85,
    "african cup of nations qualification": 0.55,
    "african cup of nations": 0.8,
    "afc asian cup qualification": 0.55,
    "afc asian cup": 0.8,
    "gold cup": 0.75,
    "uefa nations league": 0.7,
    "confederations cup": 0.75,
    "friendly": 0.3,
}
_DEFAULT_IMPORTANCE = 0.5

# (home, away, home_score, away_score, date, neutral, importance)
Game = tuple[str, str, int, int, date, bool, float]


def _importance(tournament: str) -> float:
    t = tournament.lower()
    for key, weight in _IMPORTANCE.items():
        if key in t:
            return weight
    return _DEFAULT_IMPORTANCE


def _download_games(since: date) -> list[Game]:
    text = httpx.get(_URL, timeout=120).text
    games: list[Game] = []
    for row in csv.DictReader(io.StringIO(text)):
        hs, as_ = row["home_score"], row["away_score"]
        if not hs.isdigit() or not as_.isdigit():
            continue
        match_date = date.fromisoformat(row["date"])
        if match_date < since:
            continue
        games.append(
            (
                row["home_team"],
                row["away_team"],
                int(hs),
                int(as_),
                match_date,
                row["neutral"].strip().lower() == "true",
                _importance(row["tournament"]),
            )
        )
    return games


def _fit(
    games: list[Game], half_life_days: float, shrink: float = _DEFAULT_SHRINK
) -> dict[str, tuple[float, float]]:
    teams = sorted({t for g in games for t in (g[0], g[1])})
    idx = {t: i for i, t in enumerate(teams)}
    n = len(teams)

    reference = max(g[4] for g in games)
    ages = np.array([(reference - g[4]).days for g in games], dtype=float)
    recency = 0.5 ** (ages / half_life_days)
    importance = np.array([g[6] for g in games], dtype=float)
    weights = recency * importance

    hi = np.array([idx[g[0]] for g in games])
    ai = np.array([idx[g[1]] for g in games])
    hs = np.array([g[2] for g in games], dtype=float)
    as_ = np.array([g[3] for g in games], dtype=float)
    not_neutral = np.array([0.0 if g[5] else 1.0 for g in games])

    avg_goals = float(np.average(hs + as_, weights=weights)) / 2.0
    log_base = np.log(avg_goals)

    def neg_log_lik(params: NDArray[np.float64]) -> float:
        atk = params[:n] - params[:n].mean()
        dfn = params[n : 2 * n]
        hadv = params[-1]
        lam_h = np.exp(log_base + hadv * not_neutral + atk[hi] - dfn[ai])
        lam_a = np.exp(log_base + atk[ai] - dfn[hi])
        ll = weights * (hs * np.log(lam_h) - lam_h + as_ * np.log(lam_a) - lam_a)
        penalty = _RIDGE * (np.sum(atk**2) + np.sum(dfn**2))
        return -float(ll.sum()) + penalty

    x0 = np.concatenate([np.zeros(n), np.zeros(n), [0.25]])
    res = minimize(neg_log_lik, x0, method="L-BFGS-B")
    # Centrar y comprimir el spread (shrinkage hacia la media) para escala realista.
    atk = (res.x[:n] - res.x[:n].mean()) * shrink
    dfn = (res.x[n : 2 * n] - res.x[n : 2 * n].mean()) * shrink

    ratings: dict[str, tuple[float, float]] = {}
    for t in teams:
        i = idx[t]
        attack = float(np.clip(np.exp(atk[i]), _CLIP_MIN, _CLIP_MAX))
        defense = float(np.clip(np.exp(-dfn[i]), _CLIP_MIN, _CLIP_MAX))
        ratings[t] = (round(attack, 3), round(defense, 3))
    return ratings


def main() -> None:
    parser = argparse.ArgumentParser(description="Entrena ratings internacionales.")
    parser.add_argument("--out", default="data/ratings/world_cup.json")
    parser.add_argument("--since", default=_DEFAULT_SINCE)
    parser.add_argument("--half-life-days", type=float, default=_DEFAULT_HALF_LIFE_DAYS)
    parser.add_argument("--shrink", type=float, default=_DEFAULT_SHRINK)
    args = parser.parse_args()

    games = _download_games(date.fromisoformat(args.since))
    ratings = _fit(games, args.half_life_days, args.shrink)
    payload = [
        {"team": team, "attack": atk, "defense": dfn}
        for team, (atk, dfn) in sorted(ratings.items())
    ]
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    top = sorted(ratings.items(), key=lambda kv: kv[1][0] / kv[1][1], reverse=True)[:12]
    print(f"{len(games)} partidos desde {args.since}, {len(ratings)} selecciones -> {out}")
    print("Top fuerza (attack/defense):")
    for team, (atk, dfn) in top:
        print(f"  {team:<18} atk={atk:.2f} def={dfn:.2f}")


if __name__ == "__main__":
    main()
