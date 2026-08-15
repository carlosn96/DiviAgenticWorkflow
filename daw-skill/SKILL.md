---
name: daw-skill
description: The unified source of truth for the local Divi Agentic Workflow (DAW). Use this for any task involving the creation, modification, or deployment of Divi 5 pages. It orchestrates the 4-phase workflow: Analysis, Design Research, Mapping, and Execution. Brand vars are synced to Divi Customizer via `wp brand sync` (→ et_divi + gcids + gvids).
---

# DAW-Skill: Divi Agentic Workflow Orchestrator (v5.0)

Motor definitivo para la construcción de sitios con **Divi 5.10.1 Native**. Aplica separación estricta de responsabilidades mediante una orquestación modular de **4 fases**.

> [!CAUTION]
> **Regla de oro**: cada fase produce un **artefacto escrito obligatorio** antes de que la siguiente fase comience. No existe "la fase se hizo en mi cabeza". Sin artefacto, la fase no terminó.

---

## ⚡ Pipeline Real

```
Brand vars (_design_vars.json)
  → wp brand sync
    → wp_options['et_divi'] (Customizer global)
    → divitheme.json (presets + strategy)
    → gcids via GlobalData::set_global_colors()
  → page-defs/<slug>/manifest.json + sections/*.json
  → python workspace/combine.py → <slug>-combined.json
  → wp agentic deploy_page → post_content en WP
```

---

## ⚡ Brand Sync (único comando)

```powershell
.\wp brand sync <slug>
```

Sincroniza **todo** en un solo paso:

| Destino | Qué |
|---------|-----|
| `wp_options['et_divi']` | 38+ colores, 5 fuentes, logo, font sizes/weights → tema global |
| `divitheme.json` | Solo presets + strategy (los tokens viven en los stores nativos de Divi) |
| Global Colors (gcids) | Colores vía `GlobalData::set_global_colors()` |
| Global Variables (gvids) | Radios, espacios y fuentes vía `GlobalData::set_global_variables()` — variables nativas editables en VB |

No necesita `global_colors sync` aparte. `wp brand sync` respeta el **quality gate**: falla si no hay `approve` con `vars_hash` coincidente o si los vars cambiaron sin re-validar (bypass: `--force`).

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

