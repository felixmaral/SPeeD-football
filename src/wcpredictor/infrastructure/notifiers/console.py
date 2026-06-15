"""Notificador que escribe las predicciones por consola."""

from __future__ import annotations

import sys
from typing import TextIO

from wcpredictor.application.ports.notifier import Notifier


class ConsoleNotifier(Notifier):
    """Imprime los informes de predicción en un stream de texto (stdout por defecto)."""

    def __init__(self, stream: TextIO | None = None) -> None:
        self._stream = stream if stream is not None else sys.stdout

    async def send_prediction(self, user_id: str, report: str) -> None:
        self._stream.write(report)
        self._stream.write("\n\n" + "-" * 40 + "\n\n")
