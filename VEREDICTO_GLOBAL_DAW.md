# Veredicto Global DAW — Síntesis de 3 Diagnósticos

**Fecha:** 2026-05-30
**Versión:** v5.0 (unificada)
**Basado en:** Análisis original + Diagnóstico 1 (integración ML) + Diagnóstico 2 (puntos de ruptura)

---

## 1. Mapa de los 3 Diagnósticos

| Eje | Diagnóstico 1 (integración ML) | Diagnóstico 2 (puntos de ruptura) | Diagnóstico 3 (flujo global) |
|-----|------|-------|-------|
| **Enfoque** | La capa ML (DIE) está presente pero aislada | Fallos técnicos concretos en el pipeline | Fragmentación del entorno, arquitectura partida |
| **Break principal** | No hay hooks que invoquen ML antes del build | `embeddings.pkl` en ruta inexistente | `.env` y junction link apuntan al bundle old |
| **Hallazgos** | 10 breaks (tokens, page-defs, wrappers, docs, deps, state, WPDS, logs, git) | 7 breaks (DIE, catálogo, artefactos, validación, gcids, variants, post-compose) | 12 breaks (path errors, fork huérfano, 4 fases sin enforcement) |
| **Tono** | "El ML está allí pero no se usa" | "Cosas específicas están rotas" | "El sistema no puede funcionar como está diseñado" |

---

## 2. Síntesis Unificada: Los 3 Problemas Raíz

### 🔴 Problema Raíz #1: TRIPLE ARQUITECTURA SIN INTEGRACIÓN

El DAW tiene **tres sistemas paralelos que no se comunican**:

```
Sistema 1: SKILL (4 fases manuales)
   ↓ produce page-defs manuales (si el agente sigue el proceso)
   ↓ pero no hay enforcement → quality variable

Sistema 2: PIPELINE PHP AUTOMÁTICO
   ↓ orchestrate_page.php → compose → post-compose → build
   ↓ funciona mecánicamente, pero el input es pobre
   ↓ produce páginas genéricas con contenido de catálogo ajeno

Sistema 3: ML / DIE (Design Intelligence Engine)
   ↓ 4 artefactos inteligentes (A, B, C, D) pre-construidos
   ↓ design_intelligence.py listo para orquestar
   ↓ PERO: no está conectado al pipeline real
```

**Cada sistema resuelve un problema diferente pero ninguno resuelve el problema completo.**

| Sistema | Qué hace bien | Qué no hace |
|---------|---------------|-------------|
| Skill (4 fases) | Dirección de diseño, semántica, calidad visual | Automatización, generación de JSON |
| Pipeline PHP | Build robusto, resolución de tokens, deploy | Decisión de diseño, variedad visual |
| ML/DIE | Variedad estructural, clasificación semántica | Identidad de marca, contenido real |

**Evidencia concreta:**

- El DIE carga `semantic-index.pkl` (existe), `section-patterns.json` (existe), `module-affinities.json` (existe), `content-classifier.pkl` (existe). Los 4 artefactos funcionan.
- El orquestador PHP (`orchestrate_page.php`) llama al DIE vía `shell_exec()` y parsea su output.
- Los templates del catálogo (877 .section.json) existen y están compilados.
- `design-patterns.json` existe en ml-die workspace.

**Pero nada de esto se usa porque:**

1. `.env` define `WORKSPACE_DIR=DAW_bundle/workspace` → el ecosistema apunta al bundle **old**
2. El junction link del plugin WP apunta a `DAW_bundle/divi-agentic-core/`
3. El `.agents/skills/daw-skill/SKILL.md` delega a `DAW_bundle/daw-skill/SKILL.md`
4. `AGENTS.md` raíz referencia `DAW_bundle/` en todos los comandos

**El ml-die es funcional pero está aislado. El old es el que se ejecuta pero no tiene ML.**

---

