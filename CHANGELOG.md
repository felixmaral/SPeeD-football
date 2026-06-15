# Changelog

Todos los cambios notables de este proyecto se documentan aquí, siguiendo
[Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y
[Versionado Semántico](https://semver.org/lang/es/).

## [Unreleased]

## [0.1.0-beta.1] - 2026-06-15

### Added
- Arquitectura hexagonal (dominio puro, puertos, adaptadores, delivery).
- Modelos de dominio: Dixon-Coles (resultado) como base del v0; tarjetas y rendimiento
  (xG/posesión) implementados pero **fuera de la salida del v0** (para versiones futuras).
- Ajuste por disponibilidad de jugadores y servicios Explainer/Predictor.
- Puertos `FixtureRepository`, `RatingsRepository`, `Notifier` y plugin de liga.
- Adaptadores: API-Football (httpx + retries), mock de fixtures, ratings JSON,
  notificador de consola; plugin de liga del Mundial.
- Caso de uso `PredictTodayMatches` y lanzador por CLI con `--date`.
- Configuración vía pydantic-settings con fallback a mock.
- Entrenamiento de ratings (`scripts/train_ratings.py`) desde **todos los partidos
  internacionales** (martj42): MLE Poisson ponderado por **recencia × importancia del
  torneo** y campo neutral, sobre un grafo de rivales conectado entre confederaciones
  (fuerza de calendario); identidad por nombre con alias entre fuentes; calibración por
  shrinkage/recorte. Ver `docs/RATINGS.md`.
- Salida v0 coherente: una sola cifra de goles esperados (λ Dixon-Coles), sin mostrar
  nunca `0.0%`.
- CI (ruff + mypy strict + pytest, cobertura de dominio ≥80%).

[Unreleased]: https://github.com/felixmaral/speed-world-cup/compare/v0.1.0-beta.1...HEAD
[0.1.0-beta.1]: https://github.com/felixmaral/speed-world-cup/releases/tag/v0.1.0-beta.1
