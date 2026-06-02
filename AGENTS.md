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
│   ├── aletheia/                  <-    Marca actual (ejemplo, ver .env DAW_SITE)
│   │   ├── brand/                 <-       _design_vars.json + _design_presets.json
│   │   ├── page-defs/             <-       ⭐ ENTRADA: JSON semántico del diseñador (tokens {{design:*}}, presets)
│   │   ├── pages/                 <-       SALIDA OPCIONAL: schema resuelto por build_page.php (--out, solo debug)
│   │   ├── plans/                 <-       plan.json generado por DIE (entrada de build_page.php)
│   │   ├── design-system/         <-       divitheme.json generado (64 presets + color derivación + contraste validado)
│   │   ├── briefs/                <-       Briefs de diseño
│   │   ├── content_state/         <-       Estado entre fases (local/ + remote/)
│   │   └── (compositions/ eliminado, usar plans/)
│   └── example/                   <-    Template para nuevas marcas (brand/, plans/, page-defs/, etc.)
├── _archive/                      <- Archivos legacy deprecados (b_semantic_index, compile_catalog,
│   └── die_pipeline/              <-    DIE (ML) pipeline archivado: design_intelligence.py,
│                                      a_section_patterns.py, b_slot_assigner.py,
│                                      c_module_affinities.py, d_content_classifier.py,
│                                      e_decorator.py, e_page_mapper.py, design_director.py)
├── ui-ux-pro-max/                 <- Skill de diseño UI/UX (opcional)
├── daw-skill/SKILL.md             <- FLUJO PRINCIPAL: orquestación de 4 fases
├── daw/                           <- ⭐ SHARED KERNEL (capa 1, sin side effects)
│   ├── cfg.py                     <-    .env parser único + load_daw_site() + path resolvers
│   ├── types.py                   <-    SectionType, Strategy, ImpactLevel (enums str-based)
│   ├── tokens.py                  <-    TokenResolver (resuelve {{design:*}} recursivamente)
│   ├── constants.py               <-    FRONTEND_PRINCIPLES + CONTENT_BANK (single source of truth)
│   └── exc.py                     <-    DawError, ConfigError, SectionTypeNotRegisteredError, ...
├── vie/                           <- ⭐ VISUAL IMPACT ENGINE package (capa 2)
│   ├── __init__.py                <-    Re-exports: VisualImpactEngine, create_vie, ...
│   ├── engine.py                  <-    VisualImpactEngine (orquestador, DI opcional)
│   ├── factory.py                 <-    create_vie() — preferred entry point
│   ├── cli.py                     <-    CLI: --brief-file --design-system --output --seed
│   ├── protocols.py               <-    BlockSelector, PropAdapter, ImpactEvaluator, SectionHandler
│   ├── adapters.py                <-    CatalogLoader + DatasetLoader
│   ├── resolver.py                <-    BrandResolver (token resolution)
│   ├── analysis.py                <-    PageProfileAnalyzer (narrative + contrast plan)
│   ├── selection.py               <-    BlockSelectionEngine (4D scoring + harmony matrix)
│   ├── director.py                <-    ImpactDirector (frontend-design → Divi params)
│   ├── building.py                <-    DecorationBuilder + RowBuilder
│   ├── module.py                  <-    ModuleBuilder
│   ├── section.py                 <-    SectionBuilder (PATH A: design_direction → calculado;
│   │                                     PATH B: original → presets fijos)
│   ├── design_director.py         <-    ⭐ DesignDirector: 5 moods predefinidos + helpers decoration
│   │                                     (academic_night, cool_luxury, warm_minimal,
│   │                                      tech_glass, organic_modern)
│   ├── handlers/                  <-    ⭐ SectionHandler registry (OCP)
│   │   ├── _registry.py           <-       SectionHandler Protocol + register()/get_handler()
│   │   ├── hero.py                <-       HeroSectionHandler + HeroCenteredSectionHandler
│   │   ├── features.py            <-       FeaturesSectionHandler
│   │   ├── stats.py               <-       StatsSectionHandler
│   │   ├── testimonials.py        <-       TestimonialsSectionHandler
│   │   ├── pricing.py             <-       PricingSectionHandler
│   │   ├── faq.py                 <-       FaqSectionHandler
│   │   ├── cta.py                 <-       CtaSectionHandler
│   │   ├── gallery.py             <-       GallerySectionHandler
│   │   ├── contact.py             <-       ContactSectionHandler
│   │   ├── timeline.py            <-       TimelineSectionHandler
│   │   ├── trust_bar.py           <-       TrustBarSectionHandler
│   │   └── content.py             <-       ContentSectionHandler
│   └── strategies/                <-    StrategyProfile (datos + predicates) por estrategia
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
│       ├── visual_impact_engine.py<-       ⭐ SHIM: re-exports desde vie/ (backwards compat)
│       ├── ux_pro_bridge.py       <-       Puente a ui-ux-pro-max (clasificador de estilo)
│       ├── section-patterns.json  <-       Output A (18 tipos, del DIE archivado)
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
#   Brief (UX-Pro deterministic — incluye design_direction automático)
python DAW_bundle/workspace/automation/ux_pro_brief_generator.py --query "descripción breve" --out site/<DAW_SITE>/briefs/<slug>.json
#   O brief con LLM (opcional: --llm en daw_build.py o usar generate_brief.py directamente)
python DAW_bundle/workspace/automation/generate_brief.py --prompt "descripción breve" --tone editorial --out <slug>
#   VIE → plan.json
python DAW_bundle/vie/cli.py --brief-file=DAW_bundle/site/<DAW_SITE>/briefs/<slug>.json --design-system=DAW_bundle/site/<DAW_SITE>/design-system/divitheme.json --output=DAW_bundle/site/<DAW_SITE>/plans/<slug>.json
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

