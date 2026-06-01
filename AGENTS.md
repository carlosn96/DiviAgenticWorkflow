# DAW — Divi Agentic Workflow

Este documento es la fuente de verdad para todo el flujo de diseño y despliegue de páginas Divi 5. Es autocontenido: un agente que solo vea esta carpeta puede operar sin depender de la raíz del proyecto.

Todos los paths son relativos a `DAW_bundle/` a menos que se indique lo contrario. Los comandos se ejecutan desde la raíz del proyecto (`divitheme/`).

---

## 1. Mapa del DAW

```
DAW_bundle/
├── AGENTS.md                      <- Este archivo (punto de entrada al DAW)
├── README.md                      <- Documentación rápida
├── .env.example                   <- Template de configuración
├── .gitignore                     <- Reglas git del framework
├── wp.bat, php.bat, mysql.bat     <- Wrappers genéricos (delegan a raíz del proyecto)
├── site/                          <- ⭐ DATOS DE PROYECTO (separados del framework)
│   ├── aletheia/                  <-    Marca activa: Aletheia Institute
│   │   ├── brand/                 <-       _design_vars.json + _design_presets.json
│   │   ├── page-defs/             <-       ⭐ ENTRADA: JSON semántico del diseñador (tokens {{design:*}}, presets)
│   │   ├── pages/                 <-       SALIDA OPCIONAL: schema resuelto por build_page.php (--out, solo debug)
│   │   ├── plans/                 <-       plan.json generado por DIE (entrada de build_page.php)
│   │   ├── design-system/         <-       divitheme.json generado (64 presets + color derivación + contraste validado)
│   │   ├── briefs/                <-       Briefs de diseño
│   │   ├── content_state/         <-       Estado entre fases (local/ + remote/)
│   │   └── compositions/          <-       Composición intermedia (legacy)
│   └── example/                   <-    Template para nuevas marcas (brand/, plans/, page-defs/, etc.)
├── _archive/                      <- Archivos legacy deprecados (b_semantic_index, compile_catalog, etc.)
├── ui-ux-pro-max/                 <- Skill de diseño UI/UX (opcional)
├── daw-skill/SKILL.md             <- FLUJO PRINCIPAL: orquestación de 4 fases
├── workspace/                     <- Scripts principales y datos
│   ├── daw_build.py               <- ⭐ ORQUESTADOR UNIFICADO: brand → design → brief → VIE/DIE → deploy
│   ├── brand_generator.py         <- Generador automático de _design_vars.json + _design_presets.json
│   ├── build_design_system.py     <- VISUAL INTELLIGENCE ENGINE v4.0: CIELCH, glass/glow/aura, 54 presets
│   ├── automation/                <- generate_brief.py, etc.
│   ├── data/modules/              <- Schemas de módulos generados por PHP (103 módulos)
│   └── sections/                  <- ⭐ Templates de sección con variantes
│       └── catalog/               <-    877 templates compilados como .section.json
├── ml-dataset/                    <- ⭐ ML Artifacts: Design Intelligence Engine
│   ├── dataset.jsonl              <-    877 registros limpios con contenido real
│   ├── PLAN.md, TASKS.md          <-    Arquitectura y tracking
│   └── artifacts/                 <-    Scripts + modelos del DIE
│       ├── visual_impact_engine.py<-       ⭐ VIE: generador determinístico (glass/glow/aura contextual)
│       ├── design_intelligence.py <-       Orquestador DIE (ML pipeline)
│       ├── design_director.py     <-       Stacking ensemble: clasificación + template + decoración
│       ├── e_page_mapper.py       <-       Mapea planes → page-def (section/rows/columns/modules)
│       ├── a_section_patterns.py  <-       Artefacto A: patrones de sección
│       ├── b_slot_assigner.py     <-       Artefacto B2: Hungarian slot assigner
│       ├── c_module_affinities.py <-       Artefacto C: afinidades PMI
│       ├── d_content_classifier.py<-       Artefacto D: clasificador de contenido
│       ├── e_decorator.py         <-       Artefacto E: K-means decoration clusters
│       ├── ux_pro_bridge.py       <-       Puente a ui-ux-pro-max (clasificador de estilo)
│       ├── section-patterns.json  <-       Output A (18 tipos)
│       ├── slot-catalog.pkl       <-       Output B2
│       ├── module-affinities.json <-       Output C
│       └── content-classifier.pkl <-       Output D
└── divi-agentic-core/
    ├── Plugin WordPress (Layout Engine, CLI, metadata)
    └── bin/
        ├── env_loader.php         <- ⭐ Carga .env automáticamente (DAW_SITE, API keys, etc.)
        ├── build_page.php         <- ⭐ Resuelve tokens → expande presets → deploy
        └── verify_page.php        <- Verificación post-deploy
```

---

## ⚡ Primeros Pasos (Quickstart)

> **Python**: Usar el intérprete Python global del sistema (`python --version`). No usar entornos virtuales.
> **Pipeline unificado (orquestador)**: `daw_build.py --site <nombre> --name "Marca" --accent "#hex" --full --vie --prompt "..."`

