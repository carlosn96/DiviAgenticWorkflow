# DAW — Divi Agentic Workflow

Pipeline completo de diseño → deploy para Divi 5.5.0. Este documento describe el flujo real, no el idealizado.

Todos los paths son relativos a `DAW_bundle/` salvo que se indique. Los comandos se ejecutan desde la raíz del proyecto (`divitheme/`).

---

## 1. Mapa del DAW

```
DAW_bundle/
├── AGENTS.md                      <- Este archivo (fuente de verdad del pipeline real)
├── README.md
├── .env.example
├── .gitignore
├── wp.bat, php.bat, mysql.bat     <- Wrappers que delegan a raíz del proyecto
├── site/                          <- ⭐ DATOS DE PROYECTO (separados del framework)
│   ├── <DAW_SITE>/                <-    Marca apuntada por .env DAW_SITE
│   │   ├── brand/                 <-       _design_vars.json + _design_presets.json
│   │   │   └── assets/css/        <-       brand.css generado (único, por marca)
│   │   ├── page-defs/             <-       Definiciones de página (entrada del diseñador)
│   │   │   ├── home.json          <-          Manifiesto: lista de secciones
│   │   │   ├── (manifest)        <-          Manifiesto + secciones en sections/
│   │   │   └── sections/          <-          Archivos de sección individuales
│   │   ├── plans/                 <-       plan.json generado por VIE (entrada alternativa)
│   │   ├── design-system/         <-       divitheme.json generado (58 presets)
│   │   ├── briefs/                <-       Briefs de diseño (entrada del orquestador)
│   │   └── content_state/         <-       Estado entre fases (local/ + remote/)
│   └── example/                   <-    Template para nuevas marcas
├── _archive/                      <- Código y marcas archivadas
│   └── die_pipeline/              <-    DIE (ML) archivado: design_intelligence.py + artefactos
├── ui-ux-pro-max/                 <- Skill de diseño UI/UX (opcional)
├── daw-skill/SKILL.md             <- ⭐ Orquestación de 4 fases (referencia del skill)
├── daw/                           <- Shared kernel (cfg, types, tokens, constants, exc)
├── vie/                           <- Visual Impact Engine (package Python)
├── workspace/                     <- Scripts principales
│   ├── combine.py                 <-    ⭐ Resuelve manifiesto + secciones → JSON combinado
│   ├── build_design_system.py     <-    Generador: brand vars → divitheme.json + brand.css
│   ├── daw_build.py               <-    Orquestador unificado (pipeline completo)
│   ├── automation/                <-    generate_brief.py, ux_pro_brief_generator.py, etc.
│   ├── data/modules/              <-    Schemas de módulos Divi 5 (103, generados por PHP)
│   └── sections/catalog/          <-    Template catalog (877 referencias)
└── divi-agentic-core/
    ├── Plugin WordPress (Layout Engine, CLI, metadata)
    └── bin/
        ├── build_page.php         <- ⭐ Build + Deploy (único comando)
        ├── verify_page.php        <- Verificación post-deploy
        └── env_loader.php         <- Carga .env automáticamente
```

---

## 2. ⚡ Flujo Real de Generación de Páginas

### Pipeline Manual (el que realmente usamos)

```
Brand vars → Design System → Global Colors Sync → Page Definition → Combine → Deploy
```

```powershell
# 0. DAW_SITE en .env (OBLIGATORIO) — apunta al directorio en site/

# 1. (una vez) Junction link del plugin
Remove-Item -Recurse -Force "app/public/wp-content/plugins/divi-agentic-core"
New-Item -ItemType Junction -Path "app/public/wp-content/plugins/divi-agentic-core" `
  -Target (Resolve-Path "DAW_bundle\divi-agentic-core").Path

# 2. Brand + Design System
python DAW_bundle/workspace/build_design_system.py

# 3. (una vez por cambio de colores) Sincronizar Global Colors
.\wp.bat agentic global_colors sync `
  --design-system="DAW_bundle/site/<DAW_SITE>/design-system/divitheme.json"

# 4. Crear page-def (ver §4) en site/<DAW_SITE>/page-defs/<slug>.json
#    Las secciones van en site/<DAW_SITE>/page-defs/sections/<section>.json

# 5. Combinar manifiesto + secciones
python DAW_bundle/workspace/combine.py `
  DAW_bundle/site/<DAW_SITE>/page-defs/<slug>.json `
  --out DAW_bundle/site/<DAW_SITE>/page-defs/<slug>-combined.json

# 6. Deploy directo (Layout Engine refactorizado — renderers modulares)
.\wp.bat agentic deploy_page `
  --title="Título de la página" `
  --slug="<slug>" `
  --schema="DAW_bundle/site/<DAW_SITE>/page-defs/<slug>-combined.json" `
  --design-system="DAW_bundle/site/<DAW_SITE>/design-system/divitheme.json"
```

