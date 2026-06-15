"""Puerto de salida: notificador de predicciones."""

from __future__ import annotations

from abc import ABC, abstractmethod


class Notifier(ABC):
    """Canal de salida de predicciones (consola en beta, Telegram en v1.0, …)."""

    @abstractmethod
    async def send_prediction(self, user_id: str, report: str) -> None:
        """Envía un informe de predicción a un destinatario."""
        raise NotImplementedError
