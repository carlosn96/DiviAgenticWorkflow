# Skill Selection — Design Direction

## Regla general

Si no está claro cuál cargar, usar **impeccable** (es el comodín universal).

## Matriz de selección

| Si el proyecto es... | Cargar este skill | Por qué |
|---|---|---|
| Alta costura, lujo, hotel, vino, moda | `high-end-visual-design` | Diseño agencia premium: glassmorphism, doble bezel, espaciado masivo, tipografía display |
| SaaS, startup, producto digital, app UI | `impeccable` | Principios UX sólidos: contraste, jerarquía, color estratégico, motion intencional |
| Landing page, campaña, portfolio | `hallmark` | Anti-slop, variedad estructural, 20 temas, auto-crítica pre-emit |
| Rediseño o auditoría de UI existente | `hallmark audit` / `impeccable audit` | Score anti-patrones, diagnóstico estructurado |
| Tipografía, editorial, contenido largo | `typography` | Escala, pairing, ritmo vertical, legibilidad |
| UX research, brief, validación | `ui-ux-pro-max` | 99 guías UX, 50+ estilos visuales, priorización CRITICAL→LOW |
| Rebuild de un diseño desde screenshot/URL | `hallmark study` | Extracción de DNA visual: paleta, pairing, macroestructura |
| Sistema de diseño, tokens, design system | `high-end-visual-design` + `typography` | Doble skill: visual + tipográfico |

## Cómo aplicar el skill

1. Cargar el skill ANTES de editar `_design_vars.json`
2. Leer las reglas del skill (SKILL.md + sus referencias)
3. Evaluar los valores actuales contra el criterio del skill
4. Editar con intención de diseño

## Skills por fase del pipeline

| Fase | Skill recomendado |
|------|-------------------|
| `wp brand init` (generar scaffold) | Según matriz arriba |
| Editar `_design_vars.json` | Según matriz arriba |
| `wp brand validate` (antes de sync) | El mismo usado para editar |
| `wp brand sync --force` (bypass) | Solo si se aprobó explícitamente |

## Orden de precedencia si hay conflicto entre skills

1. `hallmark` (anti-patrones, estructura)
2. `high-end-visual-design` (calidad visual premium)
3. `impeccable` (UX, jerarquía, principios generales)
4. `typography` (tipografía)
