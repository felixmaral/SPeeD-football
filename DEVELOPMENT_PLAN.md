# DEVELOPMENT PLAN — Football World Cup Predictor (`wcpredictor`)

> **Audiencia:** agente de código (Claude Code).
> **Objetivo:** construir, fase a fase y respetando reglas estrictas de desarrollo, un sistema de predicción estadística de fútbol escalable.
> **Regla de oro:** no avanzar a la siguiente fase sin que la anterior tenga tests verdes, CI en verde y PR mergeado a `develop` siguiendo la metodología descrita.

---

## 0. VISIÓN Y FASES DEL PRODUCTO

| Fase | Entregable | Estado objetivo |
|------|-----------|-----------------|
| **MVP / Beta** | Lanzador de test por CLI: detecta partidos del Mundial de hoy y emite predicciones (resultado, tarjetas, rendimiento) con explicabilidad | Ejecutable local |
| **v1.0** | Bot de Telegram con allowlist de usuarios; emite predicciones día a día | Servicio desplegado |
| **v1.1** | Scheduler que **refresca la predicción cuando salen las alineaciones (T−60 a T−30 min)** | Automatizado |
| **v2.0** | Escalado a **LaLiga** y arquitectura multi-liga por plugins | Multi-competición |
| **v2.x** | Ligas adicionales (Premier, Serie A…) como adaptadores | Extensible |

**Principio rector:** cada fase NO reescribe la anterior. La arquitectura hexagonal (puertos y adaptadores) garantiza que el núcleo de predicción sea independiente de quién lo invoca (CLI, bot, API) y de qué liga se trate.

---

## 1. ARQUITECTURA OBJETIVO

```
                    ┌─────────────────────────────────────────────┐
                    │                 DELIVERY                     │
                    │   (adaptadores de entrada / "driving")       │
                    │   ┌──────────┐  ┌──────────┐  ┌──────────┐   │
                    │   │ CLI      │  │ Telegram │  │ REST API │   │
                    │   │ launcher │  │ bot      │  │ (futuro) │   │
                    │   └────┬─────┘  └────┬─────┘  └────┬─────┘   │
                    └────────┼────────────┼─────────────┼─────────┘
                             │            │             │
                    ┌────────▼────────────▼─────────────▼─────────┐
                    │              APPLICATION                     │
                    │   Casos de uso / orquestación                │
                    │   • PredictTodayMatches                      │
                    │   • RefreshPredictionOnLineup                │
                    │   • RegisterAllowedUser                      │
                    └────────┬─────────────────────────────────────┘
                             │
                    ┌────────▼─────────────────────────────────────┐
                    │                 DOMAIN (núcleo puro)         │
                    │   • Modelos: DixonColes, CardsModel,         │
                    │     PerformanceModel                         │
                    │   • Entidades: Match, Team, Player, Referee  │
                    │   • Servicios: Predictor, Explainer          │
                    │   • SIN dependencias de I/O ni frameworks    │
                    └────────┬─────────────────────────────────────┘
                             │  (puertos / interfaces)
        ┌────────────────────┼────────────────────────────────────┐
        │                INFRASTRUCTURE                            │
        │   (adaptadores de salida / "driven")                    │
        │   ┌────────────┐ ┌────────────┐ ┌────────────┐          │
        │   │ FixtureRepo│ │ RatingsRepo│ │ Scheduler  │          │
        │   │ (API-Foot) │ │ (JSON/DB)  │ │ (jobs)     │          │
        │   └────────────┘ └────────────┘ └────────────┘          │
        │   ┌──────────────────────────────────────────┐          │
        │   │ LeaguePlugin registry: WorldCup, LaLiga…  │          │
        │   └──────────────────────────────────────────┘          │
        └──────────────────────────────────────────────────────────┘
```

### Por qué esta arquitectura escala a tus 3 objetivos
- **CLI → Bot → API:** todos son adaptadores de *delivery* que llaman a los mismos casos de uso. Añadir Telegram = añadir un adaptador, **no tocar el dominio**.
- **Mundial → LaLiga → otras ligas:** cada liga implementa la interfaz `LeaguePlugin`. El core no sabe qué liga es.
- **Refresco por alineaciones:** es un caso de uso (`RefreshPredictionOnLineup`) disparado por el `Scheduler`. Desacoplado del resto.