### 🔴 Problema Raíz #2: EL PIPELINE AUTOMÁTICO NO PUEDE DISEÑAR

El pipeline PHP es un excelente **motor de renderizado** pero un pésimo **diseñador**. El flujo automático (`orchestrate_page.php`) hace esto:

```
brief YAML → elige template del catálogo → inyecta slots → compose → build
```

El problema es que los templates del catálogo contienen:
- **Colores RGB hardcodeados** que no respetan el design system
- **Imágenes demo** de otros proyectos (diviplus.io, unsplash, placehold.co)
- **Estructuras de Divi 4** que el build debe traducir
- **Contenido placeholder** en slots que `compose_page.php` rellena con strings vacíos

El `post_compose.php` intenta limpiar esto (inyecta presets de marca, elimina imágenes demo), pero es una **capa correctiva sobre un problema de origen**. El daño ya está hecho cuando el template se selecciona.

**Causa raíz:** El pipeline automático trata el diseño como un problema de _lookup_ (brief → template), no como un problema de _composición_ (brief → diseñar estructura → escribir JSON a medida).

---

### 🔴 Problema Raíz #3: EL SKILL DE 4 FASES NO TIENE ENFORCEMENT

El skill `daw-skill/SKILL.md` v4.1 define artefactos obligatorios y puntos `⛔ STOP`, pero:

- No hay validación programática de que la Fase 2 (Design Lead) haya ocurrido
- No hay lint automático del page-def contra las 6 Leyes
- No hay verificación de que los presets existen en `_design_presets.json`
- No hay un archivo de "Design Brief" que se guarde y verifique

**El skill es una convención, no un contrato.** El agente puede saltarse la Fase 2, escribir un JSON genérico, y el pipeline lo desplegará sin protestar.

---

## 3. Mapa de Calor de los 29 Breaks (3 diagnósticos combinados)

| # | Break | Gravedad | Diagnóstico origen | Sistemas afectados |
|---|-------|----------|--------------------|--------------------|
| 1 | `.env` apunta a `DAW_bundle/`, no a ml-die | 🔴 P0 | 3 | Entorno completo |
| 2 | Junction link del plugin apunta al bundle old | 🔴 P0 | 3 | Plugin WP |
| 3 | AGENTS.md de ml-die tiene paths rotos (`DAW_bundle/`) | 🔴 P0 | 3 | Documentación |
| 4 | No hay hooks que ejecuten ML antes del build | 🔴 P0 | 1, 2, 3 | ML + Pipeline |
| 5 | Pipeline automático inyecta templates sin traducción de marca | 🔴 P0 | 2, 3 | Pipeline PHP |
| 6 | Skill de 4 fases sin enforcement | 🔴 P0 | 3 | Skill |
| 7 | `divi/heading` → `divi/text` inconsistente entre scripts | 🔴 P1 | 3 | Build + Post-compose |
| 8 | Sólo 1 variante de decoración real de ~7 prometidas | 🔴 P1 | 2, 3 | Pipeline PHP |
| 9 | No hay design-patterns.json en ml-die | 🟠 P1 | 3 | Orquestador |
| 10 | Falta `ml-dataset/requirements.txt` | 🟠 P1 | 1, 2 | DIE |
| 11 | DIE lanza `shell_exec()` sin validación de stderr | 🟠 P1 | 2 | Orquestador |
| 12 | Regex frágil para parsear output del DIE | 🟠 P1 | 2 | Orquestador |
| 13 | Sin asset mapping en post_compose.php | 🟠 P1 | 2 | Post-compose |
| 14 | Contenido duplicado con sufijos -new / -old | 🟠 P1 | 3 | Site data |
| 15 | Global colors no verificados antes de deploy | 🟠 P2 | 2, 3 | Build |
| 16 | `validate_page()` no verifica presets ni tokens | 🟠 P2 | 3 | Build |
| 17 | Typo `worskpace/` en venv path | 🟡 P2 | 2, 3 | Orquestador |
| 18 | Sin rebuild_all_artifacts.py | 🟡 P2 | 2 | DIE |
| 19 | No hay logging del DIE en logs/ del proyecto | 🟡 P2 | 1, 2 | DIE + Logs |
| 20 | Sin preview ni iteración visual | 🟡 P2 | 3 | Pipeline |
| 21 | Sin global layouts (header/footer) | 🟡 P2 | 3 | Build |
| 22 | .gitignore excluye ml-dataset/ | 🟡 P3 | 1 | Git |
| 23 | DIE lento (carga modelos en cada ejecución) | 🟡 P3 | 2, 3 | DIE |
| 24 | Sin integración con WPDS / theme.json | 🟡 P3 | 1 | DIE + WP |
| 25 | Los wrappers (wp.bat) no activan la ruta ML | 🟡 P3 | 1 | Wrappers |
| 26 | No hay entorno virtual Python | 🟡 P3 | 1, 2 | DIE |
| 27 | Los tokens ML no se mezclan con tokens del sitio | 🟡 P3 | 1 | DIE |
| 28 | Los artefactos ML no se regeneran tras cambios | 🔵 P3 | 2 | DIE |
| 29 | La documentación sugiere capacidad ML que no se materializa | 🔵 P3 | 1, 2, 3 | Docs |

