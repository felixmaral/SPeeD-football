# Guía de uso — Beta

La beta es un **lanzador por CLI** que detecta los partidos del día y emite
predicciones (resultado, tarjetas, rendimiento) con explicación.

## 1. Instalación

```bash
python -m venv .venv
source .venv/Scripts/activate   # Windows (Git Bash); .venv/bin/activate en Unix
pip install -e ".[dev]"
```

> El plan original especifica `uv`; este entorno usa `venv` + `pip` como equivalente.

## 2. Configuración

Copia `.env.example` a `.env` y ajusta los valores:

```bash
cp .env.example .env
```

| Variable | Descripción | Por defecto |
|----------|-------------|-------------|
| `WCPREDICTOR_USE_MOCK` | Usa datos mock (sin red) | `true` |
| `API_FOOTBALL_KEY` | Key de API-Football (live) | vacío |
| `API_FOOTBALL_BASE_URL` | Endpoint de API-Football | `https://v3.football.api-sports.io` |
| `WCPREDICTOR_TIMEZONE` | Zona horaria | `Europe/Madrid` |

**Fallback automático:** si no hay `API_FOOTBALL_KEY`, se usa el modo mock aunque
`WCPREDICTOR_USE_MOCK=false`.

## 3. Ejecución

### Modo mock (sin red ni API key)

```bash
WCPREDICTOR_USE_MOCK=true python -m wcpredictor.delivery.cli.launcher --date 2026-06-15
```

### Modo real (API-Football)

```bash
# con API_FOOTBALL_KEY en .env y WCPREDICTOR_USE_MOCK=false
python -m wcpredictor.delivery.cli.launcher          # partidos de hoy
python -m wcpredictor.delivery.cli.launcher --date 2026-06-15
```

También disponible como comando instalado:

```bash
wcpredictor --date 2026-06-15
```

## 4. Salida de ejemplo

```
Spain vs Cape Verde Islands
Pronóstico: Spain (51.8%)

Resultado (1X2):
  Spain: 51.8%
  Empate: 21.9%
  Cape Verde Islands: 26.3%
Goles esperados: 2.10 - 1.46
Marcador más probable: 1-1
Over 2.5 goles: 69.1%

Tarjetas:
  Esperadas: 4.4
  Over 4.5: 44.9%

Rendimiento:
  Posesión: 55% - 45%
  xG: 1.87 - 1.46
```

## 5. Limitaciones conocidas (beta)

- **API-Football free tier:** ~100 req/día y ventana de fechas restringida; pensado
  para desarrollo. Las predicciones se cachean (ratings en JSON) para mitigarlo.
- **Proxy TLS corporativo:** en redes con inspección TLS, configura el CA corporativo
  o usa el modo mock. El adaptador permite ajustar la verificación.
- **Ratings entrenados:** `data/ratings/world_cup.json` se genera con
  `scripts/train_ratings.py` a partir de **todos los partidos internacionales**
  (martj42), con MLE Poisson ponderado por recencia e importancia del torneo sobre un
  grafo de rivales conectado entre confederaciones. Las selecciones cuyo nombre no case
  conservan un rating por defecto. Ver [docs/RATINGS.md](RATINGS.md) para detalles y roadmap.
- **Refresco por alineaciones** (T−60/−30) y **bot de Telegram** llegan en v1.0/v1.1.