Capa 2a — VIE → plan.json (RECOMENDADO — pipeline activo)
  python vie/cli.py --brief-file=site/<DAW_SITE>/briefs/<slug>.json --design-system=site/<DAW_SITE>/design-system/divitheme.json --output=site/<DAW_SITE>/plans/<slug>.json

  El Visual Impact Engine (VIE) es un generador determinístico (sin ML) que:
    • Lee el brief JSON con secciones semánticas y design_direction opcional
    • Analiza el perfil narrativo del contenido
    • Selecciona bloques Divi 5 óptimos vía 4D scoring + matriz de armonía
    • Construye decoration blocks contextuales: glass, glow, gradients, dividers
    • Resuelve tokens {{design:color:*}} contra el design system
    • Sin design_direction: usa presets fijos predefinidos (PATH B)
    • Con design_direction: genera diseño calculado por mood (PATH A)

Capa 2b — DIE → plan.json (ARCHIVADO — ver §4)
  El pipeline DIE (ML: 877 templates, clasificador TF-IDF, Hungarian slot assigner)
  fue archivado en _archive/die_pipeline/. No usar para páginas nuevas.
  Los artefactos de datos (section-patterns.json, module-affinities.json, etc.)
  permanecen en ml-dataset/artifacts/ como referencia.

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
| `plans/` | **Entrada** — plan.json generado por el VIE con decoration blocks + estructura + tokens `{{design:*}}`. El pipeline lee de aquí. | VIE (`vie/cli.py`) | Trackeado |
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

`_FRONTEND_PRINCIPLES` en `ImpactDirector` adapta las reglas del skill:
- **Typography**: penaliza fonts genéricos (Inter, Arial, Roboto) en scoring
- **Motion**: delays progresivos de 150ms en animaciones
- **Spacing**: padding mínimo de 80px (generous whitespace)
- **Color**: prefiere alto contraste sobre paletas planas
- **Aesthetic**: variantes más distintivas, no rotación genérica

---

## 3c. DesignDirector — Diseño Calculado por Perfil

El VIE tiene dos caminos de diseño, bifurcados en `SectionBuilder.build()`:

### PATH A — diseño calculado (con `design_direction`)

Si el brief incluye un campo `design_direction`, el `DesignDirector` (`vie/design_director.py`)
genera decisiones de diseño concretas a partir de 5 perfiles predefinidos (moods):