**Nota:** El Layout Engine (`class-layout-engine.php`) fue refactorizado a un dispatcher delgado con renderers modulares (`inc/core/renderers/*.php`). Esto elimina el monolito de 1515 líneas y permite agregar nuevos namespaces (como `dgpc/product-carousel`) sin tocar el núcleo.

### Pipeline con VIE (alternativa, para briefs automáticos)

```powershell
# 1. Brief
python DAW_bundle/workspace/automation/ux_pro_brief_generator.py `
  --query "descripción" --out site/<DAW_SITE>/briefs/<slug>.json

# 2. VIE → plan.json (mapeo semántico → bloques Divi)
python DAW_bundle/vie/cli.py `
  --brief-file=site/<DAW_SITE>/briefs/<slug>.json `
  --design-system=site/<DAW_SITE>/design-system/divitheme.json `
  --output=site/<DAW_SITE>/plans/<slug>.json

# 3. Deploy directo
.\wp.bat agentic deploy_page `
  --title="..." --slug="..." `
  --schema="DAW_bundle/site/<DAW_SITE>/plans/<slug>.json" `
  --design-system="DAW_bundle/site/<DAW_SITE>/design-system/divitheme.json"
```

---

## 3. Pipeline Diseño → Deploy (Capas)

```
Capa 0 — Module Schemas (PHP, genera una vez)
  php divi-agentic-core/bin/generate-module-schema.php --all
  → workspace/data/modules/<slug>.json (103 módulos con estructura autoritativa)

Capa 1 — Design System (build_design_system.py v4.0)
  site/<DAW_SITE>/brand/_design_vars.json + _design_presets.json
  → build_design_system.py (CIELCH, WCAG, 58 presets)
  → site/<DAW_SITE>/design-system/divitheme.json
  → site/<DAW_SITE>/brand/assets/css/brand.css  ← ⭐ ÚNICO source de CSS de marca