```powershell
# 0. ⚡ Elegir marca activa (OBLIGATORIO)
#    Editar .env en raíz del proyecto y definir:
#      DAW_SITE=nombre-de-tu-marca
#    Sin esta variable, el pipeline se detiene con error.

# 1. Sincronizar plugin WP como junction link (una vez)
Remove-Item -Recurse -Force "app/public/wp-content/plugins/divi-agentic-core"
New-Item -ItemType Junction -Path "app/public/wp-content/plugins/divi-agentic-core" -Target (Resolve-Path "DAW_bundle\divi-agentic-core").Path

# 2. (una vez) Generar schemas de módulos + instalar deps Python
.\php.bat DAW_bundle/divi-agentic-core/bin/generate-module-schema.php --all
python -m pip install -r DAW_bundle/ml-dataset/requirements.txt

# 3. (una vez por marca) Generar design system + sincronizar colores
python DAW_bundle/workspace/build_design_system.py
.\wp.bat agentic global_colors sync --design-system="DAW_bundle/site/<DAW_SITE>/design-system/divitheme.json"

# 4. Pipeline de página (orquestador unificado — recomendado):
python DAW_bundle/workspace/daw_build.py --site $env:DAW_SITE --full --vie --prompt "descripción breve"

# Alternativa: pipeline manual paso a paso
python DAW_bundle/workspace/automation/generate_brief.py --prompt "descripción breve" --tone editorial --out <slug>
python DAW_bundle/ml-dataset/artifacts/design_intelligence.py --brief-file=DAW_bundle/site/<DAW_SITE>/briefs/<slug>.json --output=DAW_bundle/site/<DAW_SITE>/plans/<slug>.json
.\php.bat DAW_bundle/divi-agentic-core/bin/build_page.php --def=DAW_bundle/site/<DAW_SITE>/plans/<slug>.json --deploy
```

---

## 2. Pipeline: diseño → deploy (PHP unificado)

```
Capa 0 — Module Schemas (PHP, fuente única de estructura)
  php divi-agentic-core/bin/generate-module-schema.php --all
  → Lee _all_modules_metadata.php (metadata real de Divi 5)
  → workspace/data/modules/<slug>.json (103 módulos, estructura autoritativa)
  ⚠️ build_page.php NO define atributos de módulo — los carga de estos JSONs.

Capa 1 — Design System (build_design_system.py v4.0)
  site/<DAW_SITE>/brand/_design_vars.json + site/<DAW_SITE>/brand/_design_presets.json
  → build_design_system.py (Visual Intelligence Engine: CIELCH, glass/glow/aura)
  → site/<DAW_SITE>/design-system/divitheme.json
    (54 presets enriquecidos: section/text/module/divider/animation/scroll/transform)

Capa 2a — DIE → plan.json (RECOMENDADO)
  python ml-dataset/artifacts/design_intelligence.py --brief-file=site/<DAW_SITE>/briefs/<slug>.json --output=site/<DAW_SITE>/plans/<slug>.json

  design_intelligence.py (DIE v3.0) hace TODO en un solo proceso:
    • Carga A+B+C+D+E como módulos Python (sin archivos intermedios)
    • Lee brief JSON con tone, product_type, sections[]
    • Clasifica cada sección con D (content classifier)
    • Asigna templates globalmente con B2 (Hungarian + IDF + slot coverage F1)
    • B2 parsea dataset.jsonl (slots_offered por extract.py con 9 slot types),
      mapea slots_needed del brief via get_slots_needed_from_brief_section():
      titles, paragraphs, buttons, images + listas discriminadas: features, testimonials, stats, logos, items
      • Tie-breaker: +0.02 F1 si el template tiene el mismo nº de columnas que el esperado
        (items → N columnas, hero/content split → 2 cols, resto → 1 col)
      • Categorías desde embeddings.pkl + fallback keyword para 100% compatibilidad
    • Fallback: B (semantic index legacy) si B2 no encuentra match
    • Determina estructura de columnas con A (section patterns)
    • Recomienda módulos complementarios con C (module affinities)
    • Genera decoration blocks con E (decoration engine):
      - Gradients, shadows, animations, hover/scroll effects
      - Shape dividers, border-radius, masks
      - Todo con tokens {{design:color:*}}, nunca hex
    • Ensambla plan.json completo listo para build_page.php
    • Output: plan.json sin PHP intermedio, listo para consumir

Capa 2b — Page Schema + Deploy (build_page.php — ÚNICO SCRIPT)
  php divi-agentic-core/bin/build_page.php --def=plans/mipagina.json --deploy

  build_page.php hace TODO:
    • Lee plans/<slug>.json desde site/<DAW_SITE>/plans/ (output del DIE)
    • Carga estructura de módulo desde schema PHP (workspace/data/modules/)
    • Carga design system desde site/<DAW_SITE>/design-system/divitheme.json
    • Resuelve {{design:color:name}} → var(--gcid-*)
    • Resuelve {{design:font|radius|space:name}} → literales
    • Expande presets inline via deep_merge()
    • Normaliza gradient stops
    • Valida estructura (sections → rows → columns → modules)
    • Escribe site/<DAW_SITE>/pages/<slug>.json (schema completo)
    • [--deploy] Ejecuta wp agentic deploy_page
      → Layout Engine convierte var(--gcid-*) → $variable() en post_content
      → Visual Builder reconoce colores globales

  ⚠️ Sin Python en el pipeline de página. Sin archivos intermedios.
     Un solo lenguaje (PHP), un solo comando.
     El DIE es una etapa previa ML opcional que genera el plan; el build consume ese plan sin Python.

### plans/ vs pages/ (duda frecuente)

| Carpeta | Rol | Quién escribe | Git |
|---------|-----|---------------|-----|
| `plans/` | **Entrada** — plan.json generado por el DIE con decoration blocks + estructura + tokens `{{design:*}}`. El pipeline lee de aquí. | DIE (`design_intelligence.py`) | Trackeado |
| `pages/` | **Salida opcional** — Schema completo con tokens resueltos, presets expandidos inline. `build_page.php` genera esto solo si se pasa `--out`. NO es necesario para el deploy (`--deploy` trabaja en memoria). | `build_page.php` | Ignorado |

> El flujo normal es `brief.json → DIE → plans/<slug>.json → build_page.php --deploy`. `pages/` existe únicamente para debug.
```

