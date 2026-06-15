# Diseño — Modelo avanzado basado en jugadores

> Objetivo: que la fuerza de un equipo en un partido se construya **de abajo arriba
> desde sus jugadores** (no de un Elo de club plano), con **Elo de jugador variable en
> el tiempo** y **estadísticas ponderadas por el nivel del rival**. Aplica a LaLiga y
> Champions. El Mundial se queda con el modelo actual (ratings + forma + H2H + neutral).

## 1. Principios

1. **Bottom-up**: fuerza de equipo = agregación de los **11 titulares + 6 suplentes**
   disponibles (de la alineación real), no un rating de club.
2. **Temporal**: el Elo de cada jugador **evoluciona partido a partido**; se consulta
   "a fecha de" el partido a predecir (no un valor estático de temporada).
3. **Ponderado por dificultad**: rendir bien **contra un rival fuerte cuenta más** que
   contra uno débil. La dificultad del rival se mide **pre-partido**.

## 2. Fuentes de datos (validadas, gratis)

| Dato | Fuente | Notas |
|------|--------|-------|
| Rendimiento por jugador y **partido** (xG, xA, acciones, minutos) | FBref `read_player_match_stats` (soccerdata) | Pesado (Selenium) → **offline/cacheado** |
| **Dificultad del rival** en una fecha | **ClubElo** `read_by_date` (soccerdata) | Ligero (CSV); Elo de club histórico = dificultad |
| Alineación (XI + banquillo) | API-Football `/fixtures/lineups` | En vivo; gratis para fechas cercanas |
| Fixtures/resultados | API-Football `/fixtures` | Por temporada (free 2021-2024) |

> Patrón: el scraping vive en `scripts/` (offline) y genera **JSON** (Elos de jugador con
> histórico) que la app consume con repos JSON simples. La app no scrapea en runtime.

## 3. Algoritmo — Elo de jugador temporal

Se procesan los partidos en **orden cronológico**. Para cada jugador `j` que juega un
partido contra un rival de dificultad `d` (ClubElo del rival a esa fecha, normalizado):

```
perf_j      = índice de rendimiento del jugador en el partido (xG + xA + acciones, normalizado)
expected_j  = f(rating_actual_j)            # un jugador top "se espera" que rinda más
peso        = minutos_jugados / 90          # menos minutos, menos efecto
gain        = K · peso · g(d) · (perf_j − expected_j)
rating_j    ← rating_j + gain
```

- `g(d)`: factor de dificultad creciente con el nivel del rival (rendir vs un grande
  pondera más).
- `expected_j`: evita que un jugador suba indefinidamente; debe **batir su expectativa**.
- `K`: tasa de aprendizaje; regresión suave a la media en inactividad (opcional).

El resultado es una **serie temporal** de rating por jugador; se consulta `rating_as_of(j, fecha)`.

## 4. De jugadores a fuerza de equipo

1. Tomar la **alineación** (XI + banquillo) del fixture; si no hay XI confirmado, usar el
   previsto/últimos onces.
2. Seleccionar **11 + 6** por rating; `SquadAggregator` agrega (titulares peso pleno,
   banquillo parcial) → factor de fuerza de plantilla.
3. Convertir el factor a **ataque/defensa** del dominio (split ofensivo/defensivo por
   posición y métricas: atacantes pesan en ataque; defensas/portero en defensa).
4. Ese ataque/defensa entra en **Dixon-Coles** → λ de goles → matriz/1X2/over-under.

## 5. Estadísticas de equipo ponderadas por rival

Además del Elo de jugador, las **stats avanzadas de equipo** (xG a favor/en contra,
posesión, tiros) se **ponderan por la dificultad del rival** de cada partido al
agregarlas (un xG alto contra una gran defensa vale más). Alimentan:
- ajuste fino de ataque/defensa,
- **matchups de estilo** (p.ej. equipo de posesión vs bloque bajo).

## 6. Integración (capas, trazable en `--explain`)

```
Base (plantilla 11+6 con Elo de jugador temporal → ataque/defensa)
  + Stats de equipo ponderadas por rival
  + Forma reciente            (ya implementado)
  + H2H ponderado             (ya implementado)
  + Tarjetas por equipo       (modelo ya implementado)
  + Disponibilidad (lesiones/sanciones)
  → Dixon-Coles → predicción completa
```

## 7. Calibración (clave para que NO sea simplista)

- Parámetros (`K`, `g(d)`, `expected`, pesos titular/banquillo, split atk/def) se
  **calibran con datos reales** maximizando capacidad predictiva (p.ej. log-loss /
  Brier sobre resultados pasados), no a ojo.
- Validación: backtesting por temporadas; comparar contra el baseline (solo ClubElo) y
  contra el mercado cuando se pueda.

## 8. Plan de implementación (incrementos)

1. **Dominio puro `PlayerEloEngine`**: dado un histórico de rendimientos + dificultad de
   rival, produce ratings temporales (`as_of`). Sin scraping; 100% testeable. *(primero)*
2. **Spike de datos**: script que construye rendimientos reales (FBref match logs +
   ClubElo dificultad) para 1 temporada de LaLiga y valida que el ranking de jugadores
   tiene sentido (Vinicius/Bellingham/Lewandowski arriba).
3. **Script offline → JSON** de Elos de jugador con histórico.
4. **Repo JSON + agregación de plantilla** (11+6) desde alineación → ataque/defensa.
5. **Calibración** y backtesting.
6. Integración como capa y `--explain`.
