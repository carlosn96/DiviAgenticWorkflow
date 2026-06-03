---
name: daw-skill
description: The unified source of truth for the local Divi Agentic Workflow (DAW) in divitheme. Use this for any task involving the creation, modification, or deployment of Divi 5 pages. It orchestrates the 4-phase workflow: Analysis, Design Research, Mapping, and Execution.
---

# DAW-Skill: Divi Agentic Workflow Orchestrator (v4.1)

Motor definitivo para la construcción de sitios con **Divi 5.5.0 Native**. Aplica separación estricta de responsabilidades mediante una orquestación modular de **4 fases**.

> [!CAUTION]
> **Regla de oro**: cada fase produce un **artefacto escrito obligatorio** antes de que la siguiente fase comience. No existe "la fase se hizo en mi cabeza". Sin artefacto, la fase no terminó.

---

## ⚡ Pipeline Real (lo que realmente se ejecuta)

```
Brand vars (_design_vars.json)
  → build_design_system.py
    → divitheme.json (58 presets)
    → brand/assets/css/brand.css (por marca, único por DAW_SITE)
  → wp agentic global_colors sync
  → page-defs/<slug>.json (manifiesto) + sections/*.json
  → combine.py → <slug>-combined.json
  → build_page.php --deploy
    → Layout Engine → post_content en WP
  → Runtime: brand.css se encola desde disco via plugin
```

---

## ⚠️ Prerrequisito: Sistema de Colores Globales (gcid)

Antes de desplegar, los colores deben estar sincronizados con Divi 5 como Global Colors (`gcid-*`).

| Cuándo | Comando |
|--------|---------|
| **Una vez, al crear el design system** | `.\wp.bat agentic global_colors sync --design-system="DAW_bundle/site/<DAW_SITE>/design-system/divitheme.json"` |
| **Cada vez que cambien los colores** | Mismo comando (detecta cambios vía hash) |
| **Verificar estado** | `.\wp.bat agentic global_colors status --design-system="..."` |

---

## ⚡ Flujo de CSS de Marca (sin BD)

El CSS de marca (`daw-*` classes, variables `--daw-*`) se sirve **desde disco**, no desde la BD:

| Qué | Origen | Mecanismo |
|-----|--------|-----------|
| `daw-*` classes | `site/<DAW_SITE>/brand/assets/css/brand.css` | `wp_enqueue_style('daw-brand-css')` |
| `--daw-*` variables | `design-system/divitheme.json` | Inline via `wp_add_inline_style` |
| Fonts Google | `design-system/divitheme.json` | `wp_enqueue_style` dinámico |
| Module CSS | `modules/<slug>/style.css` | `Module_Registry` |

**Lo que YA NO se usa:**
- ❌ `wp_update_custom_css_post()` — no más dump a la BD
- ❌ `et_custom_css` (wp_options) — legacy eliminado
- ❌ `custom_css` CPT — vaciado
- ❌ `sync_css` en `build_page.php` — removido

**`sync_css` ahora solo limpia legacy**, no escribe:

```powershell
.\wp.bat agentic sync_css
# → Verifica archivos en disco
# → Limpia et_custom_css
# → Vacía custom_css CPT
```

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
3. Combinar: `python site/<DAW_SITE>/page-defs/combine.py <manifest> --out <combined>.json`
4. El JSON combinado se pasa a `build_page.php --def=<combined>.json`

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
python DAW_bundle/site/<DAW_SITE>/page-defs/combine.py `
  DAW_bundle/site/<DAW_SITE>/page-defs/<slug>.json `
  --out DAW_bundle/site/<DAW_SITE>/page-defs/<slug>-combined.json

# 2. Build + Deploy
.\php.bat DAW_bundle/divi-agentic-core/bin/build_page.php `
  --def="<slug>-combined.json" --deploy
```

> [!IMPORTANT]
> `build_page.php` ya NO ejecuta `sync_css`. El CSS se sirve desde disco automáticamente.

**Artefacto obligatorio:**
```
WP Post ID: <id>
URL: <http://...>
```

> ⛔ **STOP**: si el deploy falla, el Ingeniero diagnostica antes de declarar la tarea completa.

---

## Reglas de Diseño

### Dependencia del Sistema de Diseño

El design system se genera automáticamente. No se edita a mano.

```powershell
# 1. Editar brand/_design_vars.json (solo lo que cambia)
# 2. Generar design system:
python DAW_bundle/workspace/build_design_system.py
#    → site/<DAW_SITE>/design-system/divitheme.json
#    → site/<DAW_SITE>/brand/assets/css/brand.css

# 3. Sincronizar colores globales:
.\wp.bat agentic global_colors sync `
  --design-system="DAW_bundle/site/<DAW_SITE>/design-system/divitheme.json"
```

- **Contenedores**: usar decoration nativa (background, spacing) en vez de clases.
- **Tipografía**: usar `headingFont` y `bodyFont` con tokens `{{design:font:*}}`.
- **Colores**: usar tokens `{{design:color:*}}` — nunca hex hardcodeados.
- **Animaciones**: usar decoration.animation cuando sea posible.

### Bloques Divi 5 — Regla Fundamental
**NO usar `divi/code` como comodín.** Consultar siempre `blocks-dictionary.md` primero.

> [!CAUTION]
> **PROHIBIDO** usar `et_pb_*` (shortcodes Divi 4). El Layout Engine espera únicamente `divi/*`.

Cada directorio en `site/` tiene su propio `brand/assets/css/brand.css`. `DAW_SITE` en `.env` define cuál usar:

```powershell
# Editar .env: DAW_SITE=nueva-marca

# Regenerar design system + brand.css específico
python DAW_bundle/workspace/build_design_system.py

# Sincronizar colores
.\wp.bat agentic global_colors sync `
  --design-system="DAW_bundle/site/<DAW_SITE>/design-system/divitheme.json"
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
| Shared Kernel | `DAW_bundle/daw/README.md` | Capa 1: cfg, types, tokens |
| Inputs/Outputs del DS | `references/design-system-inputs.md` | Formatos de `_design_vars.json`, `_design_presets.json`, brief JSON, CLI de generadores |
| VIE package | `DAW_bundle/vie/README.md` | Visual Impact Engine |