| Mood | Fondo oscuro | Acento | Tipografía | Layout | Uso típico |
|------|-------------|-------|-----------|--------|------------|
| `academic_night` | `#0A0E1A` azul marino | `#C9A962` dorado antiguo | Crimson Pro + Space Grotesk | Asimétrico 2/5+3/5 | Campus, educación, institucional |
| `cool_luxury` | `#1C1C1E` gris oscuro | `#0071E3` azul brillante | SF Pro + SF Mono | Centrado, espaciado generoso | SaaS premium, tecnología |
| `warm_minimal` | `#1C1917` crema oscuro | `#C2410C` terracota | Palatino + Inter | Grid simétrico | Restaurantes, lifestyle |
| `tech_glass` | `#0A0A0F` negro | `#00F0FF` cian neón | JetBrains Mono + Inter | Full-bleed, glassmorphism | Startups, tech |
| `organic_modern` | `#1A2E1A` verde bosque | `#F5F5DC` crema | Cormorant Garamond + Inter | Grid masonry | Naturaleza, wellness |

El `DesignProfile` generado incluye 30+ decisiones: colores (bg, texto, acento, divider),
tipografía (display, body, UI), espaciado (hero, section, container), layout rhythm
(centered, asymmetric, grid_3, masonry), motion (none, subtle, dramatic), dividers
(curve, angle, arrow, wave), botones (filled/outline, radius, letter-spacing), y
cards (glass, solid, outline, border-radius).

### PATH B — presets fijos (comportamiento original)

Sin `design_direction`, el VIE usa el comportamiento original: selecciona bloques del
dataset, aplica presets predefinidos (`hero-dark`, `glass-card`, `cta-epic`) y genera
el plan con decoration blocks genéricos. Este camino produce exactamente el mismo
output que antes del refactor (verificado con `verify_regression.py`).

### Cómo usar

En el brief JSON, añadir el campo `design_direction`:

```json
{
  "title": "Nuestros Planteles",
  "slug": "nuestros-planteles",
  "design_direction": {
    "mood": "academic_night",
    "color_temperature": "warm_on_dark",
    "typography_style": "serif_display_plus_sans_ui",
    "layout_rhythm": "dramatic_asymmetric",
    "spacing_density": "generous",
    "accent_material": "gold_antique",
    "motion_intensity": "subtle_parallax"
  },
  "sections": [...]
}
```

El VIE detecta `design_direction` en `engine.py:56` y recrea el `SectionBuilder` con
el profile correspondiente. Todas las secciones se construyen con PATH A.

### Flujo

```
brief.json (con o sin design_direction)
  │
  ├─ sin design_direction → VIE (PATH B)
  │     → SectionBuilder.build()
  │         → ImpactDirector.select_block() → blocks + presets
  │         → plan.json con decoration genérica
  │
  └─ con design_direction → VIE (PATH A)
        → engine.py: detecta design_direction
        → SectionBuilder(pass design_direction)
            → DesignDirector.get_profile(mood) → DesignProfile
            → SectionBuilder._build_designer_section()
                → get_hero_decoration(), get_features_decoration(), ...
                → plan.json con diseño calculado
```

### Regla fundamental

> **Skills = decisión, no datos.** El plan.json solo contiene tokens
> `{{design:color:*}}`, presets Divi y estructuras nativas. La influencia
> externa se resuelve en parámetros internos, nunca en valores literales.

### Archivos

| Archivo | Rol |
|---------|-----|
| `ml-dataset/artifacts/ux_pro_bridge.py` | Clasificador: `UXProBridge.classify()` retorna solo clasificaciones Divi-nativas |
| `vie/design_director.py` | `DesignDirector`: 5 moods predefinidos + helpers decoration (PATH A) |
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
| 2. Plan | `vie/cli.py --brief-file ... --design-system ...` (o `python -m vie.cli`) | Brief JSON + Design System | `site/<DAW_SITE>/plans/<slug>.json` RICO |
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
  --site <DAW_SITE> `
  --name "<Brand Name>" `
  --accent "<#hex>" `
  --tone luxury  # luxury|tech|organic|minimal

python DAW_bundle/workspace/build_design_system.py

# Sincronizar colores globales
.\wp.bat agentic global_colors sync `
  --design-system="DAW_bundle/site/<DAW_SITE>/design-system/divitheme.json"