### Estructura de carpetas
```
wcpredictor/
├── src/wcpredictor/
│   ├── domain/              # núcleo puro, sin I/O
│   │   ├── entities/        # match.py, team.py, player.py, referee.py
│   │   ├── models/          # dixon_coles.py, cards.py, performance.py
│   │   └── services/        # predictor.py, explainer.py
│   ├── application/         # casos de uso + puertos (interfaces ABC)
│   │   ├── ports/           # fixture_repo.py, ratings_repo.py, scheduler.py, notifier.py
│   │   └── use_cases/       # predict_today.py, refresh_on_lineup.py, register_user.py
│   ├── infrastructure/      # adaptadores concretos
│   │   ├── fixtures/        # api_football.py, mock.py
│   │   ├── ratings/         # json_repo.py, (db_repo.py futuro)
│   │   ├── leagues/         # base.py, world_cup.py, la_liga.py
│   │   ├── scheduling/      # apscheduler_adapter.py
│   │   └── notifiers/       # telegram.py, console.py
│   ├── delivery/            # puntos de entrada
│   │   ├── cli/             # launcher.py  (FASE BETA)
│   │   └── bot/             # telegram_app.py (FASE v1.0)
│   └── config/              # settings.py (pydantic-settings)
├── tests/
│   ├── unit/                # dominio, sin red
│   ├── integration/         # adaptadores con mocks/sandbox
│   └── e2e/                 # flujo lanzador completo
├── data/                    # ratings entrenados (JSON), NO secretos
├── scripts/                 # entrenamiento de modelos, utilidades
├── docs/                    # ADRs, diagramas
├── .github/
│   ├── workflows/ci.yml
│   ├── ISSUE_TEMPLATE/
│   └── PULL_REQUEST_TEMPLATE.md
├── pyproject.toml
├── .pre-commit-config.yaml
├── .env.example
├── CHANGELOG.md
└── README.md
```

---

## 2. STACK Y TOOLING

| Capa | Elección | Motivo |
|------|----------|--------|
| Lenguaje | Python 3.12+ | Ecosistema de datos/ML |
| Gestor de proyecto/deps | **uv** | Rápido, lockfile reproducible |
| Config | **pydantic-settings** | Validación de env vars, sin secretos en código |
| Modelado estadístico | numpy, scipy, **PyMC** (entrenamiento) | Dixon-Coles bayesiano |
| Scheduler | **APScheduler** | Jobs con triggers de fecha/hora y reintentos |
| Bot | **python-telegram-bot** (v21+, async) | Estándar de facto |
| HTTP | **httpx** | Async, timeouts, retries |
| Tests | **pytest**, pytest-asyncio, **responses**/respx (mock HTTP) | Cobertura por capas |
| Lint/format | **ruff** (lint + format) | Una sola herramienta |
| Type check | **mypy** (strict) | Seguridad de tipos |
| Pre-commit | **pre-commit** | Calidad antes de commitear |
| CI | **GitHub Actions** | Lint + type + test en cada PR |
| Contenedor | Docker (para v1.0 deploy) | Reproducibilidad en prod |
| Versionado modelos | **MLflow** | Trazabilidad de ratings por jornada |

---

## 3. REGLAS DE DESARROLLO (CUMPLIMIENTO OBLIGATORIO)

### 3.1 Metodología de ramas — GitFlow

```
main        ──●────────────────●────────────────●──>   (solo releases; tag vX.Y.Z)
               \              /  \              /
release         \            /    release      /
                 \          /      \          /
develop  ●───●───●────●────●────●───●────●────●──>     (integración continua)
          \     /      \       /
feature    ●───●        ●─────●                         (ramas de trabajo)
```

**Ramas permanentes:**
- `main` — código en producción. Cada merge = release etiquetada. **Nunca** se commitea directo.
- `develop` — rama de integración. Base de todas las `feature/*`.

