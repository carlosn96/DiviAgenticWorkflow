---
name: daw-skill
description: The unified source of truth for the local Divi Agentic Workflow (DAW) in divitheme. Use this for any task involving the creation, modification, or deployment of Divi 5 pages. It orchestrates the 4-phase workflow: Analysis, Design Research, Mapping, and Execution. Brand CSS is now handled via Divi Customizer (brand-sync.php → et_divi).
---

# DAW-Skill: Divi Agentic Workflow Orchestrator (v5.0)

Motor definitivo para la construcción de sitios con **Divi 5.5.0 Native**. Aplica separación estricta de responsabilidades mediante una orquestación modular de **4 fases**.

> [!CAUTION]
> **Regla de oro**: cada fase produce un **artefacto escrito obligatorio** antes de que la siguiente fase comience. No existe "la fase se hizo en mi cabeza". Sin artefacto, la fase no terminó.

---

## ⚡ Pipeline Real

```
Brand vars (_design_vars.json)
  → brand-sync.php
    → wp_options['et_divi'] (Customizer global)
    → divitheme.json (tokens + presets)
    → gcids via GlobalData::set_global_colors()
  → page-defs/<slug>.json (manifiesto) + sections/*.json
  → python workspace/combine.py → <slug>-combined.json
  → wp agentic deploy_page → post_content en WP
```

---

## ⚡ Brand Sync (único comando)

```powershell
wp eval-file divi-agentic-core/bin/brand-sync.php
```

Sincroniza **todo** en un solo paso:

| Destino | Qué |
|---------|-----|
| `wp_options['et_divi']` | 38+ colores, 5 fuentes, logo, font sizes/weights → tema global |
| `divitheme.json` | Tokens actualizados para Design_Resolver |
| Global Colors (gcids) | Colores vía `GlobalData::set_global_colors()` |
| Global Variables (gvids) | Radios, espacios y fuentes vía `GlobalData::set_global_variables()` — variables nativas editables en VB |

No necesita `global_colors sync` aparte.

---

## Principio Central: Orquestación Modular con Contratos de Fase

Toda tarea DEBE pasar por estas cuatro fases en orden. Cada fase produce un artefacto concreto.

---

### Fase 1 — Análisis Semántico (El Arquitecto)

- *Consultar*: [`references/blocks-dictionary.md`](references/blocks-dictionary.md)
- *Leer*: [`references/architect.md`](references/architect.md)
- *Meta*: Definir estructura semántica y objetivos de negocio.

**Artefacto obligatorio — Brief JSON:**
```json
{
  "title": "Página",
  "slug": "slug",
  "sections": [
    {"section_type": "hero", "title": "...", "text": "...", "btn_primary_text": "..."},
    {"section_type": "features", "items": [...]}
  ]
}
```

> ⛔ **STOP**: si el Brief JSON no está escrito, NO iniciar Fase 2.

---

### Fase 2 — Investigación de Diseño (Design Lead) ← **BLOQUEANTE**

- *Leer*: [`references/design-lead.md`](references/design-lead.md)
- *Meta*: Validar contra las **6 Leyes de Calidad Autónoma**, documentar dirección visual.

**Artefacto obligatorio — Design Brief:**
```
Estilo visual: <editorial / modern / premium / minimal / dramatic>
Secciones con alternancia de fondo: [✓ ley 1]
...
```

> ⛔ **STOP**: si el Design Brief no está escrito con las 6 leyes validadas, NO iniciar Fase 3.

---

### Fase 3 — Mapeo Visual (El Diseñador)

- *Consultar*: [`references/blocks-dictionary.md`](references/blocks-dictionary.md) y [`references/designer.md`](references/designer.md)
- *Meta*: Construir page-defs y secciones.

**Formato de page-def actual:**
1. Crear manifiesto en `site/<DAW_SITE>/page-defs/<slug>.json`:
```json
{
  "_manifest": "v1",
  "title": "Mi Página",
  "slug": "mi-pagina",
  "sections": ["sections/hero.json", "sections/features.json"]
}
```
2. Crear cada sección en `site/<DAW_SITE>/page-defs/sections/<slug>.json`
3. Combinar: `python DAW_bundle/workspace/combine.py <manifest> --out <combined>.json`
4. El JSON combinado se pasa a `wp agentic deploy_page`

