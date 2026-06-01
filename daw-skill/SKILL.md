---
name: daw-skill
description: The unified source of truth for the local Divi Agentic Workflow (DAW) in divitheme. Use this for any task involving the creation, modification, or deployment of Divi 5 pages. It orchestrates the 4-phase workflow: Analysis, Design Research, Mapping, and Execution.
---

# DAW-Skill: Divi Agentic Workflow Orchestrator (v4.1)

Motor definitivo para la construcción de sitios con **Divi 5.5.0 Native**. Aplica separación estricta de responsabilidades mediante una orquestación modular de **4 fases**.

> [!CAUTION]
> **Regla de oro**: cada fase produce un **artefacto escrito obligatorio** antes de que la siguiente fase comience. No existe "la fase se hizo en mi cabeza". Sin artefacto, la fase no terminó.

---

## ⚠️ Prerrequisito: Sistema de Colores Globales (gcid)

Antes de desplegar cualquier página, el design system debe tener sus **colores sincronizados** con Divi 5 como Global Colors (`gcid-*`).

### ¿Por qué?
Los colores registrados como `gcid-*` son visibles y seleccionables en el **color picker del Visual Builder** de Divi, se renderizan vía CSS custom properties (`var(--gcid-ink)`), y son editables desde el Customizer sin re-deploy.

### ¿Cuándo sincronizar?

| Cuándo | Comando |
|--------|---------|
| **Una vez, al crear el design system** | `wp agentic global_colors sync --design-system="DAW_bundle/site/bibliotheca/design-system/divitheme.json"` |
| **Cada vez que cambien los colores en el JSON** | Mismo comando. El sistema detecta cambios vía hash. |
| **Para verificar estado** | `wp agentic global_colors status --design-system="DAW_bundle/site/bibliotheca/design-system/divitheme.json"` |

### Señal de estado
- El sistema almacena un **hash MD5** de los colores sincronizados en la opción `_dac_gcid_hash`.
- El comando `deploy_page` verifica este hash: si existe, resuelve `{{design:color:*}}` como `var(--gcid-*)`. Si no existe, emite un **warning** y resuelve a hex.

> **Regla**: Los colores se sincronizan **una vez por cambio de design system**, no por página. El sync NO se ejecuta automáticamente en `deploy_page` — es una decisión consciente del operador.

---

## Principio Central: Orquestación Modular con Contratos de Fase

Toda tarea DEBE pasar por estas cuatro fases en orden. Cada fase produce un artefacto concreto. La siguiente fase no comienza hasta que el artefacto esté escrito.

### ⚡ Pipeline Activo: VIE v2.0 + SchemaRegistry (Recomendado)

El DAW usa el **Visual Impact Engine (VIE v2.0)** como motor determinístico de producción. Lee un brief JSON rico y construye `plans/<slug>.json` usando `SchemaRegistry` (auto-descubrimiento de 102 módulos Divi 5) + `ModuleBuilder` (reglas visuales determinísticas).

El antiguo pipeline DIE (ML, 877 templates, clasificador TF-IDF) fue archivado en `_archive/die_pipeline/`.

**Flujo automático UX-Pro → VIE v2.0 (recomendado para páginas nuevas):**
```powershell
# 1. Generar brief rico con arrays de contenido real (Fase 1)
python DAW_bundle/workspace/automation/ux_pro_brief_generator.py --query "SaaS Landing Page" --out site/<DAW_SITE>/briefs/<slug>.json

# 2. VIE mapea secciones → módulos Divi 5 nativos (Fases 2-3)
python -B DAW_bundle/ml-dataset/artifacts/visual_impact_engine.py --brief-file=site/<DAW_SITE>/briefs/<slug>.json --site <DAW_SITE> --output=site/<DAW_SITE>/plans/<slug>.json

# 3. Build + Deploy (Fase 4)
.\php.bat DAW_bundle/divi-agentic-core/bin/build_page.php --def=site/<DAW_SITE>/plans/<slug>.json --deploy
```