# 1. Generar brief rico desde UX-Pro
python DAW_bundle/workspace/automation/ux_pro_brief_generator.py `
  --query "about us" `
  --out DAW_bundle/site/<DAW_SITE>/briefs/<slug>.json

# 2. Brief → Plan (VIE v3.0 — determinístico, catálogo + dataset)
python DAW_bundle/vie/cli.py `
  --brief-file="DAW_bundle/site/<DAW_SITE>/briefs/<slug>.json" `
  --design-system="DAW_bundle/site/<DAW_SITE>/design-system/divitheme.json" `
  --output="DAW_bundle/site/<DAW_SITE>/plans/<slug>.json" `
  --evaluate  # opcional: muestra impact score

# 2b. (equivalente — el monolito original es ahora un shim que re-exporta desde vie/)
python DAW_bundle/ml-dataset/artifacts/visual_impact_engine.py `
  --brief-file="DAW_bundle/site/<DAW_SITE>/briefs/<slug>.json" `
  --design-system="DAW_bundle/site/<DAW_SITE>/design-system/divitheme.json" `
  --output="DAW_bundle/site/<DAW_SITE>/plans/<slug>.json"

# 3. Plan → WordPress
.\php.bat DAW_bundle/divi-agentic-core/bin/build_page.php `
  --def=DAW_bundle/site/<DAW_SITE>/plans/<slug>.json `
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
Site/UX-Pro BM25  →  Brief JSON (riche)  →  VIE v3.0 (vie/)  →  build_page.php --deploy
```