---

## 4. El Veredicto en 5 Líneas

1. **No hay un DAW.** Hay **tres DAWs** (skill, pipeline, ML) que operan en paralelo sin integrarse. El resultado no es la suma de sus partes sino el mínimo común denominador.

2. **El pipeline PHP es extraordinario** — `build_page.php` es un motor sólido que resuelve tokens, expande presets, valida estructura y despliega. Es la única parte del sistema que funciona al 100%.

3. **El orquestador automático es el punto más débil** — intenta automatizar el diseño pero no puede. Los templates del catálogo (877) son un recurso valioso como _referencia_, no como _fuente de estructura_. Inyectarlos directamente produce páginas con colores ajenos, imágenes demo, y contenido placeholder.

4. **El ML/DIE es una promesa no cumplida** — los artefactos existen y funcionan, pero el entorno (`env`, junction link, `.agents/skills/`) apunta al bundle _old_. El DIE nunca se ejecuta en el flujo real. Su capacidad de clasificación semántica y búsqueda de templates es real pero está desaprovechada.

5. **El skill de 4 fases es la solución correcta implementada incorrectamente** — la dirección es acertada (artefactos, fases, calidad), pero sin enforcement programático es solo una convención que el agente puede ignorar.

---

## 5. La Causa Raíz Única

> **El DAW fue diseñado como un monolito (un solo bundle) pero evolucionó a un fork (old vs ml-die) sin un plan de integración. La capa ML se añadió como "otra carpeta" sin modificar las interfaces del entorno (`.env`, junction link, wrappers, skills). El resultado es que el ml-die tiene todas las piezas del rompecabezas pero están en cajas separadas.**

El problema no es técnico (el código PHP funciona). El problema es de **arquitectura del sistema**: tres subsistemas que deben cooperar pero operan en paralelo sin conexión.

---

## 6. Plan de Acción Recomendado

### Prioridad 0 — Unificar el Entorno (1 hora)

```
1. Cambiar .env → WORKSPACE_DIR=DAW_bundle_ml-die/workspace
2. Actualizar junction link → apuntar a DAW_bundle_ml-die/divi-agentic-core/
3. Actualizar .agents/skills/daw-skill/SKILL.md → delegar a DAW_bundle_ml-die/
4. Actualizar AGENTS.md raíz → referencias a DAW_bundle_ml-die/
```

Esto solo hace que el sistema apunte al bundle correcto. No arregla el pipeline, pero sin esto nada más funciona.

### Prioridad 1 — Cerrar el Gap entre Skill y Pipeline (2-3 días)

