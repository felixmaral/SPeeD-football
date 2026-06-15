"""Test end-to-end del lanzador en modo mock (sin red)."""

import pytest

from wcpredictor.delivery.cli.launcher import main


def test_launcher_runs_in_mock_mode(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("WCPREDICTOR_USE_MOCK", "true")
    exit_count = main(["--date", "2026-06-15"])
    out = capsys.readouterr().out

    assert exit_count == 3
    assert "Spain vs Cape Verde Islands" in out
    assert "Pronóstico:" in out
    assert "Resultado (1X2):" in out
    assert "Goles esperados:" in out
    assert "Over 2.5" in out


def test_launcher_default_date(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("WCPREDICTOR_USE_MOCK", "true")
    exit_count = main([])
    out = capsys.readouterr().out
    assert exit_count == 3
    assert "vs" in out