**Ramas temporales (se borran tras merge):**
- `feature/*` — nace de `develop`, muere en `develop`.
- `release/*` — nace de `develop`, muere en `main` **y** `develop`. Solo bugfixes y bump de versión.
- `hotfix/*` — nace de `main`, muere en `main` **y** `develop`. Para fallos críticos en producción.

**Prohibido:** push directo a `main` y `develop` (protección de rama activada). Todo entra por PR.

### 3.2 Denominación de ramas

Formato: `<tipo>/<id-issue>-<descripcion-kebab-case>`

| Tipo | Uso | Ejemplo |
|------|-----|---------|
| `feature/` | Nueva funcionalidad | `feature/12-dixon-coles-core` |
| `bugfix/` | Corrección en `develop` | `bugfix/34-lineup-timezone-offset` |
| `hotfix/` | Corrección urgente en prod | `hotfix/51-telegram-rate-limit` |
| `release/` | Preparación de versión | `release/1.0.0` |
| `chore/` | Mantenimiento, tooling | `chore/8-setup-ci-pipeline` |
| `docs/` | Documentación | `docs/19-architecture-adr` |

Reglas: minúsculas, separadores `-`, sin acentos ni espacios, máx ~50 caracteres tras el ID, **siempre** referencia el nº de issue.

### 3.3 Commits — Conventional Commits

Formato:
```
<tipo>(<ámbito>): <descripción imperativa en minúscula>

[cuerpo opcional: el porqué, no el qué]

[footer opcional: Refs #12 / Closes #12 / BREAKING CHANGE: ...]
```

| Tipo | Cuándo |
|------|--------|
| `feat` | Nueva funcionalidad |
| `fix` | Corrección de bug |
| `refactor` | Cambio interno sin alterar comportamiento |
| `test` | Añadir/corregir tests |
| `docs` | Documentación |
| `chore` | Tooling, deps, config |
| `ci` | Pipeline CI/CD |
| `perf` | Mejora de rendimiento |
| `style` | Formato (sin lógica) |

**Ámbitos sugeridos:** `domain`, `dixon-coles`, `cards`, `fixtures`, `telegram`, `scheduler`, `leagues`, `config`, `ci`.

Ejemplos correctos:
```
feat(dixon-coles): add bayesian rating estimation with pymc
fix(scheduler): retry lineup fetch when api returns empty squad
refactor(leagues): extract LeaguePlugin interface from world cup adapter
test(cards): cover referee strictness multiplier edge cases
chore(ci): add mypy strict to github actions
```
Reglas: descripción ≤ 72 caracteres, modo imperativo ("add", no "added"/"adds"), sin punto final. Un commit = un cambio lógico atómico. `BREAKING CHANGE:` en footer para cambios incompatibles.

### 3.4 Issues

**Naming del título:** `[<TIPO>] <descripción concisa>` — ej. `[FEATURE] Dixon-Coles bayesian core`, `[BUG] Lineup fetch ignores timezone`.

**Labels obligatorias (≥2):**
- Tipo: `type:feature`, `type:bug`, `type:chore`, `type:docs`
- Prioridad: `prio:critical`, `prio:high`, `prio:medium`, `prio:low`
- Fase: `phase:beta`, `phase:v1`, `phase:v2`
- Componente: `comp:domain`, `comp:fixtures`, `comp:telegram`, `comp:scheduler`, `comp:leagues`

**Plantilla de issue (feature):**
```markdown
## Objetivo
<qué se quiere lograr y por qué>

## Criterios de aceptación
- [ ] ...
- [ ] Tests unitarios con cobertura del caso
- [ ] Documentación/CHANGELOG actualizados

## Notas técnicas
<puerto/adaptador afectado, dependencias>

## Definición de Hecho (DoD)
- [ ] CI en verde (lint + mypy + tests)
- [ ] PR revisado y aprobado
- [ ] Mergeado a develop sin romper otros tests
```

Cada issue se vincula a su PR con `Closes #N`. Issues agrupadas por **Milestone** = fase del producto (`Beta`, `v1.0`, `v1.1`, `v2.0`).

