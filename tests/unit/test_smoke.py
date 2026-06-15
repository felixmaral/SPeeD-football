"""Smoke test: el paquete y su núcleo de dominio se importan correctamente."""

import wcpredictor
import wcpredictor.domain


def test_package_exposes_version() -> None:
    assert isinstance(wcpredictor.__version__, str)
    assert wcpredictor.__version__


def test_domain_package_importable() -> None:
    assert wcpredictor.domain is not None