---

## 3. Decoration blocks (Artifact E)

La decoración ya no se maneja con variantes de sección en archivos JSON separados. El Decoration Engine (Artifact E) genera decoration blocks completos en el plan.json, usando:

- **Gradients**: lineales/radiales con múltiples stops, mapeados por tone y product_type
- **Shadows**: múltiples capas (box-shadow, text-shadow) con opacidad y blur
- **Animaciones**: keyframes + easing + delays, con tokens {{design:*}}
- **Hover/scroll effects**: parallax-up, fade, stagger, reveal
- **Shape dividers**: 6 estilos (rounded, angle, arrow, wave, curve, custom)
- **Border-radius**: radios por esquina, responsive
- **Masks**: clip-path CSS con formas geométricas
- **Presets**: section, text, module, divider, animation, scroll, hover

Todo usa tokens `{{design:color:*}}`, nunca hex. El DIE combina tone + product_type + brand_vars para seleccionar decoration personas desde 7 clusters K-means entrenados en 877 templates reales.

> No se necesitan archivos `.variant.json`. El DIE + brand presets son la única fuente de decoration.

---

## 3b. Design Inspiration Skills (ui-ux-pro-max + frontend-design)

Ambos skills externos se integran como **inspiración de diseño**, no como
fuente de datos. Ningún valor raw (hex, font names, CSS) entra al pipeline.
Solo influyen decisiones Divi-nativas a través de clasificación de estilo.

### ui-ux-pro-max → clasificador de estilo

`UXProBridge.classify(tone, product_type)` retorna solo clasificaciones:

- `style_name`: "Liquid Glass", "Vibrant & Block-based", etc.
- `variant_hint`: variante Divi preferida (`liquid-glass`, `minimal-card`, ...)
- `atmosphere_hint`: atmósfera preferida (`clean`, `vibrant`, `gold-accent`)
- `animation_profile`: `{duration, delay_step_ms, stagger}`
- `contrast_level`: `"high"`, `"medium"` o `"low"`
- `effects_tags`: `["morphing", "fluid", "animated", ...]`

Estas clasificaciones se mapean a opciones Divi-nativas:

| Clasificación | Decisión Divi |
|---------------|---------------|
| `style_name: "Liquid Glass"` | Variante `liquid-glass.variant` en hero |
| `effects_tags: ["morphing", "fluid"]` | Animación heavy: 800ms, stagger |
| `contrast_level: "high"` | Pares surface-deep + text-on-dark |
| `atmosphere_hint: "vibrant"` | Overlay gradient violeta |

### frontend-design → principios de diseño

`_FRONTEND_PRINCIPLES` en `DesignDirector` adapta las reglas del skill:
- **Typography**: penaliza fonts genéricos (Inter, Arial, Roboto) en scoring
- **Motion**: delays progresivos de 150ms en animaciones
- **Spacing**: padding mínimo de 80px (generous whitespace)
- **Color**: prefiere alto contraste sobre paletas planas
- **Aesthetic**: variantes más distintivas, no rotación genérica

### Flujo

```
brief.json → design_intelligence.py
  → director._classify_page_style(tone, product_type)
      → UXProBridge.classify() → {variant_hint, atmosphere_hint, ...}
  → director.compose_page(brief, sections)
      → usa variant_hint → variante preferida en variant_map
      → usa atmosphere_hint → atmósfera en decoration
  → director.generate_section_plan()
      → decide_decoration()
          → recommend_typography() penaliza fonts genéricos
          → _apply_design_inspiration() usa animation_profile,
              contrast_level, effects_tags como hints internos
          → NO inyecta hex, font names ni CSS al output
```

### Regla fundamental

> **Skills = decisión, no datos.** El plan.json solo contiene tokens
> `{{design:color:*}}`, presets Divi y estructuras nativas. La influencia
> externa se resuelve en parámetros internos, nunca en valores literales.

### Archivos

| Archivo | Rol |
|---------|-----|
| `ml-dataset/artifacts/ux_pro_bridge.py` | Clasificador: `UXProBridge.classify()` retorna solo clasificaciones Divi-nativas |
| `ml-dataset/artifacts/design_director.py` | `_classify_page_style()`, `_apply_design_inspiration()`, `_FRONTEND_PRINCIPLES` |
| `~/.agents/skills/ui-ux-pro-max/scripts/` | Fuente: DesignSystemGenerator (BM25 sobre 5 dominios CSV) |
| `~/.agents/skills/frontend-design/SKILL.md` | Principios de diseño (leídos como inspiración, no como código) |

---

## 4. Pipeline de Páginas (Activo)

### Flujo Determinístico VIE v3.0 — Pipeline Oficial

```
UX-Pro Brief Generator  →  Brief JSON  →  VIE v3.0  →  build_page.php --deploy
```

