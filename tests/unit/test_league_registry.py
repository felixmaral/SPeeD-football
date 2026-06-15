"""Tests de la interfaz LeaguePlugin y el registry."""

import pytest

from wcpredictor.infrastructure.leagues.base import LeaguePlugin, LeagueRegistry


class _FakeLeague(LeaguePlugin):
    def __init__(self, league_id: int, name: str) -> None:
        self._id = league_id
        self._name = name

    @property
    def league_id(self) -> int:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    def is_knockout(self, stage: str) -> bool:
        return "final" in stage.lower()

    def ratings_namespace(self) -> str:
        return f"league-{self._id}"


def test_plugin_is_abstract() -> None:
    with pytest.raises(TypeError):
        LeaguePlugin()  # type: ignore[abstract]


def test_register_and_get() -> None:
    reg = LeagueRegistry()
    wc = _FakeLeague(1, "World Cup")
    reg.register(wc)
    assert reg.get(1) is wc
    assert reg.get_by_name("world cup") is wc
    assert reg.all() == (wc,)


def test_duplicate_registration_fails() -> None:
    reg = LeagueRegistry()
    reg.register(_FakeLeague(1, "World Cup"))
    with pytest.raises(ValueError, match="ya registrada"):
        reg.register(_FakeLeague(1, "Otra"))


def test_missing_lookups_raise() -> None:
    reg = LeagueRegistry()
    with pytest.raises(KeyError):
        reg.get(99)
    with pytest.raises(KeyError):
        reg.get_by_name("nope")


def test_is_knockout_and_namespace() -> None:
    wc = _FakeLeague(1, "World Cup")
    assert wc.is_knockout("Final") is True
    assert wc.is_knockout("Group Stage") is False
    assert wc.ratings_namespace() == "league-1"