| Paso | Script | Output |
|------|--------|--------|
| 1. Brand + Design System | `workspace/brand_generator.py` + `workspace/build_design_system.py` | `site/<DAW_SITE>/brand/` + `design-system/divitheme.json` |
| 2. Brief | `workspace/automation/ux_pro_brief_generator.py --query "..."` | `site/<DAW_SITE>/briefs/<slug>.json` |
| 3. Plan | `vie/cli.py --brief-file ...` (preferred) | `site/<DAW_SITE>/plans/<slug>.json` |
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
| Build page | `divi-agentic-core/bin/build_page.php` | Único script PHP: lee plan → resuelve tokens → deploy (usa `DAW_SITE` env) |
| Design system (generado) | `site/<DAW_SITE>/design-system/divitheme.json` | 64 presets, fuente de verdad de tokens |
| Variables de entrada | `site/<DAW_SITE>/brand/_design_vars.json` | Colores, fonts, radios, espacio |
| Presets de diseño | `site/<DAW_SITE>/brand/_design_presets.json` | 64 presets (section/text/module/divider/animation/scroll/hover) |
| Definiciones de página | `site/<DAW_SITE>/page-defs/` | JSON de entrada (home.json, about.json...) |
| Briefs de diseño | `site/<DAW_SITE>/briefs/` | JSON de entrada para el orquestador (ej: home.json) |
| Templates de sección | `workspace/sections/` | _base.section.json + *.variant.json + catalog/*.section.json |
| Catálogo de templates | `workspace/sections/catalog/` | 877 templates compilados como .section.json |
| Patrones de diseño | `ml-dataset/artifacts/section-patterns.json` | 18 tipos de sección, composición + module affinity |
| VIE (Visual Impact Engine) | `vie/` (package) | ⭐ Generador determinístico contextual: glass/glow/aura por tipo de sección. Entry: `python -m vie.cli` |
| VIE — DesignDirector | `vie/design_director.py` | ⭐ 5 moods predefinidos (academic_night, cool_luxury, warm_minimal, tech_glass, organic_modern) + helpers decoration |
| VIE — shim legacy | `ml-dataset/artifacts/visual_impact_engine.py` | Backwards-compat shim (1,480L → 50L) desde `vie/`. Conserva la API antigua. |
| VIE — sección handlers | `vie/handlers/` | ⭐ Registry OCP: 12 handlers. Añadir section_type = 1 archivo. |
| VIE — estrategias | `vie/strategies/` | StrategyProfile (datos + predicates). 5 impls: cool-luxury, warm-luxury, tech-glass, minimal, organic. |
| Shared Kernel | `daw/` | Capa 1: cfg, types, tokens, constants, exc. Sin side effects al importar. |
| Brand Generator | `workspace/brand_generator.py` | Genera _design_vars.json + _design_presets.json desde CLI |
| Orquestador | `workspace/daw_build.py` | ⭐ Un comando: brand → design → brief → VIE → deploy |
| UXProBridge | `ml-dataset/artifacts/ux_pro_bridge.py` | Puente a ui-ux-pro-max: color, tipografía, patrones, efectos |
| Dataset DIE | `ml-dataset/dataset.jsonl` | 877 registros (archivado, sólo referencia) |
| DIE pipeline (archivado) | `_archive/die_pipeline/` | 8 scripts: design_intelligence.py, a_section_patterns.py, b_slot_assigner.py, c_module_affinities.py, d_content_classifier.py, e_decorator.py, e_page_mapper.py, design_director.py |
| Plugin WordPress | `divi-agentic-core/` | Layout Engine, CLI, metadata |

---

## 7. Estructura de Carpetas

Cada tipo de archivo tiene su carpeta asignada. No crear archivos fuera de su ubicación:

| Carpeta | Contenido |
|---------|-----------|
| `site/<DAW_SITE>/brand/` | ⭐ Datos de marca: `_design_vars.json` + `_design_presets.json` |
| `site/<DAW_SITE>/plans/` | ⭐ plan.json generado por VIE (entrada de build_page.php) |
| `site/<DAW_SITE>/pages/` | Schemas resueltos (output opcional de `build_page.php --out`, solo para debug/inspección) |
| `site/<DAW_SITE>/design-system/` | `divitheme.json` generado (output, gitignored) |
| `site/<DAW_SITE>/briefs/` | ⭐ Briefs JSON de diseño (entrada del orquestador) |
| ~~`site/<DAW_SITE>/compositions/`~~ | ❌ Eliminado (usar `plans/`) |
| `site/<DAW_SITE>/content_state/` | Estado de contenido entre fases (local/ + remote/) |
| `site/example/` | Template de estructura para nuevas marcas |
| `daw/` | ⭐ Shared kernel (capa 1). `cfg.py` (`.env` parser único), `types.py` (Enums), `tokens.py` (TokenResolver), `constants.py` (FRONTEND_PRINCIPLES + CONTENT_BANK), `exc.py`. Sin side effects al importar. |
| `vie/` | ⭐ Visual Impact Engine package (capa 2). 13 módulos: `engine.py`, `factory.py`, `cli.py`, `protocols.py`, `adapters.py`, `resolver.py`, `analysis.py`, `selection.py`, `director.py`, `building.py`, `module.py`, `section.py`, `design_director.py`. |
| `vie/handlers/` | ⭐ SectionHandler registry (OCP). 12 handlers (1 archivo cada uno). Para añadir un section_type nuevo = crear archivo + añadir 1 import. |
| `vie/strategies/` | StrategyProfile: cool-luxury, warm-luxury, tech-glass, minimal, organic. |
| `workspace/sections/` | ⭐ Templates de sección con variantes de decoración |
| `workspace/sections/catalog/` | 877 templates compilados como .section.json (referencia histórica) |
| `ml-dataset/artifacts/section-patterns.json` | Output A del DIE archivado: 18 tipos de sección |
| `workspace/data/modules/` | Schemas de módulos Divi 5 (103, generados por PHP) |
| `workspace/automation/` | Scripts de automatización |
| `workspace/daw_build.py` | ⭐ Orquestador unificado: brand → design → brief → VIE → deploy |
| `workspace/brand_generator.py` | Generador automático de brand files desde CLI |
| `workspace/build_design_system.py` | Visual Intelligence Engine v4.0 (CIELCH, glass/glow/aura) |
| `ml-dataset/` | Dataset + artefactos ML del DIE (archivado, solo referencia) |
| `ml-dataset/artifacts/` | Outputs de datos del DIE: section-patterns.json, module-affinities.json, etc. |
| `_archive/die_pipeline/` | ⚠️ Pipeline ML archivado: design_intelligence.py + artefactos A/B/C/D/E |
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
  --site <nueva-marca> `
  --name "<Brand Name>" `
  --accent "<#hex>" `
  --tone luxury  # luxury|tech|organic|minimal

# 2. (Opcional) Crear DESIGN.md con YAML frontmatter para control avanzado
#    El generador puede leer tokens semánticos desde markdown estructurado
python DAW_bundle/workspace/brand_generator.py `
  --from-design DAW_bundle/site/<nueva-marca>/DESIGN.md

# 3. Generar design system (usa los brand files generados automáticamente)
python DAW_bundle/workspace/build_design_system.py

# 4. Continuar con pipeline normal (sync colors, brief, deploy)
```

#### Método B: Manual (template + edición)

```powershell
# 1. Copiar template de ejemplo (incluye 64 presets premium pre-cargados)
Copy-Item -Recurse DAW_bundle/site/example DAW_bundle/site/<nueva-marca>

# 2. Editar identidad visual manualmente en:
#      site/<nueva-marca>/brand/_design_vars.json
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

# VIE → plan.json → build + deploy
python DAW_bundle/vie/cli.py `
  --brief-file=site/<DAW_SITE>/briefs/home.json `
  --design-system=site/<DAW_SITE>/design-system/divitheme.json `
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
  --site <DAW_SITE> `
  --name "<Brand Name>" `
  --accent "<#hex>" `
  --tone luxury `
  --full --vie `
  --prompt "descripción de la página"

# Alternativa: usar ML DIE (template selection + ML)
python DAW_bundle/workspace/daw_build.py `
  --site <DAW_SITE> `
  --full `
  --prompt "descripción de la página"

# Solo brand + design system (sin deploy)
python DAW_bundle/workspace/daw_build.py `
  --site <DAW_SITE> `
  --name "<Brand Name>" `
  --accent "<#hex>" `
  --tone luxury

# Después de que brand existe: solo generar páginas
python DAW_bundle/workspace/daw_build.py `
  --site <DAW_SITE> `
  --full `
  --prompt "contact page"

# Forzar regeneración de design system (después de editar brand files)
python DAW_bundle/workspace/daw_build.py `
  --site <DAW_SITE> `
  --force-design-system `
  --full --prompt "about page"
```

# Forzar regeneración de brand files existentes
python DAW_bundle/workspace/daw_build.py `
  --site <DAW_SITE> `
  --regenerate `
  --name "<Brand Name>" `
  --accent "<#hex>" `
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
9. **Pipeline de página**: `brief.json → VIE → plans/<slug>.json → build_page.php --deploy` → página en WP.
10. **VIE (Visual Impact Engine)**: Generador determinístico. Usar `--vie` en el orquestador o `python vie/cli.py` directamente.
11. **DIE (ML)**: Archivado en `_archive/die_pipeline/`. No usar para páginas nuevas. Los artefactos de datos quedan como referencia.
12. **Multi-marca**: definir `DAW_SITE=<nombre>` en `.env` (raíz del proyecto). Sin esta variable, el pipeline se detiene con error.
13. **Artefactos one-shot**: `divitheme.json`, `_design_vars.json`, `_design_presets.json` se generan una sola vez por marca. El orquestador detecta staleness automáticamente.
14. **Catálogo de templates**: `workspace/sections/catalog/*.section.json` contiene 877 templates (referencia histórica, no activo).
15. **Sin fallbacks silenciosos**: Si `DAW_SITE` no está definido, el pipeline falla inmediatamente. No se usan marcas por defecto (`bibliotheca`, `aletheia`).
16. **VIE — añadir section_type**: crear `vie/handlers/<tipo>.py` con `@register("<tipo>")` + import en `vie/handlers/__init__.py`. **No** tocar `SectionBuilder._build_rows()` (es registry-backed, OCP).
17. **VIE — añadir estrategia**: agregar profile en `vie/strategies/__init__.py` (`COOL_LUXURY_PROFILE = {...}`) y registrar en `_PROFILE_BY_STRATEGY`. **No** agregar `if "X" in strategy` en código de aplicación.
18. **Shared kernel**: toda nueva dependencia cross-cutting (config, types, tokens) va en `daw/`. No duplicar `.env` parsers ni TokenResolvers.
19. **DesignDirector**: usar `design_direction` en el brief para activar PATH A (diseño calculado por mood). Sin ella, PATH B preserva el comportamiento original. 5 moods: `academic_night`, `cool_luxury`, `warm_minimal`, `tech_glass`, `organic_modern`.

---

## 8b. Arquitectura en Capas (post-refactor)

El DAW_bundle está organizado en 3 capas con un **Shared Kernel**:

```
┌──────────────────────────────────────────────────────────────────────┐
│ CAPA 3 — CLI / Orquestador                                          │
│   workspace/daw_build.py · workspace/brand_generator.py             │
│   workspace/build_design_system.py · vie/cli.py                     │
│   workspace/automation/{ux_pro,m}_brief_generator.py                 │
│   divi-agentic-core/bin/build_page.php (PHP — único subprocess real)│
├──────────────────────────────────────────────────────────────────────┤
│ CAPA 2 — Aplicación                                                  │
│   vie/                — Visual Impact Engine (13 módulos)            │
│   └── vie/handlers/   — SectionHandler registry (OCP, 12 entries)   │
│   └── vie/strategies/ — StrategyProfile (5 implementaciones)         │
│   └── vie/design_director.py — DesignDirector (5 moods PATH A)      │
│   (dsgn/, briefgen/ son ROADMAP — ver PLAN §5.3; no implementados)  │
├──────────────────────────────────────────────────────────────────────┤
│ CAPA 1 — Shared Kernel (sin side effects al importar)               │
│   daw/cfg.py       — load_daw_site(), get_*_dir(), .env parser       │
│   daw/types.py     — SectionType, Strategy (Enums str-based)         │
│   daw/tokens.py    — TokenResolver (recursivo, único)                │
│   daw/constants.py — FRONTEND_PRINCIPLES, CONTENT_BANK               │
│   daw/exc.py       — DawError, ConfigError, etc.                     │
└──────────────────────────────────────────────────────────────────────┘
```

**Reglas de dependencia:** capa N puede importar de capa N-1 y N-2, nunca de capa N+1. En particular:
- Capa 3 importa de Capa 2 y Capa 1 (ej: `daw_build.py → vie.factory.create_vie()` y `daw.cfg.load_daw_site()`).
- Capa 2 importa de Capa 1 (ej: `vie.resolver.BrandResolver → daw.tokens.TokenResolver`).
- Capa 1 **no** importa de Capa 2 ni de Capa 3. Test: `python -c "import daw"` debe ser silencioso (sin .env, sin sys.exit, sin stdout).

**Estado real vs roadmap:**
- ✅ Implementado: `daw/` (shared kernel), `vie/` (engine), `vie/handlers/` (registry), `vie/strategies/` (profiles).
- 📋 Roadmap: `dsgn/` (extraer lógica de `workspace/build_design_system.py` a paquete) y `briefgen/` (extraer lógica de `workspace/automation/{ux_pro,m}_brief_generator.py`). No hay tareas abiertas para esto en TASKS_RESOLVE_ANTIPATRONES.md; son ideas de una futura iteración del refactor.

**Beneficios medibles del refactor (PLAN_RESOLVE_ANTIPATRONES.md):**
- `_load_daw_site()`: 3 implementaciones → 1
- Parsers de `.env`: 6 implementaciones → 1
- Token resolvers: 3 implementaciones → 1
- Switch de section types (12 casos): → registry OCP
- `visual_impact_engine.py`: 1,480 L monolito → 13 módulos (<350 L c/u) + shim legacy de 50 L
- `import daw` y `import vie` son silenciosos (no leen `.env`, no `sys.exit()`, no stdout)

Verificación de regresión: `python _tools/verify_regression.py --seed 42` debe producir `0ba2d6e76ea62607942064b982c85694` byte-idéntico al baseline (ejecutar desde raíz del proyecto).

---

## 9. Generador de Briefs por LLM (generate_brief.py — opcional)

El script `generate_brief.py` en `DAW_bundle/workspace/automation/` es el **generador opcional por LLM**. Por defecto se usa `ux_pro_brief_generator.py` (determinístico, BM25, incluye `design_direction` automático).
Para usar el LLM, pasar `--llm` en `daw_build.py` o ejecutar `generate_brief.py` directamente.

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
6. **Limpieza de Preámbulo de IA**: Limpia el output eliminando explicaciones conversacionales previas y posteriores al bloque JSON.

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