| Paso | Script / Comando | Input | Output |
|------|------------------|-------|--------|
| 0. Brand + Design System* | `workspace/brand_generator.py` → `workspace/build_design_system.py` | Color, nombre, tone | `site/<DAW_SITE>/brand/` + `design-system/divitheme.json` |
| 1. Brief | `workspace/automation/ux_pro_brief_generator.py --query "..."` | Query semántico | `site/<DAW_SITE>/briefs/<slug>.json` |
| 2. Plan | `ml-dataset/artifacts/visual_impact_engine.py --brief-file ... --design-system ...` | Brief JSON + Design System | `site/<DAW_SITE>/plans/<slug>.json` RICO |
| 3. Deploy | `divi-agentic-core/bin/build_page.php --def=... --deploy` | Plan JSON | Página WP viva |

**VIE v3.0 — Arquitectura de 3 capas (determinística, sin LLMs):**

```
brief.json ──► Style Director ──► design_spec.json
                    │
    ┌───────────────┼───────────────┐
    ▼               ▼               ▼
Catálogo Divi   Dataset diviplus   Brand vars
(127 props)     (12 blocks)        (colores/fonts)
    │               │               │
    └───────────────┴───────────────┘
                    ▼
         Visual Impact Engine v3.0
         (reglas determinísticas)
                    ▼
            page-def.json RICO
    (glass, glow, blur, gradient overlays,
     hover effects, shape dividers)
                    ▼
           build_page.php ──► WP
```

| Capa | Archivo | Propósito |
|------|---------|-----------|
| Catálogo Divi | `workspace/data/divi_catalog.json` | 127 props nativas de alto impacto con paths, tipos, valores válidos y reglas de impacto |
| Dataset diviplus | `workspace/data/diviplus_dataset.json` | 12 block patterns (hero_glass, features_glass_grid, cta_epic...) con combinaciones ganadoras + reglas de combinación + adaptación por estrategia |
| Brand Resolver | inline en VIE | Resuelve `{{design:color:*}}` → hex vía design-system/divitheme.json |
| Impact Director | inline en VIE | Aplica reglas frontend-design (tipografía fluida, motion premium, spacing generoso) en decisiones Divi-nativas |

\* Brand se genera **una sola vez por marca** (ve §Cómo crear una nueva marca).

### Pipeline Completo Manual (paso a paso)

```powershell
# 0. (una vez por marca) Brand + Design System
python DAW_bundle/workspace/brand_generator.py `
  --site aletheia `
  --name "Aletheia Institute" `
  --accent "#CA8A04" `
  --tone luxury

python DAW_bundle/workspace/build_design_system.py

# Sincronizar colores globales
.\wp.bat agentic global_colors sync `
  --design-system="DAW_bundle/site/aletheia/design-system/divitheme.json"

# 1. Generar brief rico desde UX-Pro
python DAW_bundle/workspace/automation/ux_pro_brief_generator.py `
  --query "about us" `
  --out DAW_bundle/site/aletheia/briefs/about-us.json

# 2. Brief → Plan (VIE v3.0 — determinístico, catálogo + dataset)
python DAW_bundle/ml-dataset/artifacts/visual_impact_engine.py `
  --brief-file="DAW_bundle/site/aletheia/briefs/about-us.json" `
  --design-system="DAW_bundle/site/aletheia/design-system/divitheme.json" `
  --output="DAW_bundle/site/aletheia/plans/about-us.json" `
  --evaluate  # opcional: muestra impact score

# 3. Plan → WordPress
.\php.bat DAW_bundle/divi-agentic-core/bin/build_page.php `
  --def=DAW_bundle/site/aletheia/plans/about-us.json `
  --deploy
```

### Pipeline con Orquestador (daw_build.py)

```powershell
# Un solo comando para todo (brand + design system + brief + deploy)
python DAW_bundle/workspace/daw_build.py `
  --site <DAW_SITE> `
  --name "Mi Marca" `
  --accent "#CA8A04" `
  --tone luxury `
  --full --vie `
  --prompt "home page description"
