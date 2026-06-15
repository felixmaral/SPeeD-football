"""Tests del helper puro del pipeline de tarjetas (sin scraping)."""

import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "scrape_cards",
    Path(__file__).resolve().parents[2] / "scripts" / "scrape_cards.py",
)
assert _spec and _spec.loader
scrape_cards = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(scrape_cards)
build_cards_payload = scrape_cards.build_cards_payload


def _rows() -> list[dict[str, object]]:
    return [
        {
            "team": "Aggressive",
            "matches": 10,
            "yellow": 30,
            "red": 2,
            "fouls_committed": 150,
            "fouls_drawn": 100,
        },
        {
            "team": "Calm",
            "matches": 10,
            "yellow": 10,
            "red": 0,
            "fouls_committed": 90,
            "fouls_drawn": 110,
        },
    ]


def test_cards_per_match_and_means() -> None:
    payload = {t["team"]: t for t in build_cards_payload(_rows())}
    assert payload["Aggressive"]["cards_per_match"] == 3.2  # (30+2)/10
    assert payload["Calm"]["cards_per_match"] == 1.0
    assert payload["Aggressive"]["fouls_committed_per_match"] == 15.0
    assert payload["Calm"]["fouls_drawn_per_match"] == 11.0


def test_tendency_relative_to_league_average() -> None:
    payload = {t["team"]: t for t in build_cards_payload(_rows())}
    # media liga = (3.2 + 1.0)/2 = 2.1 -> Aggressive 3.2/2.1≈1.524, Calm 1.0/2.1≈0.476
    assert payload["Aggressive"]["tendency"] > 1.0
    assert payload["Calm"]["tendency"] < 1.0
    assert payload["Aggressive"]["tendency"] > payload["Calm"]["tendency"]


def test_sorted_by_tendency_desc() -> None:
    payload = build_cards_payload(_rows())
    assert payload[0]["team"] == "Aggressive"


def test_bundled_laliga_file_is_valid() -> None:
    import json

    path = Path(__file__).resolve().parents[2] / "data" / "cards" / "la_liga.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert len(data) >= 18
    assert all({"team", "cards_per_match", "tendency"} <= set(t) for t in data)