Capa 2 — Page Deploy (Layout Engine v12.1 — refactorizado)
  .\wp.bat agentic deploy_page --title="..." --slug="..." --schema="<combined.json>" --design-system="<divitheme.json>"
  deploy_page hace TODO:
    • Carga design system desde divitheme.json
    • Resuelve {{design:color:name}} → var(--gcid-*)
    • Resuelve {{design:font|radius|space:name}} → literales
    • Compila a Divi 5 blocks via Layout Engine refactorizado
      → Layout Engine dispatchea a renderers modulares (inc/core/renderers/*.php)
      → Convierte var(--gcid-*) → $variable() en post_content
      → Visual Builder reconoce colores globales
      → Namespaces externos (dgpc/*, dac/*) tienen su propio renderer

  ⚠️ build_page.php (monolito legacy) ya no se usa para deploy.
      No tiene schemas para módulos de terceros (dgpc, etc).
      Usar solo para resolución de tokens si el combined.json los contiene.
```

---

## 4. Page Definition — Cómo usar combine.py

### 4.1. Estructura

```
site/<DAW_SITE>/page-defs/
├── <slug>.json          ← Manifiesto (lista de secciones)
├── combine.py           ← [MOVIO a workspace/combine.py]
└── sections/
    ├── hero.json        ← Cada archivo = una sección Divi 5
    ├── services.json
    └── ...
```

### 4.2. Crear el manifiesto

El manifiesto solo define qué secciones incluir y en qué orden:

```json
{
  "_manifest": "v1",
  "title": "Título de la Página",
  "slug": "mi-pagina",
  "sections": [
    "sections/hero.json",
    "sections/services.json",
    "sections/cta-final.json"
  ]
}
```

Los paths de `sections/` son **relativos al directorio del manifiesto**.

### 4.3. Crear cada sección

Cada archivo en `sections/` contiene UNA sección de Divi 5:

```json
{
  "module_class": "daw-hero",
  "decoration": { ... },
  "advanced": { "css": { "className": "daw-hero" } },
  "css": ".daw-hero{min-height:100vh}...",
  "rows": [
    { "column_structure": "1_1", "columns": [...] }
  ]
}
```

- `"css"` (string) → CSS libre de la sección, se inyecta como `freeForm` en Divi 5
- `"rows"` → array de rows con sus columns y modules

### 4.4. Combinar

```powershell
python DAW_bundle/workspace/combine.py `
  DAW_bundle/site/<DAW_SITE>/page-defs/<slug>.json `
  --out DAW_bundle/site/<DAW_SITE>/page-defs/<slug>-combined.json
```

Esto resuelve los paths relativos del manifiesto, junta todas las secciones en un solo JSON, y lo escribe en `<slug>-combined.json`.

### 4.5. Desplegar

```powershell
.\wp.bat agentic deploy_page `
  --title="Título" --slug="<slug>" `
  --schema="DAW_bundle/site/<DAW_SITE>/page-defs/<slug>-combined.json" `
  --design-system="DAW_bundle/site/<DAW_SITE>/design-system/divitheme.json"
```

---

## 5. ⭐ Flujo de CSS de Marca (sin redundancia)

> Sección 4 explica cómo crear page-defs y usar combine.py.

### Cómo se sirve el CSS actualmente

| Qué | Origen | Mecanismo |
|-----|--------|-----------|
| Clases `daw-*` (blobs, badges, botones, etc.) | `site/<DAW_SITE>/brand/assets/css/brand.css` | Encolado como `daw-brand-css` via `wp_enqueue_style()` |
| Variables `--daw-*` | `divitheme.json` → `daw_generate_css_vars()` | Inline via `wp_add_inline_style('daw-design-tokens')` |
| Fonts Google | `divitheme.json` → detección dinámica de familias | Encolados como stylesheet externo |
| CSS de módulos personalizados | `modules/<slug>/style.css` | `Module_Registry` via `wp_register_style()` |
| Divi 5 nativo | Tema Divi | Motor de estilos propio del builder |

### Lo que YA NO se usa

| Mecanismo | Antes | Ahora |
|-----------|-------|-------|
| `wp_update_custom_css_post()` | Sincronizaba brand.css + tokens + module CSS a la BD | ❌ Eliminado — `sync_css` solo limpia legacy |
| `et_custom_css` (wp_options) | Legacy de Divi ePanel | ❌ Eliminado — `sync_css` lo borra |
| `custom_css` CPT | Almacenaba el CSS combinado | ❌ Vaciado — el CSS se sirve desde disco |
| `sync_css` en `build_page.php` | Se ejecutaba post-deploy | ❌ Eliminado |

### ¿Qué hace `sync_css` ahora?

`wp agentic sync_css` ya no escribe nada. Solo **verifica** que los archivos existan y **limpia** datos legacy:

```powershell
.\wp.bat agentic sync_css
# → brand.css (8244 chars) found at: site/<DAW_SITE>/brand/assets/css/brand.css
# → Design system found: site/<DAW_SITE>/design-system/divitheme.json
# → Cleaned up et_custom_css legacy option.
# → Cleared WordPress Custom CSS post content.
# → Success: CSS flow synchronized: file-based enqueue is active.
```

Se ejecuta **una vez** al migrar al nuevo flujo. No es necesario en el día a día.

Cada directorio en `site/` tiene su propio `brand.css`. El plugin lee `DAW_SITE` del `.env` para saber cuál encolar.

---

## 6. Cómo Crear una Nueva Marca

```powershell
# 1. Editar .env en la raíz del proyecto
#    DAW_SITE=nombre-de-tu-marca

# 2. Generar brand files
#    Opción A: Brand Generator (automático)
python DAW_bundle/workspace/brand_generator.py `
  --site <nombre> --name "<Brand>" --accent "<#hex>" --tone luxury

#    Opción B: Copiar template + editar manual
Copy-Item -Recurse DAW_bundle/site/example DAW_bundle/site/<nombre>

# 3. Generar design system + brand.css
#    El brand.css se escribe a site/<nombre>/brand/assets/css/brand.css
python DAW_bundle/workspace/build_design_system.py

# 4. Sincronizar colores globales
.\wp.bat agentic global_colors sync `
  --design-system="DAW_bundle/site/<DAW_SITE>/design-system/divitheme.json"

# 5. Crear page-def y secciones
#    site/<DAW_SITE>/page-defs/<slug>.json (manifiesto)
#    site/<DAW_SITE>/page-defs/sections/<section>.json (secciones)

# 6. Combinar y desplegar
python DAW_bundle/workspace/combine.py `
  DAW_bundle/site/<DAW_SITE>/page-defs/<slug>.json `
  --out DAW_bundle/site/<DAW_SITE>/page-defs/<slug>-combined.json
.\wp.bat agentic deploy_page `
  --title="Título de la página" `
  --slug="<slug>" `
  --schema="DAW_bundle/site/<DAW_SITE>/page-defs/<slug>-combined.json" `
  --design-system="DAW_bundle/site/<DAW_SITE>/design-system/divitheme.json"
```

---

## 7. Prerrequisito: Global Colors (gcid)

Antes del primer deploy, sincronizar colores:

| Acción | Comando |
|--------|---------|
| Sincronizar | `.\wp.bat agentic global_colors sync --design-system="DAW_bundle/site/<DAW_SITE>/design-system/divitheme.json"` |
| Verificar estado | `.\wp.bat agentic global_colors status --design-system="..."` |
| Listar activos | `.\wp.bat agentic global_colors list` |

Si no hay gcids sincronizados, `deploy_page` emite warning y resuelve a hex.

---

## 8. Reglas DAW

1. No editar `divitheme.json` a mano — regenerar con `build_design_system.py`.
2. No usar `divi/code` como comodín — consultar `blocks-dictionary.md` primero.
3. No usar `et_pb_*` (shortcodes Divi 4) — solo namespace `divi/*`.
4. Colores siempre como `{{design:color:*}}`, nunca hex hardcodeados en schemas.
5. **Deploy directo.** Usar `wp agentic deploy_page`, no `build_page.php`. El combined.json puede tener tokens `{{design:*}}` que `deploy_page` resuelve automáticamente.
6. **Sin CSS en BD.** El CSS de marca vive en disco y se encola como stylesheet nativo. `sync_css` no escribe — solo limpia legacy.
7. **brand.css por marca.** `build_design_system.py` escribe a `site/<DAW_SITE>/brand/assets/css/brand.css`.
8. **Frontera site/:** Todo dato de proyecto va en `site/<DAW_SITE>/`. El framework no contiene datos de proyecto.
9. **Pipeline de página:** `page-defs/<slug>.json` (manifiesto) → `workspace/combine.py` → `wp agentic deploy_page` → página en WP.
10. **Layout Engine refactorizado:** Renderers modulares en `inc/core/renderers/`. Para agregar un nuevo namespace (ej. `dgpc/*`, `dac/*`), crear su renderer y registrarlo en el dispatcher de `class-layout-engine.php`.
11. **VIE (Visual Impact Engine):** Alternativa automática: `brief → vie/cli.py → plans/ → deploy_page`.
12. **DIE (ML):** Archivado en `_archive/die_pipeline/`. No usar para páginas nuevas.
13. Cada directorio en `site/` tiene su propio `brand/assets/css/brand.css`. `DAW_SITE` en `.env` define cuál usar.
14. **Sin fallbacks silenciosos:** Si `DAW_SITE` no está definido, el pipeline falla inmediatamente.
15. **CSS de sección autocontenido:** Cada sección lleva su propio CSS inline (freeForm en el atributo `css` del JSON de sección). CSS global de página va en el Custom CSS de la página vía WordPress.

---

## 9. Arquitectura en Capas

```
┌──────────────────────────────────────────────────────────────┐
│ CAPA 3 — CLI / Orquestador                                   │
│   workspace/build_design_system.py                           │
│   workspace/automation/{ux_pro,m}_brief_generator.py         │
│   wp agentic deploy_page (vía WP-CLI)                        │
├──────────────────────────────────────────────────────────────┤
│ CAPA 2 — Aplicación / Layout Engine                          │
│   divi-agentic-core/inc/core/class-layout-engine.php         │
│     → Dispatcher delgado con renderers modulares             │
│   divi-agentic-core/inc/core/renderers/*.php                 │
│     → 13 renderers (structural, text, button, media,         │
│       form, content, container, dynamic, woo, generic,       │
│       dgpc, dac, base + trait helpers)                       │
│   vie/                — Visual Impact Engine (13 módulos)    │
│   └── vie/handlers/   — SectionHandler registry (OCP)        │
│   └── vie/strategies/ — StrategyProfile                      │
├──────────────────────────────────────────────────────────────┤
│ CAPA 1 — Shared Kernel                                       │
│   daw/cfg.py, types.py, tokens.py, constants.py, exc.py     │
└──────────────────────────────────────────────────────────────┘
```

---

## 10. Referencias

| Recurso | Path | Propósito |
|---------|------|-----------|
| SKILL.md (4 fases) | `daw-skill/SKILL.md` | Orquestación completa análisis → diseño → mapeo → CLI |
| Diccionario de bloques | `daw-skill/references/blocks-dictionary.md` | Guía de 102 módulos Divi 5 |
| Lógica del Ingeniero | `daw-skill/references/engineer.md` | Comandos CLI, deploy, verificación |
| Lógica del Diseñador | `daw-skill/references/designer.md` | Mapeo semántico → bloques, tokens, presets |
| Layout Engine | `divi-agentic-core/inc/core/class-layout-engine.php` | Dispatcher con renderers modulares |
| Renderers | `divi-agentic-core/inc/core/renderers/*.php` | 13 renderers (structural, text, button, media, form, content, container, dynamic, woo, generic, dgpc, dac) |
| Refactor Plan | `divi-agentic-core/inc/core/REFACTOR-PLAN.md` | Plan de migración del monolito a renderers |
| Shared Kernel | `daw/` | Capa 1 — sin side effects al importar |
| VIE package | `vie/` | Visual Impact Engine |
| Inputs/Outputs del DS | `references/design-system-inputs.md` | Formatos de `_design_vars.json`, `_design_presets.json`, `_effects.css`, brief JSON, CLI de generadores |