```

### Pipeline Activo: VIE (Determinístico) — Recomendado

```
Site/UX-Pro BM25  →  Brief JSON (riche)  →  VIE v2.0  →  build_page.php --deploy
```

| Paso | Script | Output |
|------|--------|--------|
| 1. Brand + Design System | `workspace/brand_generator.py` + `workspace/build_design_system.py` | `site/<DAW_SITE>/brand/` + `design-system/divitheme.json` |
| 2. Brief | `workspace/automation/ux_pro_brief_generator.py --query "..."` | `site/<DAW_SITE>/briefs/<slug>.json` |
| 3. Plan | `ml-dataset/artifacts/visual_impact_engine.py --brief-file ...` | `site/<DAW_SITE>/plans/<slug>.json` |
| 4. Deploy | `divi-agentic-core/bin/build_page.php --def=... --deploy` | Página WP viva |

### Pipeline Legacy: DIE (ML) — Archivado

El pipeline ML (`design_intelligence.py` + artefactos A/B/C/D/E) fue archivado en `_archive/die_pipeline/`.

> No usar. El dataset de 877 templates y los artefactos de ML aún existen como referencia, pero el pipeline activo es el determinístico.

0. (Una vez por proyecto o tras actualizar Divi) Regenerar schemas de módulos:
   ```
   .\php.bat DAW_bundle/divi-agentic-core/bin/generate-module-schema.php --all
   ```

1. Crear definición de página en `site/<DAW_SITE>/page-defs/<slug>.json`:

   > `DAW_SITE` debe estar definido en `.env` o como variable de entorno.

```json
{
  "title": "Título de la Página",
  "slug": "mi-pagina",
  "description": "Opcional",
  "sections": [
    {
      "presets": ["section:hero-dark"],
      "parallax": "on",
      "bg_gradient": {
        "type": "linear", "direction": "135deg",
        "overlaysImage": "on",
        "stops": [
          {"color": "rgba(15,23,42,0.92)", "position": "0"},
          {"color": "rgba(15,23,42,0.35)", "position": "100"}
        ]
      },
      "rows": [
        {
          "column_structure": "4_4",
          "modules": [
            {"type": "divi/text", "presets": ["text:eyebrow"],
             "content": "<p>Subt&iacute;tulo</p>"},
            {"type": "divi/text", "presets": ["text:display-xl"],
             "content": "<h1>T&iacute;tulo Principal</h1>"}
          ]
        },
        {
          "column_structure": "1_2,1_2",
          "columns": [
            {"type": "1_2", "modules": [
              {"type": "divi/button", "presets": ["module:btn-primary"],
               "button_text": "Acci&oacute;n", "button_url": "/ruta"}
            ]},
            {"type": "1_2", "modules": [
              {"type": "divi/blurb", "presets": ["module:feature-card"],
               "title": "Feature", "icon": "&#xe03a;"}
            ]}
          ]
        }
      ]
    }
  ]
}
```

**Formato de definición:**
- `sections[]` — arreglo de secciones
  - `presets[]` — refs a presets del design system (`section:*`, `text:*`, `module:*`)
  - `rows[]` — arreglo de filas
    - `column_structure` — string como `"4_4"`, `"1_2,1_2"`, `"1_3,1_3,1_3"`
    - `modules[]` — (modo simple) módulos en columna única (4_4 implícito)
    - `columns[]` — (modo explícito) arreglo de columnas, cada una con `type` y `modules[]`
    - `module.type` — nombre del módulo Divi 5: `divi/text`, `divi/blurb`, etc.
    - `module.presets[]` — presets a aplicar (se expanden inline)
    - `module.decoration` — decoration object (spacing, border, boxShadow, animation, etc.)
    - `animation`, `scroll`, `transform` — motion presets como string (ej: `"fade-in"`)

2. Build + Deploy (un solo paso):
   ```
   .\php.bat DAW_bundle/divi-agentic-core/bin/build_page.php --def=site/<DAW_SITE>/page-defs/mi-pagina.json --deploy
   ```

   Opciones adicionales:
   - `--out=path.json` — escribir schema sin desplegar
   - `--no-resolve` — schema raw sin expandir presets/tokens (debug)
   - `--deploy --front` — desplegar y establecer como portada
   - `--deploy --verify` — ejecutar verificación post-deploy (comprueba gcids, bloques, estructura)
   - `--deploy --verify --url="https://..."` — verificación + acceso HTTP público
   - `DAW_SITE` env var — cambiar proyecto activo (`$env:DAW_SITE="otromarca"`)

   La verificación post-deploy ejecuta `verify_page.php` que comprueba:
   - La página existe en WordPress
   - El contenido contiene bloques Divi 5
   - Las variables `var(--gcid-*)` están presentes
   - No quedan tokens `{{design:*}}` sin resolver
   - Coincidencia estructural vs schema (opcional con `--schema`)
   - Accesibilidad HTTP pública (opcional con `--url`)

   > Para verificación visual (screenshot), integrar con Playwright:
   > `npx playwright wk http://localhost/mi-pagina --screenshot`

---

## 4. Sistema de Diseño

No editar `divitheme.json` a mano. Usar `build_design_system.py` (v4.0, Visual Intelligence Engine):

```powershell
# La herramienta ahora tiene inteligencia de diseño:
#   - Deriva automáticamente 26 colores desde un solo color_accent
#   - Valida contraste WCAG AA/AAA
#   - Añade hover states a módulos interactivos
#   - Convierte tipografía fija a fluida con clamp()
#   - Añade presets faltantes (glass-card, divisores SVG, motion)
python DAW_bundle/workspace/build_design_system.py `
  --vars DAW_bundle/site/<DAW_SITE>/brand/_design_vars.json `
  --presets DAW_bundle/site/<DAW_SITE>/brand/_design_presets.json `
  --out DAW_bundle/site/<DAW_SITE>/design-system/divitheme.json
```

Para otra marca: `$env:DAW_SITE="otramarca"` antes de ejecutar, o pasar rutas explicitas con `--vars`/`--presets`/`--out`.

Sincronizar colores globales en Divi 5:
```
.\wp.bat agentic global_colors sync `
  --design-system="DAW_bundle/site/<DAW_SITE>/design-system/divitheme.json"
```

El generador auto-descubre tokens por prefijo (`color_`, `font_`, `radius_`, `space_`) de cualquier archivo de variables. No hay nombres hardcodeados en Python — funciona con cualquier marca.

**Colores**: se referencian como `{{design:color:name}}` y el resolver los convierte a `var(--gcid-name)` (dinámico). Los tokens en `divitheme.json` mantienen valores hex para el sync de gcids.

**Fonts, radii, spacing**: se referencian como `{{design:font:name}}`, `{{design:radius:name}}`, `{{space_name}}` y se resuelven a literales (horneados en build).

---

## 5. Prerrequisito: Global Colors (gcid)

Antes del primer deploy, sincronizar colores. El verificador de hash está en `_dac_gcid_hash`:

