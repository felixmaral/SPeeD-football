"""Tests de la configuración (pydantic-settings)."""

import pytest

from wcpredictor.config.settings import Settings


def _settings() -> Settings:
    # _env_file=None evita leer el .env real del repo en los tests.
    return Settings(_env_file=None)  # type: ignore[call-arg]


def test_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in ("WCPREDICTOR_USE_MOCK", "API_FOOTBALL_KEY"):
        monkeypatch.delenv(var, raising=False)
    s = _settings()
    assert s.use_mock is True
    assert s.api_football_base_url.startswith("https://")
    assert s.effective_use_mock is True


def test_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WCPREDICTOR_USE_MOCK", "false")
    monkeypatch.setenv("API_FOOTBALL_KEY", "abc123")
    s = _settings()
    assert s.use_mock is False
    assert s.api_football_key == "abc123"
    assert s.effective_use_mock is False


def test_fallback_to_mock_without_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WCPREDICTOR_USE_MOCK", "false")
    monkeypatch.delenv("API_FOOTBALL_KEY", raising=False)
    s = _settings()
    assert s.use_mock is False
    # Sin key -> efectivamente mock.
    assert s.effective_use_mock is True


def test_allowed_user_ids_parsing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_ALLOWED_USER_IDS", "1, 2 ,3")
    s = _settings()
    assert s.allowed_user_ids == (1, 2, 3)


def test_allowed_user_ids_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TELEGRAM_ALLOWED_USER_IDS", raising=False)
    assert _settings().allowed_user_ids == ()