```
1. Añadir validación programática al page-def:
   - lint_page_def.php que verifique las 6 Leyes, presets existentes, sin hex, sin et_pb_*
   - Ejecutar automáticamente antes de build_page.php

2. Eliminar la inyección automática del catálogo en orchestrate_page.php:
   - El orquestador debe generar un page-def ESQUELETO (solo slots vacíos con tipo de sección)
   - No seleccionar templates del catálogo automáticamente
   - El diseño real lo hace la Fase 3 (skill) → page-def a medida

3. El catálogo (877 templates) debe ser solo referencia:
   - search_catalog.py para búsqueda por similitud
   - El agente inspecciona, extrae proporciones, traduce a tokens
   - El agente escribe el page-def manualmente
```

### Prioridad 1.5 — Generación Inteligente de page-defs desde Brief (3-4 días)

**Problema:** Escribir page-defs JSON manualmente es caro en tokens y lento. Pero inyectar templates del catálogo produce páginas con contenido ajeno y colores incorrectos. Se necesita un término medio: **generación programática con inteligencia de diseño real**.

**Solución:** Usar los 4 artefactos ML del DIE (A: patrones de sección, B: índice semántico, C: matriz PMI de afinidad de módulos, D: clasificador de contenido) como fuente de **decisión estructural**, no como fuente de **copia de template**.

```
brief.yml → DIE (análisis) → recomendaciones estructurales → PHP genera page-def → lint → build → deploy
           ───────────────────  ──────────────────────────
           ML intelligence       Programmatic generation
           (artefactos A+B+C+D)  (no templates, no catálogo)
```

#### Estrategia: `generate_page_def.php`

Nuevo script que reemplaza el pipeline viejo (template lookup) y también el manual (escribir JSON):

```
php divi-agentic-core/bin/generate_page_def.php --brief=home.yml
  → Lee brief + DIE artifacts
  → Para cada sección:
      1. Clasifica tipo de contenido (D: content-classifier.pkl)
      2. Recomienda estructura de columnas (A: section-patterns.json)
      3. Recomienda módulos por afinidad (C: module-affinities.json)
      4. Busca template semánticamente similar (B: semantic-index.pkl) solo para PROPORCIONES
      5. Genera page-def con presets correctos + contenido del brief + Leyes aplicadas
  → Escribe site/<DAW_SITE>/page-defs/<slug>.json
```

#### Reglas de generación (garantizan calidad sin catálogo)

| Regla | Implementación |
|-------|----------------|
| **Usar presets siempre** | `section:hero-dark`, `text:display-xl`, `module:feature-card` — nunca hex ni valores sueltos |
| **Alternancia de fondos** | Si section 0 usa `hero-dark`, section 1 usa `light`, section 2 usa `white`, etc. Ciclo automático |
| **Titular display-xl en hero** | Primera sección siempre H1 con `text:display-xl` o `text:hero-title` |
| **Padding mínimo 96px** | Sections siempre con `{{design:space:2xl}}` o 96px |
| **Hover en elementos clickeables** | Botones con `transform:hover-lift`, cards con `transform:hover-scale` |
| **Sin hex hardcodeados** | Generador solo produce `{{design:color:*}}` y `{{design:font:*}}` |
| **breakpoints responsivos** | Desktop/tablet/phone con reducción 35-40% (Ley 6) |

#### Arquitectura de generación por sección

Para cada sección, el generador consulta:

