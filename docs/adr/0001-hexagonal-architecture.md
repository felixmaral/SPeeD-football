# ADR-001 — Arquitectura hexagonal (puertos y adaptadores)

- **Estado:** Aceptada
- **Fecha:** 2026-06-15
- **Decisores:** equipo wcpredictor

## Contexto

`wcpredictor` debe evolucionar en fases sin reescribir lo anterior:

1. **Canales de entrada distintos:** CLI (beta) → bot de Telegram (v1.0) → posible API REST.
2. **Refresco por alineaciones:** un scheduler que re-predice cuando se publican los onces (T−60/−30).
3. **Multi-liga:** Mundial (beta) → LaLiga (v2.0) → otras ligas como adaptadores.

El riesgo principal es acoplar la lógica de predicción (modelos estadísticos) a un canal
concreto o a una fuente de datos concreta, lo que obligaría a reescribir el núcleo en cada fase.

## Decisión

Adoptamos **arquitectura hexagonal (puertos y adaptadores)** con cuatro capas:

- **`domain/`** — núcleo puro: entidades (`Match`, `Team`, `Player`, `Referee`), modelos
  (`DixonColes`, `CardsModel`, `PerformanceModel`) y servicios (`Predictor`, `Explainer`).
  **Sin dependencias de I/O ni frameworks.**
- **`application/`** — casos de uso (`PredictTodayMatches`, `RefreshPredictionOnLineup`, …) y
  **puertos** (interfaces ABC: `FixtureRepository`, `RatingsRepository`, `Notifier`, `Scheduler`).
- **`infrastructure/`** — adaptadores concretos *driven* (API-Football, mocks, repos JSON,
  plugins de liga, APScheduler, notificadores).
- **`delivery/`** — adaptadores *driving* (CLI, bot de Telegram, futura API).

Reglas de dependencia: las dependencias **apuntan hacia el dominio**. El dominio no importa
nada de las capas externas; la aplicación define interfaces que la infraestructura implementa.

```
delivery ─▶ application ─▶ domain ◀─ infrastructure
                 │                        ▲
                 └────── puertos (ABC) ───┘
```

## Consecuencias

**Positivas**
- Añadir un canal (Telegram, API) = nuevo adaptador en `delivery/`, sin tocar el dominio.
- Añadir una liga = implementar `LeaguePlugin`, sin tocar el dominio.
- El dominio se testea sin red (cobertura ≥80% exigida en CI).
- Sustituibilidad: API real ↔ mock vía el mismo puerto.

**Negativas / coste**
- Más ficheros e indirección (interfaces ABC) que un diseño monolítico.
- Disciplina necesaria para no filtrar detalles de infraestructura al dominio.

## Alternativas consideradas

- **Monolito en capas simple:** menos boilerplate, pero acopla canal y datos al núcleo;
  rechazado por los 3 objetivos de evolución.
- **Microservicios:** sobredimensionado para el alcance actual.
