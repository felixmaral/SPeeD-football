"""Tests del repositorio JSON de ratings (identidad por nombre)."""

import json
from pathlib import Path

from wcpredictor.infrastructure.ratings.json_repo import JsonRatingsRepository


def _write(base: Path, namespace: str, data: list[dict[str, object]]) -> None:
    (base / f"{namespace}.json").write_text(json.dumps(data), encoding="utf-8")


def test_loads_ratings(tmp_path: Path) -> None:
    _write(tmp_path, "world_cup", [{"team": "Spain", "attack": 1.6, "defense": 0.7}])
    repo = JsonRatingsRepository(tmp_path)
    ratings = repo.get_all("world_cup")
    assert ratings["spain"].attack == 1.6
    assert ratings["spain"].defense == 0.7


def test_get_rating_case_insensitive(tmp_path: Path) -> None:
    _write(tmp_path, "world_cup", [{"team": "Spain", "attack": 1.6, "defense": 0.7}])
    repo = JsonRatingsRepository(tmp_path)
    assert repo.get_rating("world_cup", "SPAIN") is not None
    assert repo.get_rating("world_cup", "Narnia") is None


def test_missing_namespace_returns_empty(tmp_path: Path) -> None:
    repo = JsonRatingsRepository(tmp_path)
    assert repo.get_all("nope") == {}
    assert repo.get_rating("nope", "Spain") is None


def test_cache_avoids_reread(tmp_path: Path) -> None:
    _write(tmp_path, "world_cup", [{"team": "A", "attack": 1.0, "defense": 1.0}])
    repo = JsonRatingsRepository(tmp_path)
    first = repo.get_all("world_cup")
    _write(tmp_path, "world_cup", [{"team": "B", "attack": 2.0, "defense": 2.0}])
    assert repo.get_all("world_cup") is first


def test_bundled_world_cup_file_loads() -> None:
    data_dir = Path(__file__).resolve().parents[2] / "data" / "ratings"
    repo = JsonRatingsRepository(data_dir)
    ratings = repo.get_all("world_cup")
    assert len(ratings) >= 20
    assert repo.get_rating("world_cup", "France") is not None
    assert all(r.attack > 0 and r.defense > 0 for r in ratings.values())