| Escenario | Flujo |
|-----------|-------|
| Nueva página desde prompt | `ux_pro_brief_generator.py` → `visual_impact_engine.py` → `build_page.php` |
| Página con diseño muy específico | Skill manual 4 fases (abajo) |
| Iteración sobre plan existente | Editar `plans/<slug>.json` → `build_page.php` |

**Cuándo usar cada flujo:** Si el usuario da un prompt natural sin textos definidos, usar el pipeline automático UX-Pro → VIE. Si entrega textos exactos, wireframes o requiere control fino, usar las 4 fases manuales abajo.

---

### Fase 1 — Análisis Semántico (El Arquitecto)

- *Consultar*: [`references/blocks-dictionary.md`](references/blocks-dictionary.md) (Guía de Decisión Semántica + índice)
- *Leer*: [`references/architect.md`](references/architect.md)
- *Meta*: Definir estructura semántica y objetivos de negocio. Para cada sección, elegir el bloque Divi 5 correcto consultando el diccionario.

#### 💡 Criterio de uso del Generador de Briefs (`generate_brief.py`):
El uso de `generate_brief.py` (con LLM) y de `ux_pro_brief_generator.py` (determinístico BM25) se rige por:
1. **Usar `ux_pro_brief_generator.py` para páginas nuevas** que no tienen estructura definida. Genera briefs ricos con arrays de datos: `items[]`, `testimonials[]`, `phases[]`, `features[]`.
2. **No usar si ya existe un brief** en `site/<DAW_SITE>/briefs/<slug>.json`.
3. **Ir directo al plan** si el usuario entrega textos exactos, wireframes o estructura definida.

**Artefacto obligatorio — Brief JSON** (escribirlo antes de continuar):
```json
{
  "title": "Página",
  "slug": "slug",
  "sections": [
    {"section_type": "hero", "title": "...", "text": "...", "btn_primary_text": "..."},
    {"section_type": "features", "items": [{"title": "...", "icon": "", "text": "..."}]},
    {"section_type": "cta", "title": "...", "text": "...", "btn_primary_text": "..."}
  ]
}
```
Tipos de `section_type` soportados por VIE v2.0: `hero`, `hero-centered`, `features`, `content`, `content-list`, `stats`, `testimonials`, `pricing`, `faq`, `icon-list`, `timeline`, `contact`, `process`, `team`, `gallery`, `logos`, `cta`.

> ⛔ **STOP**: si el Brief JSON no está escrito, NO iniciar Fase 2.

---

### Fase 2 — Investigación de Diseño (Design Lead)  ← **BLOQUEANTE**

- *Leer*: [`references/design-lead.md`](references/design-lead.md) — **leer completo antes de continuar**
- *Consultar* (opcional): [`ui-ux-pro-max` skill](ui-ux-pro-max/SKILL.md) para tendencias y patrones avanzados
- *Meta*: Validar el Plan Semántico contra las **6 Leyes de Calidad Autónoma** de design-lead.md §3, documentar la dirección visual y hacer handoff formal al Diseñador.

**El Design Lead es un bloqueante real**. Si cualquiera de las 6 leyes no se cumple en el plan, el agente DETIENE el flujo, propone alternativa, y re-valida antes de continuar. No es un checklist decorativo.

**Artefacto obligatorio — Design Brief** (escribirlo antes de continuar):
```
Estilo visual: <editorial / modern / premium / minimal / dramatic>
Secciones con alternancia de fondo confirmada: [✓ ley 1]
  sec-1: section:hero-dark
  sec-2: section:light
  sec-3: section:white
  sec-4: section:dark
  ...
Titular hero: preset text:display-xl o text:hero-title [✓ ley 2]
Espacio negativo: padding mínimo 2xl en secciones [✓ ley 3]
Hover documentado en: <lista de elementos clickeables> [✓ ley 4]
Ancla visual por sección: <elemento dominante de cada sección> [✓ ley 5]
Escala responsiva hero: desktop Xpx / tablet Ypx / mobile Zpx [✓ ley 6]
Decisiones documentadas:
  - <decisión>: <fundamento>
Restricciones para el Diseñador:
  - <lo que no debe hacerse>
```
> ⛔ **STOP**: si el Design Brief no está escrito con las 6 leyes validadas, NO iniciar Fase 3.

