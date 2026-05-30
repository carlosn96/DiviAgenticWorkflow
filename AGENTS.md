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
│   ├── bibliotheca/               <-    Marca activa: San Pablo MX / Bibliotheca
│   │   ├── brand/                 <-       _design_vars.json + _design_presets.json
│   │   ├── page-defs/             <-       ⭐ ENTRADA: JSON semántico del diseñador (tokens {{design:*}}, presets)
│   │   ├── pages/                 <-       SALIDA OPCIONAL: schema resuelto por build_page.php (--out, solo debug)
│   │   ├── design-system/         <-       divitheme.json generado (64 presets + color derivación + contraste validado)
│   │   ├── briefs/                <-       Briefs de diseño
│   │   └── content_state/         <-       Estado entre fases (local/ + remote/)
│   └── example/                   <-    Template para nuevas marcas (brand/, page-defs/, etc.)
├── ui-ux-pro-max/                 <- Skill de diseño UI/UX (opcional)
├── daw-skill/SKILL.md             <- FLUJO PRINCIPAL: orquestación de 4 fases
├── workspace/                     <- Caché, datos extraídos, scripts one-time
│   ├── build_design_system.py     <- DISEÑO INTELIGENTE v3.0: deriva colores, valida contraste WCAG, enriquece 64 presets
│   ├── design-patterns.json       <- Patrones extraídos de 877 catálogos Divi 4 (O(1) keyed)
│   ├── extract_patterns.py        <- One-time: analiza 892 templates → design-patterns.json
│   ├── data/modules/              <- Schemas de módulos generados por PHP (102 módulos)
│   └── sections/                  <- ⭐ Templates de sección con variantes
│       ├── hero-split/            <-    Templates locales curados (con variantes)
│       ├── catalog/               <-    877 templates del catálogo compilados como .section.json
│       └── ... (*.section.json para templates sin variante)
├── ml-dataset/                    <- ⭐ ML Artifacts: Design Intelligence Engine
│   ├── dataset.jsonl              <-    877 registros limpios con contenido real
│   ├── PLAN.md                    <-    Arquitectura de los 4 artefactos
│   ├── TASKS.md                   <-    Tracking de artefactos
│   └── artifacts/                 <-    Scripts + modelos del DIE
│       ├── design_intelligence.py <-       Orquestador DIE (--brief-file, --section-file)
│       ├── a_section_patterns.py  <-       Artefacto A: patrones de sección
│       ├── b_semantic_index.py    <-       Artefacto B: índice semántico
│       ├── c_module_affinities.py <-       Artefacto C: afinidades PMI
│       ├── d_content_classifier.py<-       Artefacto D: clasificador de contenido
│       ├── section-patterns.json  <-       Output A (18 tipos)
│       ├── semantic-index.pkl     <-       Output B (892 items)
│       ├── module-affinities.json <-       Output C (matriz PMI)
│       └── content-classifier.pkl <-       Output D (98.2% acc)
└── divi-agentic-core/
    ├── Plugin WordPress (Layout Engine, CLI, metadata)
    └── bin/
        ├── env_loader.php         <- ⭐ Carga .env automáticamente (DAW_SITE, API keys, etc.)
        ├── build_page.php         <- ⭐ ÚNICO script: lee page-def → resuelve tokens → expande presets → deploy (quality gate incluido)
        └── verify_page.php        <- Verificación post-deploy
```

---

## ⚡ Primeros Pasos (Quickstart)

> **Python**: Usar el intérprete Python global del sistema (el que esté disponible en PATH como `python`).
> Verificar con: `python --version`. No usar entornos virtuales (venv).
> El pipeline de páginas es: DIE (ML opcional) → plan.json → build_page.php --deploy.
> El DIE (Design Intelligence Engine) sí requiere Python para generar planes ML — pero es opcional: si el script no existe, el orquestador cae al lookup tradicional.

```powershell
# 0. ⚡ Elegir marca activa (OBLIGATORIO si cambias de proyecto)
#    Editar .env en raíz del proyecto y definir:
#      DAW_SITE=nombre-de-tu-marca
#    Todas las rutas site/<DAW_SITE>/ se resuelven automáticamente.
#    Si no se define, defaults a 'bibliotheca'.

