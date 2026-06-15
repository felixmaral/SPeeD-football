"""Interfaz `LeaguePlugin` y registry de ligas.

Cada liga (Mundial, LaLiga, …) implementa `LeaguePlugin`. Añadir una liga = crear
un plugin y registrarlo; el dominio no sabe qué liga es.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class LeaguePlugin(ABC):
    """Contrato que toda competición debe implementar."""

    @property
    @abstractmethod
    def league_id(self) -> int:
        """Identificador de la liga en la fuente de datos (p.ej. API-Football)."""
        raise NotImplementedError

    @property
    @abstractmethod
    def name(self) -> str:
        """Nombre legible de la competición."""
        raise NotImplementedError

    @abstractmethod
    def is_knockout(self, stage: str) -> bool:
        """Indica si una fase dada es eliminatoria (vs. liguilla/grupos)."""
        raise NotImplementedError

    @abstractmethod
    def ratings_namespace(self) -> str:
        """Namespace bajo el que se guardan los ratings de esta liga."""
        raise NotImplementedError

    @property
    def neutral_venue(self) -> bool:
        """Si los partidos se juegan en sede neutral (sin ventaja de local real).

        Por defecto False (ligas de clubes con local/visitante). Las competiciones
        a partido único en sede neutral (p.ej. Mundial) deben devolver True.
        """
        return False


class LeagueRegistry:
    """Registro de plugins de liga, indexado por `league_id`."""

    def __init__(self) -> None:
        self._by_id: dict[int, LeaguePlugin] = {}

    def register(self, plugin: LeaguePlugin) -> None:
        """Registra un plugin. Falla si ya hay uno con el mismo `league_id`."""
        if plugin.league_id in self._by_id:
            raise ValueError(f"Liga ya registrada: id={plugin.league_id}")
        self._by_id[plugin.league_id] = plugin

    def get(self, league_id: int) -> LeaguePlugin:
        """Devuelve el plugin por id, o lanza `KeyError` si no existe."""
        try:
            return self._by_id[league_id]
        except KeyError:
            raise KeyError(f"Liga no registrada: id={league_id}") from None

    def get_by_name(self, name: str) -> LeaguePlugin:
        """Devuelve el plugin cuyo nombre coincide (case-insensitive)."""
        for plugin in self._by_id.values():
            if plugin.name.lower() == name.lower():
                return plugin
        raise KeyError(f"Liga no registrada: name={name!r}")

    def all(self) -> tuple[LeaguePlugin, ...]:
        """Devuelve todos los plugins registrados."""
        return tuple(self._by_id.values())