### 3.5 Pull Requests

- Título con Conventional Commits: `feat(dixon-coles): bayesian rating core`.
- Cuerpo según `PULL_REQUEST_TEMPLATE.md`: qué, por qué, cómo probar, checklist DoD, `Closes #N`.
- **No se mergea** sin: CI verde + 1 aprobación + sin conflictos + rama actualizada con `develop`.
- Estrategia de merge: **squash & merge** hacia `develop` (historial limpio); **merge commit** real para `release→main`.
- Borrar rama tras merge.

### 3.6 Versionado — SemVer

`MAJOR.MINOR.PATCH`. Beta usa sufijo: `0.1.0-beta.1`. Releases etiquetan `main` con `git tag vX.Y.Z`. `CHANGELOG.md` mantenido en formato *Keep a Changelog*, actualizado en cada `release/*`.

### 3.7 Calidad — gates automáticos
- **pre-commit** local: ruff (lint+format), mypy, detección de secretos, fin de fichero.
- **CI** bloqueante en cada PR: `ruff check`, `ruff format --check`, `mypy --strict`, `pytest` con cobertura mínima **80%** en `domain/`.
- Ningún PR rojo se mergea.

---

## 4. EJECUCIÓN POR FASES (el agente sigue este orden)

> Cada paso = 1 issue + 1 rama `feature/*` + 1 PR a `develop`. El agente abre la issue, crea la rama con la notación correcta, commitea con Conventional Commits, abre PR enlazando la issue, espera CI verde, mergea.

### FASE 0 — Bootstrap del repositorio  · Milestone: `Beta`
- **#1** `[CHORE] Initialize repo, uv project and structure` → rama `chore/1-init-project`
  - `uv init`, estructura de carpetas hexagonal, `pyproject.toml`, `.env.example`, `.gitignore`.
  - Configurar protección de ramas en `main` y `develop`.
- **#2** `[CHORE] Setup tooling: ruff, mypy, pre-commit` → `chore/2-tooling`
- **#3** `[CI] GitHub Actions: lint, type-check, test` → `ci/3-github-actions`
- **#4** `[CHORE] Issue/PR templates and labels` → `chore/4-repo-templates`
- **#5** `[DOCS] ADR-001 hexagonal architecture + README skeleton` → `docs/5-architecture-adr`

### FASE 1 — Núcleo de dominio (puro, testeable sin red)  · Milestone: `Beta`
- **#6** `[FEATURE] Domain entities: Match, Team, Player, Referee` → `feature/6-domain-entities`
- **#7** `[FEATURE] Dixon-Coles result model + score matrix` → `feature/7-dixon-coles-core`
  - Implementación determinista, totalmente cubierta por tests unitarios.
- **#8** `[FEATURE] Player-availability adjustment to team strength` → `feature/8-availability-factor`
- **#9** `[FEATURE] Cards model (referee × aggression × player risk)` → `feature/9-cards-model`
- **#10** `[FEATURE] Performance model (xG, possession, box touches)` → `feature/10-performance-model`
- **#11** `[FEATURE] Explainer service (decomposición legible)` → `feature/11-explainer`
- **#12** `[FEATURE] Predictor service orchestrating domain models` → `feature/12-predictor-service`

> **Checkpoint dominio:** 100% del núcleo funciona con datos en memoria, sin tocar red. Cobertura ≥80%.

### FASE 2 — Puertos y adaptadores de datos  · Milestone: `Beta`
- **#13** `[FEATURE] Define ports: FixtureRepo, RatingsRepo (ABC)` → `feature/13-ports-interfaces`
- **#14** `[FEATURE] LeaguePlugin interface + registry` → `feature/14-league-plugin-interface`
- **#15** `[FEATURE] WorldCup league adapter` → `feature/15-world-cup-adapter`
- **#16** `[FEATURE] API-Football fixture adapter (httpx + retries)` → `feature/16-api-football-adapter`
- **#17** `[FEATURE] Mock fixture adapter for offline/dev` → `feature/17-mock-adapter`
- **#18** `[FEATURE] JSON ratings repository` → `feature/18-json-ratings-repo`
- **#19** `[TEST] Integration tests for adapters (respx mocks)` → `feature/19-adapter-integration-tests`