# 1. Activar el plugin
#    Ir a WP Admin > Plugins > "Divi Agentic Core" > Activar
#    (junction link desde DAW_bundle/divi-agentic-core/ → app/public/wp-content/plugins/)

# 2. Configurar entorno
Copy-Item DAW_bundle/.env.example .env        # editar con credenciales reales

# 3a. (una vez) Generar schemas de módulos Divi 5
.\php.bat DAW_bundle/divi-agentic-core/bin/generate-module-schema.php --all

# 3b. (opcional, una vez) Instalar dependencias Python para DIE (Design Intelligence Engine)
python -m pip install -r ml-dataset/requirements.txt
#    Esto instala: scikit-learn, sentence-transformers, torch (CPU), numpy, scipy, transformers, huggingface-hub
#    Luego verificar que los artefactos existen (ya pre-construidos):
dir ml-dataset/artifacts/*.pkl, ml-dataset/artifacts/*.json

# 3c. (opcional, una vez) Instalar dependencias para buscador semántico de catálogos (legacy)
python -m pip install -r DAW_bundle/workspace/automation/requirements.txt
#    Luego compilar el índice semántico (una vez):
python DAW_bundle/workspace/automation/generate_embeddings.py

# 3d. (una vez por proyecto) Pre-compilar catálogo completo a Divi 5
#    Traduce los 892 layouts del catálogo a esquemas Divi 5 tokenizados y slotificados de una sola vez
python DAW_bundle/workspace/automation/compile_catalog.py

# 4. (una vez por marca) Generar design system
#    Variables en: site/<DAW_SITE>/brand/_design_vars.json
#    Presets en:   site/<DAW_SITE>/brand/_design_presets.json
$env:DAW_SITE="bibliotheca"
python DAW_bundle/workspace/build_design_system.py

# 5. Sincronizar colores globales en Divi 5
.\wp.bat agentic global_colors sync `
  --design-system="DAW_bundle/site/bibliotheca/design-system/divitheme.json"

# 6a. (Opcional) Generar brief YAML desde lenguaje natural
#     Configura tu API key en .env (DEEPSEEK_API_KEY, GEMINI_API_KEY, OPENAI_API_KEY, etc.)
python DAW_bundle/workspace/automation/generate_brief.py --prompt "hazme una pagina para contacto de mi biblioteca digital"

# 6b. (Recomendado) DIE → plan.json → build + deploy
python DAW_bundle/ml-dataset/artifacts/design_intelligence.py --brief-file=site/bibliotheca/briefs/contacto-biblioteca.json --output=site/bibliotheca/plans/contacto.json
.\php.bat DAW_bundle/divi-agentic-core/bin/build_page.php --def=site/bibliotheca/plans/contacto.json --deploy
```

---

## 2. Pipeline: diseño → deploy (PHP unificado)

```
Capa 0 — Module Schemas (PHP, fuente única de estructura)
  php divi-agentic-core/bin/generate-module-schema.php --all
  → Lee _all_modules_metadata.php (metadata real de Divi 5)
  → workspace/data/modules/<slug>.json (102 módulos, estructura autoritativa)
  ⚠️ build_page.php NO define atributos de módulo — los carga de estos JSONs.

Capa 1 — Design System (build_design_system.py)
  site/bibliotheca/brand/_design_vars.json + site/bibliotheca/brand/_design_presets.json
  → build_design_system.py
  → site/bibliotheca/design-system/divitheme.json
    (64 presets: section/text/module/divider/animation/scroll/hover + tokens {{design:type:name}})

Capa 2a — DIE → plan.json (RECOMENDADO)
  python ml-dataset/artifacts/design_intelligence.py --brief-file=site/<DAW_SITE>/briefs/<slug>.json --output=site/<DAW_SITE>/plans/<slug>.json

  design_intelligence.py (DIE v3.0) hace TODO en un solo proceso:
    • Carga A+B+C+D+E como módulos Python (sin archivos intermedios)
    • Lee brief JSON con tone, product_type, sections[]
    • Clasifica cada sección con D (content classifier)
    • Busca template similar con B (semantic index)
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

## 4. Crear una página nueva

### A. Con DIE (recomendado)

0. (Una vez) Construir artefactos ML:
   ```
   python ml-dataset/artifacts/e_decorator.py --build        # ← decoration clusters + rules
   python ml-dataset/artifacts/d_content_classifier.py       # ← content-classifier.pkl
   python ml-dataset/artifacts/b_semantic_index.py           # ← semantic-index.pkl
   python ml-dataset/artifacts/a_section_patterns.py         # ← section-patterns.json
   python ml-dataset/artifacts/c_module_affinities.py        # ← module-affinities.json
   ```
   > Si los artefactos no existen, el DIE funciona con defaults para estructura.

1. Crear brief en `site/<DAW_SITE>/briefs/<slug>.json`:
   ```json
   {
     "title": "Mi Página",
     "slug": "mi-pagina",
     "tone": "editorial",
     "product_type": "bibliotheca",
     "sections": [
       {
         "section_type": "hero",
         "title": "Título Principal",
         "text": "Descripción...",
         "btn_primary_text": "Acción"
       }
     ]
   }
   ```

2. DIE → plan.json:
   ```
   python ml-dataset/artifacts/design_intelligence.py --brief-file=site/<DAW_SITE>/briefs/<slug>.json --output=site/<DAW_SITE>/plans/<slug>.json
   ```
   > El DIE carga A+B+C+D+E, genera decoration blocks con `{{design:color:*}}` tokens, y produce plan.json listo para build.

3. Build + Deploy:
   ```
   .\php.bat divi-agentic-core/bin/build_page.php --def=site/<DAW_SITE>/plans/<slug>.json --deploy
   ```

### B. Directo (page-def.json — legacy)

0. (Una vez por proyecto o tras actualizar Divi) Regenerar schemas de módulos:
   ```
   .\php.bat DAW_bundle/divi-agentic-core/bin/generate-module-schema.php --all
   ```

1. Crear definición de página en `site/<DAW_SITE>/page-defs/<slug>.json`:

   > `DAW_SITE` defaults to `bibliotheca`. Para usar otra marca: `$env:DAW_SITE="minuevamarca"`

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
   .\php.bat DAW_bundle/divi-agentic-core/bin/build_page.php --def=site/bibliotheca/page-defs/mi-pagina.json --deploy
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

No editar `divitheme.json` a mano. Usar `build_design_system.py` (v3.0, design intelligence):

```powershell
# La herramienta ahora tiene inteligencia de diseño:
#   - Deriva automáticamente 26 colores desde un solo color_accent
#   - Valida contraste WCAG AA/AAA
#   - Añade hover states a módulos interactivos
#   - Convierte tipografía fija a fluida con clamp()
#   - Añade presets faltantes (glass-card, divisores SVG, motion)
python DAW_bundle/workspace/build_design_system.py ^
  --vars DAW_bundle/site/bibliotheca/brand/_design_vars.json ^
  --presets DAW_bundle/site/bibliotheca/brand/_design_presets.json ^
  --out DAW_bundle/site/bibliotheca/design-system/divitheme.json
```

Para otra marca: `$env:DAW_SITE="otramarca"` antes de ejecutar, o pasar rutas explicitas con `--vars`/`--presets`/`--out`.

Sincronizar colores globales en Divi 5:
```
.\wp.bat agentic global_colors sync ^
  --design-system="DAW_bundle/site/bibliotheca/design-system/divitheme.json"
```

El generador auto-descubre tokens por prefijo (`color_`, `font_`, `radius_`, `space_`) de cualquier archivo de variables. No hay nombres hardcodeados en Python — funciona con cualquier marca.

**Colores**: se referencian como `{{design:color:name}}` y el resolver los convierte a `var(--gcid-name)` (dinámico). Los tokens en `divitheme.json` mantienen valores hex para el sync de gcids.

**Fonts, radii, spacing**: se referencian como `{{design:font:name}}`, `{{design:radius:name}}`, `{{space_name}}` y se resuelven a literales (horneados en build).

---

## 5. Prerrequisito: Global Colors (gcid)

Antes del primer deploy, sincronizar colores. El verificador de hash está en `_dac_gcid_hash`:

| Acción | Comando |
|--------|---------|
| Sincronizar | `wp agentic global_colors sync --design-system="DAW_bundle/site/bibliotheca/design-system/divitheme.json"` |
| Verificar estado | `wp agentic global_colors status --design-system="..."` |
| Listar activos | `wp agentic global_colors list` |

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
| Patrones de diseño | `workspace/design-patterns.json` | O(1) keyed: composition + module affinity + color clusters |
| DIE — Design Intelligence Engine | `ml-dataset/artifacts/design_intelligence.py` | ⭐ Orquestador ML: clasifica + busca + recomienda + decora (A+B+C+D+E) |
| DIE — Artefacto A | `ml-dataset/artifacts/a_section_patterns.py` | Patrones estructurales de 877 templates |
| DIE — Artefacto B | `ml-dataset/artifacts/b_semantic_index.py` | Índice semántico (892 templates, 384-dim embeddings) |
| DIE — Artefacto C | `ml-dataset/artifacts/c_module_affinities.py` | Matriz PMI de co-ocurrencia de módulos |
| DIE — Artefacto D | `ml-dataset/artifacts/d_content_classifier.py` | Clasificador TF-IDF + Naive Bayes (98.2% acc) |
| DIE — Artefacto E | `ml-dataset/artifacts/e_decorator.py` | Decoration Engine: K-means clusters + 4 CSVs → decoration blocks |
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
| `workspace/design-patterns.json` | Patrones O(1) extraídos de 877 catálogos |
| `workspace/data/modules/` | Schemas de módulos Divi 5 (102, generados por PHP) |
| `workspace/automation/` | Scripts de automatización |
| `workspace/build_design_system.py` | Generador de design system v3.0 (inteligencia de diseño) |
| `ml-dataset/` | ⭐ Dataset + artefactos ML del DIE |
| `ml-dataset/artifacts/` | Scripts + modelos del DIE (A, B, C, D + orquestador) |
| `divi-agentic-core/bin/` | ⭐ build_page.php + verify_page.php + generate-module-schema (orquestador eliminado) |
| `daw-skill/` | Skill de orquestación y sus referencias |
| `divi-agentic-core/` | Plugin WordPress |
| `ui-ux-pro-max/` | Skill auxiliar de diseño UI/UX (opcional) |

### Cómo crear una nueva marca

> ⚠️ **Antes de empezar**: editar `.env` en la raíz del proyecto y definir `DAW_SITE=nombre-de-tu-marca`.
> Todos los scripts PHP leen `.env` automáticamente vía `env_loader.php`. No necesitas `$env:DAW_SITE`.

```powershell
# 1. Copiar template de ejemplo (incluye 64 presets premium pre-cargados)
Copy-Item -Recurse DAW_bundle/site/example DAW_bundle/site/minuevamarca

# 2. Editar identidad visual (REQUERIDO)
#    El template ya trae 64 presets completos (section, text, module, divider,
#    animation, scroll, transform) con {{design:color:*}} tokens.
#    Solo necesitas definir colores y tipografías en:
#      site/minuevamarca/brand/_design_vars.json
#    build_design_system.py deriva automáticamente ~26 colores desde color_accent.
#    Ver site/example/brand/_design_vars.json como referencia.

# 3. Editar .env con la marca activa
#    En .env (raíz del proyecto): DAW_SITE=minuevamarca

# 4. Generar design system (resuelve tokens, valida contraste WCAG, enriquece presets)
python DAW_bundle/workspace/build_design_system.py

# 5. Sincronizar colores globales en Divi 5
.\wp.bat agentic global_colors sync `
  --design-system="DAW_bundle/site/minuevamarca/design-system/divitheme.json"

# 6. Generar brief (ahora es brand-aware: lee _design_vars.json para el prompt)
python DAW_bundle/workspace/automation/generate_brief.py `
  --prompt "pagina principal de mi nueva marca" `
  --tone editorial

# 7. DIE → plan.json → build + deploy
python DAW_bundle/ml-dataset/artifacts/design_intelligence.py --brief-file=site/bibliotheca/briefs/home.json --output=site/bibliotheca/plans/home.json
.\php.bat DAW_bundle/divi-agentic-core/bin/build_page.php --def=site/bibliotheca/plans/home.json --deploy
```

**Regla**: todo dato de marca va en `site/<DAW_SITE>/brand/`. Plans en `site/<DAW_SITE>/plans/`. Código PHP de build en `divi-agentic-core/bin/`. 
**Framework**: no mezclar datos de proyecto con el código del DAW. `site/` es la frontera.

---

## 8. Reglas DAW

1. No editar `divitheme.json` a mano — regenerar con `build_design_system.py` (v3.0, design intelligence: deriva colores, valida contraste, enriquece presets).
2. No usar `divi/code` como comodín — consultar `blocks-dictionary.md` primero.
3. No usar `et_pb_*` (shortcodes Divi 4) — solo namespace `divi/*`.
4. Colores siempre como `{{design:color:*}}`, nunca hex hardcodeados en schemas.
5. `build_page.php` con resolved=true (default) expande presets inline y resuelve tokens.
6. Sin CSS inyectado en `functions.php` ni overrides en `style.css`.
7. Posiciones de gradient sin `%` (el Layout Engine normaliza).
8. **Frontera site/**: todo dato de proyecto va en `site/<DAW_SITE>/`. El framework DAW (skills, plugin, build scripts) no contiene datos de proyecto.
9. **Pipeline de página**: `brief.json → DIE (Python) → plans/<slug>.json → build_page.php --deploy` → página en WP.
10. El DIE (ML, Python) genera el plan. `build_page.php` (PHP) ejecuta el deploy. Cada uno en su lenguaje.
11. **Multi-marca**: definir `DAW_SITE=<nombre>` en `.env` (raíz del proyecto). Todos los scripts PHP lo leen automáticamente vía `env_loader.php`. No necesita `$env:` ni vars de sistema.
12. **Marca activa obligatoria**: antes de cualquier operación, verificar que `.env` contiene `DAW_SITE=<marca>`. Si no está definido, defaults a `bibliotheca` con advertencia.
13. **Pipeline completo**: brief → **DIE (A+B+C+D+E)** → plan.json → `build_page.php --deploy` → quality gate → página en WP. Sin orchestrate_page, compose_page, post_compose.
    - El DIE se llama UNA vez por página (no por sección), cargando modelos una sola vez.
    - decoration blocks usan `{{design:color:*}}` tokens, nunca hex.
    - 7 clusters K-means (scikit-learn) sobre 877 templates reales, combinados con 4 CSVs curados.
14. **Catálogo de templates**: `workspace/sections/catalog/*.section.json` contiene 877 templates compilados. El DIE los selecciona por similitud semántica (B). La decoración la genera E, no viene del template.

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