**Formato de page-def actual (una carpeta por página):**
1. Crear la carpeta y el manifiesto `site/<DAW_SITE>/page-defs/<slug>/manifest.json`:
```json
{
  "_manifest": "v1",
  "title": "Mi Página",
  "slug": "mi-pagina",
  "sections": ["sections/hero.json", "sections/features.json"]
}
```
2. Crear cada sección en `site/<DAW_SITE>/page-defs/<slug>/sections/<nombre>.json` (con `"_section": true`).
3. CSS freeForm por sección en `site/<DAW_SITE>/page-defs/<slug>/css/<nombre>.css` (mismo nombre que la sección; lo inyecta `combine.py`). **⚠️ Ningún `<` en ese CSS** (regla #15 — `wp_strip_all_tags` trunca).
4. Combinar: `python workspace/combine.py <manifest> --out <combined>.json` → `<slug>-combined.json`
5. Desplegar con el wrapper `.\workspace\deploy.ps1 -Slug <slug> -Title "..."` (hace combine + `deploy_page` + flush).

**Verificación antes de entregar a Fase 4:**
- [ ] Ningún tipo `et_pb_*` en el JSON
- [ ] Ningún hex hardcodeado — todo es `{{design:color:*}}`
- [ ] Ningún preset inexistente (verificar contra `divitheme.json`)
- [ ] Posiciones de gradient sin `%`
- [ ] Las 6 leyes del Design Brief están reflejadas
- [ ] Pasa `php divi-agentic-core/bin/lint_page_def.php --def=<slug>-combined.json`

> ⛔ **STOP**: si el page-def no pasa la verificación, NO iniciar Fase 4.

---

### Fase 4 — Ejecución CLI (El Ingeniero)

- *Leer*: [`references/engineer.md`](references/engineer.md)
- *Meta*: Desplegar con un solo comando. **Regla #5: usar siempre los wrappers**, nunca comandos sueltos.

**Flujo recomendado (wrapper — combina, despliega y flushea caché):**
```powershell
# Página
.\workspace\deploy.ps1 -Slug <slug> -Title "Título de la página"

# Template global (header/footer/body) — ver references/engineer.md §Templates
.\workspace\deploy-template.ps1 -UseOn "singular:post_type:page:all" -Title "Todas las páginas"
```

**Equivalente directo (solo si el wrapper no aplica):**
```powershell
python workspace/combine.py `
  site/<DAW_SITE>/page-defs/<slug>/manifest.json `
  --out site/<DAW_SITE>/page-defs/<slug>/<slug>-combined.json

.\wp.bat agentic deploy_page `
  --title="Título de la página" `
  --slug="<slug>" `
  --schema="site/<DAW_SITE>/page-defs/<slug>/<slug>-combined.json" `
  --design-system="site/<DAW_SITE>/design-system/divitheme.json"
```

> [!IMPORTANT]
> `build_page.php` es **legacy**. El Layout Engine fue refactorizado a renderers modulares (`inc/core/renderers/*.php`) que soportan namespaces de terceros (`dgpc/*`, `dac/*`).

**Verificación post-deploy:** `php divi-agentic-core/bin/verify_page.php --slug=<slug>` y `php divi-agentic-core/bin/check_frontend.php <slug>`. Para inspeccionar módulos y schemas: `bin/inspect-module.php`, `bin/extract-module-meta.php`, `bin/generate-module-schema.php` (ver `divi-agentic-core/bin/AGENTS.md`).

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
# 2. Validar y aprobar (quality gate):
.\wp brand validate <DAW_SITE> [--suggest]
.\wp brand approve <DAW_SITE>          # persiste .design-pass con vars_hash
# 3. Sincronizar todo:
.\wp brand sync <DAW_SITE>             # falla si no hay approve o si vars cambiaron
#    → et_divi (Customizer) + divitheme.json (presets+strategy) + gcids + gvids
```

- **Contenedores**: usar decoration nativa (background, spacing) en vez de clases.
- **Tipografía**: usar `headingFont` y `bodyFont` con tokens `{{design:font:*}}`.
- **Colores**: usar tokens `{{design:color:*}}` — nunca hex hardcodeados.
- **Animaciones**: usar decoration.animation cuando sea posible.
- **CSS freeForm**: guardarlo en `css/<sección>.css` (lo inyecta `combine.py`). ⚠️ **Ningún `<` en ninguna parte** — `wp_strip_all_tags()` trunca el CSS (regla #15 de AGENTS.md).

### Bloques Divi 5 — Regla Fundamental
**NO usar `divi/code` como comodín.** Consultar siempre `blocks-dictionary.md` primero.

> [!CAUTION]
> **PROHIBIDO** usar `et_pb_*` (shortcodes Divi 4). El Layout Engine espera únicamente `divi/*`.

`DAW_SITE` en `.env` define qué directorio `site/` usar. `wp brand sync` auto-descubre la ruta:

```powershell
# Editar .env: DAW_SITE=nueva-marca
# Editar site/<DAW_SITE>/brand/_design_vars.json
# Sincronizar todo:
.\wp brand sync
```

---

## Fuente de Verdad (Ground Truth)

| Recurso | Archivo | Propósito |
|---------|---------|-----------|
| Diccionario de bloques | `references/blocks-dictionary.md` | Guía de 102 módulos (+ bloques 5.10 y Loop Builder) |
| Estándares del proyecto | `references/knowledge.md` | Reglas técnicas |
| Lógica del Diseñador | `references/designer.md` | Mapeo semántico → page-defs (§8 gotchas, §9 responsive) |
| Lógica del Ingeniero | `references/engineer.md` | CLI, deploy, verificación (§Templates incl. trampa R14) |
| Pipeline DAW | `../AGENTS.md` | Fuente de verdad del flujo completo |
| Brand Sync | `wp brand sync` | Mapeo `_design_vars.json` → `et_divi` + gcids + gvids |
| Inputs del Brand | `../references/design-system-inputs.md` | Formatos de `_design_vars.json`, brief JSON |
| Scripts de inspección | `../divi-agentic-core/bin/AGENTS.md` | check-example, lint_page_def, verify_page, inspect-*, generate-module-schema… |
| Referencia externa de módulos | `../../test/divi5-skill/DIVI5-*.md` | Recetas y schema render-verificados de Divi 5.10 (componentes, presets, MCP) |
| VIE package | `../_archive/vie/vie/README.md` | Visual Impact Engine (archivado, no usar) |