**Verificación antes de entregar a Fase 4:**
- [ ] Ningún tipo `et_pb_*` en el JSON
- [ ] Ningún hex hardcodeado — todo es `{{design:color:*}}`
- [ ] Ningún preset inexistente (verificar contra `divitheme.json`)
- [ ] Posiciones de gradient sin `%`
- [ ] Las 6 leyes del Design Brief están reflejadas

> ⛔ **STOP**: si el page-def no pasa la verificación, NO iniciar Fase 4.

---

### Fase 4 — Ejecución CLI (El Ingeniero)

- *Leer*: [`references/engineer.md`](references/engineer.md)
- *Meta*: Desplegar con un solo comando.

**Flujo actual:**
```powershell
# 1. Combinar manifiesto + secciones
python DAW_bundle/workspace/combine.py `
  DAW_bundle/site/<DAW_SITE>/page-defs/<slug>.json `
  --out DAW_bundle/site/<DAW_SITE>/page-defs/<slug>-combined.json

# 2. Deploy directo (Layout Engine refactorizado con renderers modulares)
.\wp.bat agentic deploy_page `
  --title="Título de la página" `
  --slug="<slug>" `
  --schema="DAW_bundle/site/<DAW_SITE>/page-defs/<slug>-combined.json" `
  --design-system="DAW_bundle/site/<DAW_SITE>/design-system/divitheme.json"
```

> [!IMPORTANT]
> `build_page.php` es **legacy**. El Layout Engine fue refactorizado a renderers modulares (`inc/core/renderers/*.php`) que soportan namespaces de terceros (`dgpc/*`, `dac/*`).

**Artefacto obligatorio:**
```
WP Post ID: <id>
URL: <http://...>
```

> ⛔ **STOP**: si el deploy falla, el Ingeniero diagnostica antes de declarar la tarea completa.

---

## Reglas de Diseño

### Dependencia del Sistema de Diseño

```powershell
# 1. Editar brand/_design_vars.json (solo lo que cambia)
# 2. Sincronizar todo:
.\wp eval-file DAW_bundle/divi-agentic-core/bin/brand-sync.php
#    → et_divi (Customizer) + divitheme.json (tokens) + gcids (colores vivos)
```

- **Contenedores**: usar decoration nativa (background, spacing) en vez de clases.
- **Tipografía**: usar `headingFont` y `bodyFont` con tokens `{{design:font:*}}`.
- **Colores**: usar tokens `{{design:color:*}}` — nunca hex hardcodeados.
- **Animaciones**: usar decoration.animation cuando sea posible.

### Bloques Divi 5 — Regla Fundamental
**NO usar `divi/code` como comodín.** Consultar siempre `blocks-dictionary.md` primero.

> [!CAUTION]
> **PROHIBIDO** usar `et_pb_*` (shortcodes Divi 4). El Layout Engine espera únicamente `divi/*`.

`DAW_SITE` en `.env` define qué directorio `site/` usar. `brand-sync.php` auto-descubre la ruta:

```powershell
# Editar .env: DAW_SITE=nueva-marca
# Editar site/<DAW_SITE>/brand/_design_vars.json
# Sincronizar todo:
.\wp eval-file DAW_bundle/divi-agentic-core/bin/brand-sync.php
```

---

## Fuente de Verdad (Ground Truth)

| Recurso | Archivo | Propósito |
|---------|---------|-----------|
| Diccionario de bloques | `references/blocks-dictionary.md` | Guía de 102 módulos |
| Estándares del proyecto | `references/knowledge.md` | Reglas técnicas |
| Lógica del Diseñador | `references/designer.md` | Mapeo semántico → page-defs |
| Lógica del Ingeniero | `references/engineer.md` | CLI, deploy, verificación |
| Pipeline DAW | `DAW_bundle/AGENTS.md` | Fuente de verdad del flujo completo |
| Brand Sync | `DAW_bundle/divi-agentic-core/bin/brand-sync.php` | Mapeo `_design_vars.json` → `et_divi` |
| Inputs del Brand | `references/design-system-inputs.md` | Formatos de `_design_vars.json`, brief JSON |
| VIE package | `DAW_bundle/vie/README.md` | Visual Impact Engine |