### FASE 3 — Caso de uso + Lanzador BETA (ENTREGABLE BETA)  · Milestone: `Beta`
- **#20** `[FEATURE] Use case: PredictTodayMatches` → `feature/20-predict-today-usecase`
  - Detecta fecha de hoy, resuelve liga activa (WorldCup), trae fixtures, predice, explica.
- **#21** `[FEATURE] CLI launcher with console notifier` → `feature/21-cli-launcher`
  - `python -m wcpredictor.delivery.cli.launcher` → imprime predicciones de hoy.
- **#22** `[FEATURE] Config via pydantic-settings (.env, mock fallback)` → `feature/22-settings`
- **#23** `[TEST] E2E test: launcher runs in mock mode` → `feature/23-e2e-launcher`
- **#24** `[DOCS] Beta usage guide` → `docs/24-beta-readme`
- **RELEASE** `release/0.1.0-beta.1` → merge a `main`, tag `v0.1.0-beta.1`. **🎯 BETA ENTREGADA.**

### FASE 4 — Bot de Telegram con allowlist  · Milestone: `v1.0`
- **#25** `[FEATURE] Notifier port + Telegram notifier adapter` → `feature/25-telegram-notifier`
- **#26** `[FEATURE] User allowlist (authorized access only)` → `feature/26-user-allowlist`
  - Solo IDs autorizados reciben/consultan predicciones. Persistencia en repo de usuarios.
- **#27** `[FEATURE] Use case: RegisterAllowedUser + admin commands` → `feature/27-register-user`
- **#28** `[FEATURE] Telegram bot app (commands: /today, /match, /help)` → `feature/28-telegram-bot`
- **#29** `[FEATURE] Daily digest job (predicciones del día)` → `feature/29-daily-digest`
- **#30** `[CHORE] Dockerfile + deployment config` → `chore/30-docker-deploy`
- **#31** `[TEST] Bot integration tests (mocked Telegram API)` → `feature/31-bot-tests`
- **RELEASE** `release/1.0.0` → tag `v1.0.0`.

### FASE 5 — Scheduler de alineaciones (T−60/−30 min)  · Milestone: `v1.1`
> **Componente crítico del objetivo final.** Las alineaciones se publican de forma irregular; el sistema debe sondear y **re-predecir** cuando aparezcan.

- **#32** `[FEATURE] Scheduler port + APScheduler adapter` → `feature/32-scheduler-adapter`
- **#33** `[FEATURE] Lineup availability fetch (injuries + confirmed XI)` → `feature/33-lineup-fetch`
- **#34** `[FEATURE] Use case: RefreshPredictionOnLineup` → `feature/34-refresh-on-lineup`
  - Lógica: por cada partido de hoy, programar sondeo desde T−75 min; reintentar cada 5 min hasta confirmar XI o llegar a T−10 min; al confirmarse, **recalcular** predicción con jugadores reales y notificar la versión actualizada.
- **#35** `[FEATURE] Pre-match scheduling orchestrator (per-fixture jobs)` → `feature/35-prematch-orchestrator`
- **#36** `[FEATURE] Robust retry/backoff + idempotencia de notificaciones` → `feature/36-retry-idempotency`
  - No notificar dos veces la misma versión; marcar predicción como "preliminar" vs "confirmada con alineación".
- **#37** `[TEST] Scheduler tests with simulated clock` → `feature/37-scheduler-tests`
- **RELEASE** `release/1.1.0` → tag `v1.1.0`. **🎯 OBJETIVO FINAL FUNCIONAL.**

