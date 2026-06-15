# Ratings y evolución del entrenamiento

Los modelos del dominio consumen **fuerzas multiplicativas** por equipo
(`attack`, `defense`, media ≈ 1.0). Este documento describe cómo se generan hoy y
cómo evolucionarán.

## Cómo funciona hoy (v0)

```
Resultados internacionales  ──►  scripts/train_ratings.py  ──►  data/ratings/world_cup.json
 (TODOS: amistosos +            (MLE Poisson ponderado:           (por NOMBRE de equipo)
  clasificatorios + torneos,     recencia × importancia,                 │
  todas las confederaciones)     neutral, + ridge)                       ▼
                                          PredictTodayMatches enriquece por nombre
                                          (si no hay rating, conserva el del equipo)
```

- **Fuente:** dataset abierto [martj42/international_results](https://github.com/martj42/international_results)
  — **todos** los partidos internacionales hasta hoy. Por defecto desde 2019
  (~7000 partidos, ~280 selecciones). Clave: el grafo de rivales queda **conectado**
  entre confederaciones (los amistosos enlazan continentes), así el MLE normaliza por el
  **nivel real del rival** (fuerza de calendario) y no infla a dominadores de una
  confederación de nivel medio más bajo.
- **Ponderación por partido** = recencia × importancia:
  - **Recencia:** `0.5 ** (antigüedad / half_life)` (half-life ≈ 2.5 años) → la forma actual pesa más.
  - **Importancia:** un amistoso (0.3) pesa menos que un clasificatorio (~0.6-0.8) o un Mundial (1.0).
- **Campo neutral:** la ventaja de local solo se aplica si el partido no es neutral.
- **Modelo:** Poisson bivariante por MLE ponderado; `lam = exp(log(media) + ventaja·noNeutral +
  atk_i − def_j)`, identificabilidad `mean(attack)=0` y **regularización L2** (shrinkage).
- **Conversión:** `attack = exp(atk)`, `defense = exp(−def)` (centrados) → escala
  multiplicativa del dominio.
- **Identidad:** por **nombre** de equipo (robusto entre fuentes con ids distintos).

Ejemplos del v0 (con ventaja de local): España–Cabo Verde 93%, España–Brasil 56/22/22,
Francia–Argentina 31/28/41, Marruecos–Portugal 45/28/28.

Ajustar:

```bash
python scripts/train_ratings.py --since 2021-01-01 --half-life-days 730
```

Regenerar:

```bash
python scripts/train_ratings.py            # -> data/ratings/world_cup.json
```

## Limitaciones actuales

- Diferencias de **nomenclatura** entre fuentes (p.ej. "Cape Verde" vs "Cape Verde
  Islands"): si el nombre no casa, el equipo conserva su valor por defecto. Normalización
  pendiente (R2).
- Escala `base_rate`/ventaja del dominio aún sin **calibrar** finamente contra la media de
  la fuente de entrenamiento.
- Sin ajuste por fase (grupos vs eliminatoria) ni por sede concreta.
- Tarjetas y rendimiento usan tasas base, no están entrenados aún.

## Roadmap de evolución

| Hito | Mejora | Estado |
|------|--------|--------|
| **R0 (v0)** | MLE Poisson + ridge, identidad por nombre | ✅ |
| **R1 (v0)** | Grafo internacional conectado (fuerza de calendario) + recencia + importancia del torneo + neutral | ✅ |
| **R2** | Normalización de nombres entre fuentes; calibración de `base_rate`/ventaja | ⏳ |
| **R3** | Estimación bayesiana (PyMC) con priors por confederación; versionado con MLflow | ⏳ (plan v2) |
| **R4** | Ratings dinámicos intra-torneo (actualización tras cada jornada) | ⏳ |
| **R5** | Tarjetas y rendimiento entrenados con datos reales (no solo tasas base) | ⏳ |

> El objetivo es que cada hito mejore la calibración **sin** cambiar el dominio: el
> entrenamiento vive en `scripts/` y solo produce el JSON que consume el `RatingsRepository`.