```
brief.sections[i]:
  section_type: hero
  slots:
    title: "Bibliotheca San Pablo"
    text: "Descubre el conocimiento..."
    btn_text: "Explorar"

→ DIE (content-classifier.pkl): "hero tipográfico institucional"
→ DIE (section-patterns.json): column_structures más comunes → ["4_4" (72%), "1_2,1_2" (16%)]
→ DIE (module-affinities.json): módulos con mayor PMI → [heading(2.34), button(1.89), text(1.45)]
→ DIE (semantic-index.pkl): búsqueda por similitud → solo PROPORCIONES, no contenido

→ OUTPUT:
{
  "presets": ["section:hero-dark"],
  "rows": [{
    "column_structure": "4_4",
    "modules": [
      {"type": "divi/heading", "presets": ["text:eyebrow-dark"], "content": "{{slot:eyebrow}}"},
      {"type": "divi/heading", "presets": ["text:hero-title"], "content": "<h1>{{slot:title}}</h1>"},
      {"type": "divi/text", "presets": ["text:lead"], "content": "<p>{{slot:text}}</p>"},
      {"type": "divi/button", "presets": ["module:btn-primary", "transform:hover-lift"], "button_text": "{{slot:btn_text}}"}
    ]
  }]
}
```

#### Lo que NO hace (anti-patrones)

1. **No copia templates del catálogo** — solo extrae proporciones y patrones
2. **No usa imágenes demo** — el generador no tiene URL de imágenes
3. **No usa colores ajenos** — solo `{{design:color:*}}` tokens
4. **No usa `et_pb_*`** — solo namespace `divi/*`
5. **No genera contenido placeholder** — todo el texto viene del brief o es string vacío
6. **No repite la misma sección** — variación automática en column_structure y decoration

#### Migración desde el orquestador actual

El `orchestrate_page.php` debe delegar a `generate_page_def.php` en vez de hacer template lookup:

```
antes:  brief → lookup template (catalog/local) → compose → build
ahora:  brief → generate_page_def.php (DIE-guided) → lint → build
```

Esto elimina la necesidad de:
- `compose_page.php` (ya no hay templates que llenar)
- `_skeleton.section.json` (generador produce page-defs completas)
- Catálogo como fuente de estructura (solo como referencia de proporciones)

#### Dependencias

1. Los 4 artefactos DIE deben existir (ya existen: `.pkl` y `.json`)
2. El DIE orquestador (`design_intelligence.py`) debe exponer interfaz limpia: `--brief-file` → JSON con recomendaciones por sección
3. `generate_page_def.php` (nuevo, PHP) que consume el output del DIE y genera page-defs

---

### Prioridad 2 — Integrar el DIE como Asistente, No como Generador (2-3 días)

```
1. design_intelligence.py debe producir RECOMENDACIONES, no TEMPLATES:
   - "para esta sección hero, las column structures más comunes son 4_4 (72%) y 1_2,1_2 (16%)"
   - "los módulos con mayor afinidad son heading+button (PMI 2.34)"
   - El page-def lo escribe el agente basado en estas recomendaciones

2. Añadir logging del DIE:
   - Guardar die_input.json + die_output.json en site/<DAW_SITE>/compositions/
   - Capturar stderr en logs/die.log

3. Script rebuild_all_artifacts.py que regenera A+B+C+D en cascada
```

### Prioridad 3 — Quality Gates Automáticos (1 día)

```
1. Pre-deploy: validar gcids sincronizados
2. Pre-deploy: validar que no hay {{design:*}} sin resolver (--no-resolve off)
3. Pre-deploy: validar que no hay button_text:"" ni src:"" ni content vacío
4. Post-deploy: verify_page.php mejorado que captura screenshot
```

---

## 7. Conclusión Final

**El DAW no está roto. Está incompleto.**

`build_page.php` es un motor de producción sólido. Los artefactos ML del DIE son reales y funcionales. El skill de 4 fases tiene la dirección correcta. El catálogo de 877 templates es un recurso valioso.

Lo que falta es la **capa de integración** que conecte estos sistemas. Hoy operan como islas. Cuando se conecten, el DAW generará páginas con calidad consistente: variedad estructural del ML, dirección visual del skill, y ejecución robusta del pipeline PHP.

**Sin integración, el DAW siempre producirá resultados pobres — no por falta de capacidades, sino por falta de conexión entre ellas.**