### FASE 6 — Escalado multi-liga (LaLiga +)  · Milestone: `v2.0`
- **#38** `[FEATURE] LaLiga league adapter` → `feature/38-la-liga-adapter`
- **#39** `[REFACTOR] Generalize fixture/ratings repos for any league` → `feature/39-multi-league-repos`
- **#40** `[FEATURE] League selection in CLI/bot (per-user league prefs)` → `feature/40-league-selection`
- **#41** `[FEATURE] Train & version LaLiga ratings (MLflow)` → `feature/41-laliga-ratings`
- **#42** `[DOCS] Guide: add a new league in N steps` → `docs/42-add-league-guide`
- **#43** `[CHORE] Migrate ratings JSON → database (scalability)` → `chore/43-db-migration`
- **RELEASE** `release/2.0.0` → tag `v2.0.0`. **🎯 MULTI-LIGA.**

---

## 5. CONTRATOS CLAVE (interfaces que garantizan la escalabilidad)

El agente define estas interfaces **antes** de cualquier adaptador concreto. Son el corazón de la extensibilidad.

```python
# application/ports/fixture_repo.py
from abc import ABC, abstractmethod
from datetime import date
from wcpredictor.domain.entities.match import Match

class FixtureRepository(ABC):
    @abstractmethod
    async def get_fixtures_for_date(self, day: date, league_id: int) -> list[Match]: ...

    @abstractmethod
    async def get_lineup_availability(self, fixture_id: int) -> "LineupInfo": ...


# infrastructure/leagues/base.py
class LeaguePlugin(ABC):
    """Cada liga (Mundial, LaLiga, …) implementa este contrato.
    Añadir una liga = implementar esta interfaz, sin tocar el dominio."""
    @property
    @abstractmethod
    def league_id(self) -> int: ...

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def is_knockout(self, stage: str) -> bool: ...

    @abstractmethod
    def ratings_namespace(self) -> str: ...


# application/ports/notifier.py
class Notifier(ABC):
    """Console (beta), Telegram (v1.0), futuros canales."""
    @abstractmethod
    async def send_prediction(self, user_id: str, report: str) -> None: ...


# application/ports/scheduler.py
class Scheduler(ABC):
    @abstractmethod
    def schedule_at(self, run_at, job_id: str, func, **kwargs) -> None: ...

    @abstractmethod
    def cancel(self, job_id: str) -> None: ...
```

**Lógica del refresco por alineación (caso de uso v1.1), en pseudocódigo:**
```
RefreshPredictionOnLineup(fixture):
    for t in [T-75, T-70, ..., T-10]:        # sondeo cada 5 min
        lineup = fixture_repo.get_lineup_availability(fixture.id)
        if lineup.is_confirmed():
            prediction = predictor.predict(fixture, lineup)   # re-predicción con XI real
            if prediction.version != last_notified.version:   # idempotencia
                notifier.send_prediction(..., mark="CONFIRMADA")
            return
    # si nunca se confirma: notificar la última estimación preliminar
```

---

## 6. CHECKLIST QUE EL AGENTE VERIFICA EN CADA ISSUE

```
[ ] Issue creada con título [TIPO] + labels (tipo, prioridad, fase, componente) + milestone
[ ] Rama creada desde develop con notación <tipo>/<id>-<kebab> 
[ ] Commits en Conventional Commits, atómicos, imperativos
[ ] Tests añadidos (unit para dominio; integration para adaptadores)
[ ] ruff + mypy --strict en verde localmente (pre-commit)
[ ] PR abierto con plantilla, "Closes #N", descripción de cómo probar
[ ] CI en verde (lint + type + test, cobertura dominio ≥80%)
[ ] Squash & merge a develop; rama borrada
[ ] CHANGELOG actualizado si aplica
```

---

## 7. PRIMER COMANDO PARA EL AGENTE

> Comienza por la **Fase 0, issue #1**. No escribas lógica de negocio todavía: monta el esqueleto, el tooling y el CI. Crea la rama `chore/1-init-project` desde `develop`, implementa la estructura de carpetas de la sección 1, configura `pyproject.toml` con uv y abre el PR enlazando la issue #1. Detente y reporta antes de pasar a #2.

Respeta SIEMPRE las reglas de la sección 3. Ante cualquier ambigüedad, prioriza: (1) que el dominio quede puro y testeable sin red, (2) que cada adaptador sea sustituible, (3) que añadir una liga o un canal de salida no requiera tocar el núcleo.
