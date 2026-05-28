---
name: daw-skill
description: The unified source of truth for the local Divi Agentic Workflow (DAW) in divitheme. Use this for any task involving the creation, modification, or deployment of Divi 5 pages. It orchestrates the 4-phase workflow: Analysis, Design Research, Mapping, and Execution.
---

# DAW-Skill: Divi Agentic Workflow Orchestrator (v4.0)

Motor definitivo para la construcción de sitios con **Divi 5.5.0 Native**. Aplica separación estricta de responsabilidades mediante una orquestación modular de **4 fases**.

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
- Para listar los Global Colors activos: `wp agentic global_colors list`

> **Regla**: Los colores se sincronizan **una vez por cambio de design system**, no por página. El sync NO se ejecuta automáticamente en `deploy_page` — es una decisión consciente del operador.

---

## Principio Central: Orquestación Modular

Toda tarea DEBE pasar por estas cuatro fases en orden. Cada fase tiene su módulo de referencia:

1. **Fase 1: Análisis Semántico (El Arquitecto)**
   - *Consultar*: [`references/blocks-dictionary.md`](references/blocks-dictionary.md) (Guía de Decisión Semántica + índice)
   - *Leer*: [`references/architect.md`](references/architect.md)
   - *Meta*: Definir estructura semántica y objetivos de negocio. Para cada elemento, elegir el bloque Divi 5 correcto consultando el diccionario.
   - *Entrega*: Plan Semántico JSON

2. **Fase 2: Investigación de Diseño (Design Lead)**
   - *Consultar* (opcional): [`ui-ux-pro-max` skill](ui-ux-pro-max/SKILL.md) para tendencias, paletas y patrones avanzados
   - *Leer*: [`references/design-lead.md`](references/design-lead.md)
   - *Meta*: Investigar dirección visual moderna, validar contra principios UX críticos, documentar decisiones de diseño.
   - *Entrega*: Documento de dirección visual + UX validation + decisiones documentadas

3. **Fase 3: Mapeo Visual (El Diseñador)**
   - *Consultar*: [`references/blocks-dictionary.md`](references/blocks-dictionary.md) (atributos exactos + ejemplos de schema)
   - *Leer*: [`references/designer.md`](references/designer.md)
   - *Meta*: Construir un archivo JSON en `site/<DAW_SITE>/page-defs/<slug>.json` con la definición de la página. `build_page.php` lo procesa: carga módulos, resuelve `{{design:color:*}}` → `var(--gcid-*)`, expande presets inline, normaliza posiciones de gradient. Ver `site/bibliotheca/page-defs/home.json` como plantilla.
   - *Entrega*: Archivo de definición en `site/<DAW_SITE>/page-defs/<slug>.json`

4. **Fase 4: Ejecución CLI (El Ingeniero)**
   - *Leer*: [`references/engineer.md`](references/engineer.md)
   - *Meta*: Desplegar con un solo comando:
     ```
      .\php.bat DAW_bundle/divi-agentic-core/bin/build_page.php ^
        --def=DAW_bundle/site/bibliotheca/page-defs/<slug>.json ^
        --deploy
     ```
     `build_page.php` construye el schema (resuelve tokens, expande presets) y llama a `wp agentic deploy_page`. El Layout Engine convierte `var(--gcid-*)` → `$variable()` syntax en post_content.
   - *Entrega*: WP Post ID confirmado

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
| Dirección de Diseño | [`references/design-lead.md`](references/design-lead.md) | Investigación UX/UI, validación, decisiones de diseño |
| Índice de Bloques Divi 5 | [`references/blocks-index.json`](references/blocks-index.json) | Índice ligero (16 KB): slug, nombre, categoría, children de los 102 bloques. Para atributos detallados: `php DAW_bundle/divi-agentic-core/bin/extract-module-meta.php <slug>` |
| Metadata completa (on-demand) | `DAW_bundle/divi-agentic-core/data/_all_modules_metadata.php` (2.6 MB) | Schema oficial completo de Divi 5. El trait `Module_Metadata` lo lee directamente. No se carga en sesión DAW a menos que se necesite. |

---

## Reglas de Diseño

### Dependencia del Sistema de Diseño

**El design system se genera automáticamente.** No se edita a mano.

Usar `build_design_system.py` (v2.0, data-driven) para crear o modificar el sistema de diseño:

```powershell
# 1. Crear (o modificar) archivos de variables y presets en su carpeta de marca:
#    DAW_bundle/site/<DAW_SITE>/brand/_design_vars.json
#    DAW_bundle/site/<DAW_SITE>/brand/_design_presets.json (57 presets: section/text/module/animation/scroll/hover)
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
El Design Lead es el guardián de la calidad UX/UI del proyecto. Sus decisiones de dirección visual y validaciones son vinculantes para el Diseñador. Consultar [`references/design-lead.md`](references/design-lead.md) para:
- Dirección de estilo (Agnóstica y Ultra-Premium)
- Checklist UX crítica (contraste, touch targets, jerarquía)
- Documentación de decisiones de diseño
- Integración con [`ui-ux-pro-max` skill](ui-ux-pro-max/SKILL.md) para deep dives

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
