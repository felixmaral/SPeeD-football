"""Configuración de la aplicación (pydantic-settings).

Lee variables de entorno y `.env`. No contiene secretos; estos llegan por entorno.
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Ajustes de ejecución de wcpredictor."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Modo de ejecución.
    use_mock: bool = Field(default=True, alias="WCPREDICTOR_USE_MOCK")

    # API-Football.
    api_football_key: str = Field(default="", alias="API_FOOTBALL_KEY")
    api_football_base_url: str = Field(
        default="https://v3.football.api-sports.io", alias="API_FOOTBALL_BASE_URL"
    )

    # Telegram (fase v1.0).
    telegram_bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")
    telegram_allowed_user_ids: str = Field(default="", alias="TELEGRAM_ALLOWED_USER_IDS")

    # General.
    log_level: str = Field(default="INFO", alias="WCPREDICTOR_LOG_LEVEL")
    timezone: str = Field(default="Europe/Madrid", alias="WCPREDICTOR_TIMEZONE")

    @property
    def effective_use_mock(self) -> bool:
        """Usa mock si se pide explícitamente o si falta la API key."""
        return self.use_mock or not self.api_football_key

    @property
    def allowed_user_ids(self) -> tuple[int, ...]:
        """IDs de Telegram autorizados, parseados desde la lista separada por comas."""
        return tuple(
            int(part) for part in self.telegram_allowed_user_ids.split(",") if part.strip()
        )
