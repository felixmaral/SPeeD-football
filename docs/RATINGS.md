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
- **Conversión:** `attack = exp(atk·shrink)`, `defense = exp(−def·shrink)` (centrados),
  con un **recorte** holgado `[0.30, 3.50]` que solo corta valores patológicos de
  selecciones con muy pocos partidos. `shrink=1.0` por defecto (sin compresión).
- **Identidad:** por **nombre** de equipo con tabla de **alias** entre fuentes
  (p.ej. "Cape Verde Islands"→"Cape Verde", "Korea Republic"→"South Korea").

### Alcance del v0 (salida)
La salida se centra en **resultado (1X2), goles esperados (una sola cifra, las λ),
marcador más probable y over/under**. Las probabilidades nunca se muestran como `0.0%`
(se usa `<0.1%`). Posesión, xG separado y tarjetas quedan **fuera del v0** (sus modelos
permanecen en el código para versiones futuras).

Ejemplos del v0 (con ventaja de local): España–Cabo Verde 93%/6%/2% (3.87-0.53),
España–Brasil 56/22/22, Francia–Argentina 37/26/36, Canadá–Cabo Verde 71% (Canadá favorita).

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
