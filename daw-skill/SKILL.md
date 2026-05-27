---
name: daw-skill
description: The Unified Source of Truth for the Divi Agentic Workflow (DAW). Use this for any task involving the creation, modification, or deployment of Divi 5 pages. It orchestrates the 4-phase agentic workflow: Analysis, Design Research, Mapping, and Execution.
---

# DAW-Skill: Divi Agentic Workflow Orchestrator (v4.0)

Motor definitivo para la construcción de sitios con **Divi 5.5.0 Native**. Aplica separación estricta de responsabilidades mediante una orquestación modular de **4 fases**.

---

## Principio Central: Orquestación Modular

Toda tarea DEBE pasar por estas cuatro fases en orden. Cada fase tiene su módulo de referencia:

1. **Fase 1: Análisis Semántico (El Arquitecto)**
   - *Consultar*: [`references/blocks-dictionary.md`](references/blocks-dictionary.md) (Guía de Decisión Semántica + índice)
   - *Leer*: [`references/architect.md`](references/architect.md)
   - *Meta*: Definir estructura semántica y objetivos de negocio. Para cada elemento, elegir el bloque Divi 5 correcto consultando el diccionario.
   - *Entrega*: Plan Semántico JSON

2. **Fase 2: Investigación de Diseño (Design Lead)**
   - *Consultar* (integración externa opcional): [`ui-ux-pro-max` skill](../ui-ux-pro-max/SKILL.md) para tendencias, paletas y patrones avanzados
   - *Leer*: [`references/design-lead.md`](references/design-lead.md)
   - *Meta*: Investigar dirección visual moderna, validar contra principios UX críticos, documentar decisiones de diseño.
   - *Entrega*: Documento de dirección visual + UX validation + decisiones documentadas

3. **Fase 3: Mapeo Visual (El Diseñador)**
   - *Consultar*: [`references/blocks-dictionary.md`](references/blocks-dictionary.md) (atributos exactos + ejemplos de schema)
   - *Leer*: [`references/designer.md`](references/designer.md)
   - *Meta*: Traducir el plan semántico + dirección visual a un JSON Schema con bloques `divi/*`, tokens `{{design:*}}` y decoration nativa.
   - *Entrega*: Schema en `workspace/pages/<slug>.json`

4. **Fase 4: Ejecución CLI (El Ingeniero)**
   - *Leer*: [`references/engineer.md`](references/engineer.md)
   - *Meta*: Desplegar vía `.\wp.bat agentic deploy_page --design-system=...`, limpiar caché y verificar persistencia en DB.
   - *Entrega*: WP Post ID confirmado

---

## Fuente de Verdad (Ground Truth)

Este skill es **100% autocontenido**. Prioriza siempre estos archivos internos:

| Recurso | Archivo | Propósito |
| :--- | :--- | :--- |
| Diccionario de bloques | [`references/blocks-dictionary.md`](references/blocks-dictionary.md) | Guía completa de 94+ bloques, cuándo usar cada uno, atributos y ejemplos |
| Estándares del proyecto | [`references/knowledge.md`](references/knowledge.md) | Variables CSS, directorios, reglas técnicas |
| Lógica del Diseñador | [`references/designer.md`](references/designer.md) | Mapeo semántico → bloques, tokens, presets, decoration |
| Lógica del Ingeniero | [`references/engineer.md`](references/engineer.md) | Comandos CLI, deploy, verificación, producción |
| Lógica del Arquitecto | [`references/architect.md`](references/architect.md) | Análisis semántico |
| Dirección de Diseño | [`references/design-lead.md`](references/design-lead.md) | Investigación UX/UI, validación, decisiones de diseño |
| Índice de Bloques Divi 5 | [`references/blocks-index.json`](references/blocks-index.json) | Índice ligero (16 KB): slug, nombre, categoría, children de los 102 bloques. Para atributos detallados: `php divi-agentic-core/bin/extract-module-meta.php <slug>` |
| Metadata completa (on-demand) | `divi-agentic-core/data/_all_modules_metadata.php` (2.6 MB) | Schema oficial completo de Divi 5. El trait `Module_Metadata` lo lee directamente. No se carga en sesión DAW a menos que se necesite. |

---

## Reglas de Diseño

### Dependencia del Sistema de Diseño
Consultar el archivo `workspace/design-system/<proyecto>.json` como referencia estricta de estilo, tokens y patrones visuales.
- **Contenedores**: usar decoration nativa (background, spacing) en vez de clases.
- **Tipografía**: usar `headingFont` y `bodyFont` con tokens `{{design:font:*}}`.
- **Colores**: usar tokens `{{design:color:*}}` — nunca hex hardcodeados.
- **Animaciones**: usar decoration.animation cuando sea posible.

### Investigación de Diseño (Design Lead)
El Design Lead es el guardián de la calidad UX/UI del proyecto. Sus decisiones de dirección visual y validaciones son vinculantes para el Diseñador. Consultar [`references/design-lead.md`](references/design-lead.md) para:
- Dirección de estilo (Agnóstica y Ultra-Premium)
- Checklist UX crítica (contraste, touch targets, jerarquía)
- Documentación de decisiones de diseño
- Integración externa con `ui-ux-pro-max` skill para deep dives

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