---

### Fase 3 — Mapeo Visual (El Diseñador)

- *Consultar*: [`references/blocks-dictionary.md`](references/blocks-dictionary.md) y [`references/designer.md`](references/designer.md)
- *Meta*: Construir el archivo JSON en `site/<DAW_SITE>/page-defs/<slug>.json` implementando **exactamente** el Design Brief de Fase 2.

**Sobre el catálogo semántico** (`search_catalog.py` + `workspace/sections/catalog/`):
Los 877 templates compilados son una fuente de referencia de diseño real — layouts de Divi Plus probados en producción. El flujo correcto de uso:

1. Buscar con `python DAW_bundle/workspace/automation/search_catalog.py --query "descripción" --limit 3`
2. Abrir el JSON indicado en `path` e inspeccionar: estructura de filas, proporciones de columnas, valores de spacing, patrones de anidación, composición de módulos
3. Extraer lo útil: márgenes, paddings, decisiones de layout, ritmo visual
4. **Traducir obligatoriamente** todo lo extraído a tokens `{{design:*}}` y bloques `divi/*` antes de escribirlo en el page-def

Lo que **NO** se hace con el catálogo:
- No copiar colores hex → reemplazar por `{{design:color:*}}`
- No copiar imágenes de demo → reemplazar por assets reales o `{{SITE_URL}}/...`
- No copiar el JSON completo como sección → traducir estructura a page-def nativo
- No dejar que `orchestrate_page.php` lo inyecte automáticamente (ese script contamina el resultado)

