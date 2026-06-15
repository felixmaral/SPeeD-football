<!-- Título en Conventional Commits, p.ej. feat(dixon-coles): bayesian rating core -->

## Qué
<resumen del cambio>

## Por qué
<motivación / issue que resuelve>

## Cómo probar
```bash
# pasos para verificar el cambio
```

## Checklist DoD
- [ ] Commits en Conventional Commits, atómicos
- [ ] Tests añadidos (unit dominio / integration adaptadores)
- [ ] `ruff` + `mypy --strict` en verde localmente
- [ ] CI en verde (lint + type + test, cobertura dominio ≥80%)
- [ ] CHANGELOG actualizado si aplica
- [ ] Rama actualizada con `develop`

Closes #