| Acción | Comando |
|--------|---------|
| Sincronizar | `.\wp.bat agentic global_colors sync --design-system="DAW_bundle/site/<DAW_SITE>/design-system/divitheme.json"` |
| Verificar estado | `.\wp.bat agentic global_colors status --design-system="..."` |
| Listar activos | `.\wp.bat agentic global_colors list` |

Si no hay gcids sincronizados, `deploy_page` emite warning y resuelve a hex.

---

## 6. Referencias

| Recurso | Path (desde DAW_bundle/) | Propósito |
|---------|--------------------------|-----------|
| SKILL.md (4 fases) | `daw-skill/SKILL.md` | Orquestación completa análisis → diseño → mapeo → CLI |
| Diccionario de bloques | `daw-skill/references/blocks-dictionary.md` | Guía de 102 módulos Divi 5 |
| Lógica del Diseñador | `daw-skill/references/designer.md` | Mapeo semántico → bloques, tokens, decoration |
| Lógica del Ingeniero | `daw-skill/references/engineer.md` | Comandos CLI, deploy, verificación |
| DIE (Design Intelligence Engine) | `ml-dataset/artifacts/design_intelligence.py` | ⭐ A+B+C+D+E: brief → plan.json con decoration blocks |
| Build page | `divi-agentic-core/bin/build_page.php` | Único script PHP: lee plan → resuelve tokens → deploy (usa `DAW_SITE` env) |
| Decoration Engine | `ml-dataset/artifacts/e_decorator.py` | ⭐ K-means sobre 877 templates + 4 CSVs → decoration blocks |
| Design system (generado) | `site/<DAW_SITE>/design-system/divitheme.json` | 64 presets, fuente de verdad de tokens |
| Variables de entrada | `site/<DAW_SITE>/brand/_design_vars.json` | Colores, fonts, radios, espacio |
| Presets de diseño | `site/<DAW_SITE>/brand/_design_presets.json` | 64 presets (section/text/module/divider/animation/scroll/hover) |
| Definiciones de página | `site/<DAW_SITE>/page-defs/` | JSON de entrada (home.json, about.json...) |
| Briefs de diseño | `site/<DAW_SITE>/briefs/` | YAML de entrada para el orquestador |
| Templates de sección | `workspace/sections/` | _base.section.json + *.variant.json + catalog/*.section.json |
| Catálogo de templates | `workspace/sections/catalog/` | 877 templates compilados como .section.json (usados por DIE) |
| Patrones de diseño | `ml-dataset/artifacts/section-patterns.json` | 18 tipos de sección, composición + module affinity |
| DIE — Design Intelligence Engine | `ml-dataset/artifacts/design_intelligence.py` | ⭐ Orquestador ML: clasifica + busca + recomienda + decora (A+B+C+D+E) |
| DIE — Artefacto A | `ml-dataset/artifacts/a_section_patterns.py` | Patrones estructurales de 877 templates |
| DIE — Artefacto B2 | `ml-dataset/artifacts/b_slot_assigner.py` | Hungarian + IDF + col tie-breaker: 9 slot types, 877 templates, 18 categorías |
| DIE — Artefacto C | `ml-dataset/artifacts/c_module_affinities.py` | Matriz PMI de co-ocurrencia de módulos |
| DIE — Artefacto D | `ml-dataset/artifacts/d_content_classifier.py` | Clasificador TF-IDF + Naive Bayes (98.2% acc) |
| DIE — Artefacto E | `ml-dataset/artifacts/e_decorator.py` | Decoration Engine: K-means clusters + 4 CSVs → decoration blocks |
| VIE (Visual Impact Engine) | `ml-dataset/artifacts/visual_impact_engine.py` | ⭐ Generador determinístico contextual: glass/glow/aura por tipo de sección |
| Brand Generator | `workspace/brand_generator.py` | Genera _design_vars.json + _design_presets.json desde CLI |
| Orquestador | `workspace/daw_build.py` | ⭐ Un comando: brand → design → brief → VIE/DIE → deploy |
| UXProBridge | `ml-dataset/artifacts/ux_pro_bridge.py` | Puente a ui-ux-pro-max: color, tipografía, patrones, efectos |
| Dataset DIE | `ml-dataset/dataset.jsonl` | 877 registros limpios con contenido real |
| Plugin WordPress | `divi-agentic-core/` | Layout Engine, CLI, metadata |

---

## 7. Estructura de Carpetas

Cada tipo de archivo tiene su carpeta asignada. No crear archivos fuera de su ubicación:

| Carpeta | Contenido |
|---------|-----------|
| `site/<DAW_SITE>/brand/` | ⭐ Datos de marca: `_design_vars.json` + `_design_presets.json` |
| `site/<DAW_SITE>/plans/` | ⭐ plan.json generado por DIE (entrada de build_page.php) |
| `site/<DAW_SITE>/pages/` | Schemas resueltos (output opcional de `build_page.php --out`, solo para debug/inspección) |
| `site/<DAW_SITE>/design-system/` | `divitheme.json` generado (output, gitignored) |
| `site/<DAW_SITE>/briefs/` | ⭐ Briefs YAML de diseño (entrada del orquestador) |
| `site/<DAW_SITE>/compositions/` | (legacy — eliminado, usar plans/) |
| `site/<DAW_SITE>/content_state/` | Estado de contenido entre fases (local/ + remote/) |
| `site/example/` | Template de estructura para nuevas marcas |
| `workspace/sections/` | ⭐ Templates de sección con variantes de decoración |
| `workspace/sections/catalog/` | 877 templates del catálogo compilados como .section.json (usados por DIE) |
| `ml-dataset/artifacts/section-patterns.json` | ⭐ Output A: 18 tipos de sección |
| `workspace/data/modules/` | Schemas de módulos Divi 5 (103, generados por PHP) |
| `workspace/automation/` | Scripts de automatización |
| `workspace/daw_build.py` | ⭐ Orquestador unificado: brand → design → brief → VIE/DIE → deploy |
| `workspace/brand_generator.py` | Generador automático de brand files desde CLI |
| `workspace/build_design_system.py` | Visual Intelligence Engine v4.0 (CIELCH, glass/glow/aura) |
| `ml-dataset/` | ⭐ Dataset + artefactos ML del DIE |
| `ml-dataset/artifacts/` | Scripts + modelos del DIE (A, B, C, D + orquestador) |
| `divi-agentic-core/bin/` | ⭐ build_page.php + verify_page.php + generate-module-schema (orquestador eliminado) |
| `daw-skill/` | Skill de orquestación y sus referencias |
| `divi-agentic-core/` | Plugin WordPress |
| `ui-ux-pro-max/` | Skill auxiliar de diseño UI/UX (opcional) |

### Cómo crear una nueva marca

> ⚠️ **Antes de empezar**: editar `.env` en la raíz del proyecto y definir `DAW_SITE=nombre-de-tu-marca`.
> Todos los scripts PHP leen `.env` automáticamente vía `env_loader.php`. No necesitas `$env:DAW_SITE`.

#### Método A: Generación automática (recomendado)

```powershell
# 1. Generar brand files automáticamente desde CLI
#    El motor detecta estrategia visual desde color_accent + brand_name
python DAW_bundle/workspace/brand_generator.py `
  --site minuevamarca `
  --name "Mi Nueva Marca" `
  --accent "#CA8A04" `
  --tone luxury  `# opcional: luxury|tech|organic|minimal`

# 2. (Opcional) Crear DESIGN.md con YAML frontmatter para control avanzado
#    El generador puede leer tokens semánticos desde markdown estructurado
python DAW_bundle/workspace/brand_generator.py `
  --from-design DAW_bundle/site/minuevamarca/DESIGN.md

# 3. Generar design system (usa los brand files generados automáticamente)
python DAW_bundle/workspace/build_design_system.py

# 4. Continuar con pipeline normal (sync colors, brief, deploy)
```

#### Método B: Manual (template + edición)

```powershell
# 1. Copiar template de ejemplo (incluye 64 presets premium pre-cargados)
Copy-Item -Recurse DAW_bundle/site/example DAW_bundle/site/minuevamarca

# 2. Editar identidad visual manualmente en:
#      site/minuevamarca/brand/_design_vars.json
#    Ver site/example/brand/_design_vars.json como referencia.

# 3. Generar design system
python DAW_bundle/workspace/build_design_system.py
```

#### Pipeline completo post-brand (método manual — ahora obsoleto, usar `daw_build.py`)

```powershell
# Sincronizar colores globales en Divi 5
.\wp.bat agentic global_colors sync `
  --design-system="DAW_bundle/site/<DAW_SITE>/design-system/divitheme.json"

# Generar brief (brand-aware: lee _design_vars.json)
python DAW_bundle/workspace/automation/generate_brief.py `
  --prompt "pagina principal de mi nueva marca" `
  --tone editorial

# DIE → plan.json → build + deploy
python DAW_bundle/ml-dataset/artifacts/design_intelligence.py `
  --brief-file=site/<DAW_SITE>/briefs/home.json `
  --output=site/<DAW_SITE>/plans/home.json
.\php.bat DAW_bundle/divi-agentic-core/bin/build_page.php `
  --def=site/<DAW_SITE>/plans/home.json --deploy
```

#### Pipeline orquestado (recomendado — `daw_build.py`)

> **Artefactos one-shot**: `divitheme.json`, `_design_vars.json`, `_design_presets.json` se generan una sola vez. El orquestador detecta automáticamente si están actualizados y evita recompilaciones innecesarias.
> **Visual Impact Engine (VIE)**: Generador determinístico de alto impacto visual. Recomendado sobre ML DIE.

```powershell
# Orquestador unificado: brand → design system → brief → VIE → deploy
#   Primera vez: genera brand + design system (one-shot)
#   Segunda vez: salta brand + design system (stale detection)
#   Usa Visual Impact Engine (deterministic, glass/glow/aura)
python DAW_bundle/workspace/daw_build.py `
  --site aletheia `
  --name "Aletheia Institute" `
  --accent "#CA8A04" `
  --tone luxury `
  --full --vie `
  --prompt "home page for biohacking institute"

# Alternativa: usar ML DIE (template selection + ML)
python DAW_bundle/workspace/daw_build.py `
  --site aletheia `
  --full `
  --prompt "home page for biohacking institute"

# Solo brand + design system (sin deploy)
python DAW_bundle/workspace/daw_build.py `
  --site aletheia `
  --name "Aletheia Institute" `
  --accent "#CA8A04" `
  --tone luxury

# Después de que brand existe: solo generar páginas
python DAW_bundle/workspace/daw_build.py `
  --site aletheia `
  --full `
  --prompt "contact page"

# Forzar regeneración de design system (después de editar brand files)
python DAW_bundle/workspace/daw_build.py `
  --site aletheia `
  --force-design-system `
  --full --prompt "about page"
```

# Forzar regeneración de brand files existentes
python DAW_bundle/workspace/daw_build.py `
  --site aletheia `
  --regenerate `
  --name "Aletheia Institute" `
  --accent "#CA8A04" `
  --tone luxury
```

**Regla**: todo dato de marca va en `site/<DAW_SITE>/brand/`. Plans en `site/<DAW_SITE>/plans/`. Código PHP de build en `divi-agentic-core/bin/`. 
**Framework**: no mezclar datos de proyecto con el código del DAW. `site/` es la frontera.

---

## 8. Reglas DAW

1. No editar `divitheme.json` a mano — regenerar con `build_design_system.py` (v4.0, Visual Intelligence Engine: CIELCH, glass/glow/aura).
2. No usar `divi/code` como comodín — consultar `blocks-dictionary.md` primero.
3. No usar `et_pb_*` (shortcodes Divi 4) — solo namespace `divi/*`.
4. Colores siempre como `{{design:color:*}}`, nunca hex hardcodeados en schemas.
5. `build_page.php` con resolved=true (default) expande presets inline y resuelve tokens.
6. Sin CSS inyectado en `functions.php` ni overrides en `style.css`.
7. Posiciones de gradient sin `%` (el Layout Engine normaliza).
8. **Frontera site/**: todo dato de proyecto va en `site/<DAW_SITE>/`. El framework DAW (skills, plugin, build scripts) no contiene datos de proyecto.
9. **Pipeline de página**: `brief.json → DIE/VIE → plans/<slug>.json → build_page.php --deploy` → página en WP.
10. **VIE (Visual Impact Engine)**: Generador determinístico recomendado. Aplica glass/glow/aura contextual por tipo de sección. Usar con `--vie` en el orquestador.
11. **DIE (ML)**: Disponible como alternativa. Selecciona templates con B2 (Hungarian slot assigner + 9 slot types + column tie-breaker). La decoración la genera E.
12. **Multi-marca**: definir `DAW_SITE=<nombre>` en `.env` (raíz del proyecto). Sin esta variable, el pipeline se detiene con error.
13. **Artefactos one-shot**: `divitheme.json`, `_design_vars.json`, `_design_presets.json` se generan una sola vez por marca. El orquestador detecta staleness automáticamente.
14. **Catálogo de templates**: `workspace/sections/catalog/*.section.json` contiene 877 templates compilados para el DIE.
15. **Sin fallbacks silenciosos**: Si `DAW_SITE` no está definido, el pipeline falla inmediatamente. No se usan marcas por defecto (`bibliotheca`, `aletheia`).

---

## 9. Generador de Briefs Inteligente (generate_brief.py)

El script `generate_brief.py` en `DAW_bundle/workspace/automation/` automatiza el primer paso del flujo de trabajo, traduciendo requerimientos en lenguaje natural de los usuarios a briefs estructurados YAML.

### Características y Operación:
0. **Brand-Aware (nuevo)**: Lee `DAW_SITE` del entorno y construye el `SYSTEM_PROMPT` dinámicamente desde `site/<DAW_SITE>/brand/_design_vars.json`. Si no encuentra vars de marca, usa un prompt genérico premium. Los briefs se guardan en `site/<DAW_SITE>/briefs/`.
1. **Detección Dinámica de Proveedores**: Lee tu archivo `.env` buscando en orden de costo:
   - **DeepSeek** (`DEEPSEEK_API_KEY`) -> Usa `deepseek-chat` de bajísimo costo.
   - **Gemini** (`GEMINI_API_KEY`) -> Modelo `gemini-2.5-flash` ultra económico.
   - **OpenAI** (`OPENAI_API_KEY`) -> Modelo `gpt-4o-mini` rápido y económico.
   - **OpenRouter** (`OPENROUTER_API_KEY`) -> Mapeo inteligente de prefijos (ej. `gpt-4o-mini` -> `openai/gpt-4o-mini`).
   - **Anthropic** (`ANTHROPIC_API_KEY`) -> Modelo `claude-3-5-haiku` como fallback.
   - **Groq** (`GROQ_API_KEY`) -> Modelo `llama-3.3-70b-versatile` para inferencia instantánea gratuita.
2. **Estrategia de Fallback Activo**: Si un proveedor devuelve un error (como caída de DNS o límite excedido), el generador pasa automáticamente al siguiente proveedor activo de la lista.
3. **Bypass de Bloqueos Cloudflare**: Envía un User-Agent de navegador para evitar errores `403 Forbidden (error 1010)` al conectarse a APIs como Groq.
4. **Auto-Mapeo de Modelos Deprecados**: Traduce automáticamente modelos antiguos de Groq (como `llama3-8b-8192`) a sus sucesores activos (`llama-3.1-8b-instant`).
5. **Modo Interactivo**: Si no pasas `--prompt`, te solicitará el requerimiento directamente en la consola interactiva.
6. **Limpieza de Preámbulo de IA**: Limpia el output eliminando explicaciones conversacionales previas y posteriores al bloque YAML.

### Ejemplos de Comandos:
```powershell
# Ejecución simple interactiva
python DAW_bundle/workspace/automation/generate_brief.py

# Especificando un prompt directo, forzando tono estético y depurando la llamada
python DAW_bundle/workspace/automation/generate_brief.py `
  --prompt "hazme una pagina para contacto de mi biblioteca digital" `
  --tone editorial `
  --out contacto `
  --verbose
```

