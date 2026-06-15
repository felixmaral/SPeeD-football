# wcpredictor

Sistema de predicción estadística de fútbol con **arquitectura hexagonal** (puertos y
adaptadores). El núcleo de dominio es puro y testeable sin red; los canales de entrada
(CLI, Telegram, API) y las fuentes de datos (API-Football, mocks, ligas) son adaptadores
sustituibles.

> Roadmap completo y reglas de desarrollo en [`DEVELOPMENT_PLAN.md`](DEVELOPMENT_PLAN.md).

## Estado

| Fase | Entregable | Estado |
|------|-----------|--------|
| Beta | Lanzador CLI de predicciones del día | 🚧 en construcción |
| v1.0 | Bot de Telegram con allowlist | ⏳ |
| v1.1 | Refresco por alineaciones (T−60/−30) | ⏳ |
| v2.0 | Multi-liga (LaLiga +) | ⏳ |

## Arquitectura

Arquitectura **hexagonal (puertos y adaptadores)**. Las dependencias apuntan hacia el dominio:

```
delivery ─▶ application ─▶ domain ◀─ infrastructure
                 │                        ▲
                 └────── puertos (ABC) ───┘
```

- **domain** — núcleo puro (entidades, modelos estadísticos, servicios). Sin I/O ni frameworks.
- **application** — casos de uso + puertos (interfaces ABC).
- **infrastructure** — adaptadores *driven* (API-Football, mocks, repos, ligas, scheduler).
- **delivery** — adaptadores *driving* (CLI, bot, futura API).

Detalle y justificación en [ADR-001](docs/adr/0001-hexagonal-architecture.md)
(índice en [docs/adr/](docs/adr/README.md)).

## Estructura

```
src/wcpredictor/
├── domain/          # núcleo puro (entidades, modelos, servicios) — sin I/O
├── application/     # casos de uso + puertos (interfaces ABC)
├── infrastructure/  # adaptadores concretos (fixtures, ratings, leagues, ...)
├── delivery/        # puntos de entrada (CLI, bot)
└── config/          # settings (pydantic-settings)
```

## Uso (Beta)

```bash
# Modo mock (sin red ni API key)
WCPREDICTOR_USE_MOCK=true python -m wcpredictor.delivery.cli.launcher --date 2026-06-15

# Modo real (con API_FOOTBALL_KEY en .env)
wcpredictor                      # partidos de hoy
```

Guía completa en [docs/BETA.md](docs/BETA.md).

## Desarrollo

```bash
python -m venv .venv
source .venv/Scripts/activate   # Windows (Git Bash); .venv/bin/activate en Unix
pip install -e ".[dev]"
pytest
```

> El plan original especifica `uv`; este entorno usa `venv` + `pip` como equivalente.

## Licencia

MIT (privado, uso interno).