El catálogo vale exactamente en la medida en que el agente lo lee con criterio, extrae lo útil, y lo traduce. Ver [`references/designer.md §8`](references/designer.md#8-uso-del-buscador-semántico-de-referencias-catálogo-divi-plus) para el ciclo completo de ingeniería inversa.

**Artefacto obligatorio**:
```
Archivo: DAW_bundle/site/<DAW_SITE>/page-defs/<slug>.json
```
Verificación antes de entregar a Fase 4:
- [ ] Ningún tipo `et_pb_*` en el JSON
- [ ] Ningún hex hardcodeado — todo es `{{design:color:*}}`
- [ ] Ningún `button_text: ""` ni `src: ""` — todo el contenido es real
- [ ] Ningún preset inexistente (verificar contra `_design_presets.json`)
- [ ] Posiciones de gradient sin `%`
- [ ] Las 6 leyes del Design Brief están reflejadas en el JSON

> ⛔ **STOP**: si el page-def no pasa la verificación, NO iniciar Fase 4.

---

### Fase 4 — Ejecución CLI (El Ingeniero)

- *Leer*: [`references/engineer.md`](references/engineer.md)
- *Meta*: Desplegar con un solo comando:
  ```powershell
  .\php.bat DAW_bundle/divi-agentic-core/bin/build_page.php ^
    --def=DAW_bundle/site/bibliotheca/page-defs/<slug>.json ^
    --deploy --verify
  ```
  `build_page.php` construye el schema (resuelve tokens, expande presets) y llama a `wp agentic deploy_page`. El Layout Engine convierte `var(--gcid-*)` → `$variable()` syntax en post_content.

**Artefacto obligatorio**:
```
WP Post ID: <id>
URL: <http://...>
Verificación: [✓ bloques Divi 5 presentes] [✓ gcids resueltos] [✓ sin tokens sin resolver]
```
> ⛔ **STOP**: si el deploy falla o la verificación reporta errores, el Ingeniero diagnostica y re-ejecuta antes de declarar la tarea completa.

---

## Fuente de Verdad (Ground Truth)

Este skill es **100% autocontenido** para el proyecto local `divitheme`. Prioriza siempre estos archivos internos:

| Recurso | Archivo | Propósito |
| :--- | :--- | :--- |
| Diccionario de bloques | [`references/blocks-dictionary.md`](references/blocks-dictionary.md) | Guía completa de 102 módulos, cuándo usar cada uno, atributos y ejemplos |
| Estándares del proyecto | [`references/knowledge.md`](references/knowledge.md) | Variables CSS, directorios, reglas técnicas |
| Lógica del Diseñador | [`references/designer.md`](references/designer.md) | Mapeo semántico → bloques, tokens, presets, decoration |
| Lógica del Ingeniero | [`references/engineer.md`](references/engineer.md) | Comandos CLI, deploy, verificación, producción |
| Lógica del Arquitecto | [`references/architect.md`](references/architect.md) | Análisis semántico |
| Dirección de Diseño | [`references/design-lead.md`](references/design-lead.md) | **Leyes de calidad autónoma (bloqueante), investigación UX/UI, decisiones** |
| Índice de Bloques Divi 5 | [`references/blocks-index.json`](references/blocks-index.json) | Índice ligero (16 KB): slug, nombre, categoría, children de los 102 bloques. Para atributos detallados: `php DAW_bundle/divi-agentic-core/bin/extract-module-meta.php <slug>` |
| Metadata completa (on-demand) | `DAW_bundle/divi-agentic-core/data/_all_modules_metadata.php` (2.6 MB) | Schema oficial completo de Divi 5. No se carga en sesión DAW a menos que se necesite. |

---

## Reglas de Diseño

### Dependencia del Sistema de Diseño

**El design system se genera automáticamente.** No se edita a mano.

Usar `build_design_system.py` (v3.0, design intelligence) para crear o modificar el sistema de diseño:

```powershell
# 1. Crear (o modificar) archivos de variables y presets en su carpeta de marca:
#    DAW_bundle/site/<DAW_SITE>/brand/_design_vars.json
#    DAW_bundle/site/<DAW_SITE>/brand/_design_presets.json (64 presets: section/text/module/divider/animation/scroll/hover)
#    (solo las variables que cambian — el resto usa defaults ultra-pro)

# 2. Generar design system completo:
$env:DAW_SITE="<DAW_SITE>"
python DAW_bundle/workspace/build_design_system.py

# 3. Sincronizar colores globales:
.\wp.bat agentic global_colors sync `
  --design-system="DAW_bundle/site/bibliotheca/design-system/divitheme.json"
```

El generador auto-descubre tokens por prefijo (`color_`, `font_`, `radius_`, `space_`) de cualquier archivo de variables — no hay nombres hardcodeados en Python. Funciona con cualquier marca sin modificar el script.

El archivo generado `DAW_bundle/site/bibliotheca/design-system/divitheme.json` es la referencia estricta de estilo, tokens y patrones visuales.

- **Contenedores**: usar decoration nativa (background, spacing) en vez de clases.
- **Tipografía**: usar `headingFont` y `bodyFont` con tokens `{{design:font:*}}`.
- **Colores**: usar tokens `{{design:color:*}}` — nunca hex hardcodeados.
- **Animaciones**: usar decoration.animation cuando sea posible.

### Investigación de Diseño (Design Lead)
El Design Lead es el guardián de la calidad UX/UI del proyecto. Sus decisiones de dirección visual y validaciones son **vinculantes y bloqueantes** para el Diseñador. Consultar [`references/design-lead.md`](references/design-lead.md) — las 6 Leyes de Calidad Autónoma están al inicio del documento y deben completarse antes del handoff.

### Bloques Divi 5 — Regla Fundamental
**NO usar `divi/code` como comodín.** Consultar siempre `blocks-dictionary.md` primero para encontrar el bloque nativo correcto. `divi/code` es el último recurso.

> [!CAUTION]
> **PROHIBIDO** usar `et_pb_*` (shortcodes Divi 4). El motor `Layout_Engine` espera únicamente el namespace `divi/*`.

### Compatibilidad con Visual Builder
- Todo CSS global debe estar en el Customizer de WordPress.
- Los estilos inline dentro de `content` se preservan en el editor visual.
- La decoration nativa (`headingFont`, `bodyFont`, `border`, etc.) es completamente editable en Divi 5.

---

*Este skill es la ÚNICA fuente autorizada para el flujo DAW. Reemplaza y depreca cualquier referencia anterior a divi-agentic-core como fuente de diseño.*
