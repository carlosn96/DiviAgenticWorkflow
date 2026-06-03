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
│   │   │   ├── combine.py         <-          Resuelve manifiesto + secciones → JSON combinado
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
Brand vars → Design System → Global Colors Sync → Page Definition → Combine → Build + Deploy
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
python DAW_bundle/site/<DAW_SITE>/page-defs/combine.py `
  DAW_bundle/site/<DAW_SITE>/page-defs/home.json `
  --out DAW_bundle/site/<DAW_SITE>/page-defs/home-combined.json

# 6. Build + Deploy (un solo comando)
.\php.bat DAW_bundle/divi-agentic-core/bin/build_page.php `
  --def="home-combined.json" --deploy
#      ^^ el path es relativo a site/<DAW_SITE>/page-defs/
```

**Nota:** `build_page.php` ya no ejecuta `sync_css` post-deploy. El CSS de marca se sirve desde disco vía enqueue del plugin.

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

# 3. Build + Deploy
.\php.bat DAW_bundle/divi-agentic-core/bin/build_page.php `
  --def=site/<DAW_SITE>/plans/<slug>.json --deploy
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

Capa 2 — Page Schema (build_page.php — ÚNICO COMANDO)
  .\php.bat DAW_bundle/divi-agentic-core/bin/build_page.php --def=<path> --deploy
  build_page.php hace TODO:
    • Lee el page-def (JSON de entrada)
    • Carga estructura de módulo desde schema PHP
    • Carga design system desde divitheme.json
    • Resuelve {{design:color:name}} → var(--gcid-*)
    • Resuelve {{design:font|radius|space:name}} → literales
    • Expande presets inline via deep_merge()
    • Normaliza gradient stops
    • Valida estructura (sections → rows → columns → modules)
    • Ejecuta wp agentic deploy_page
      → Layout Engine convierte var(--gcid-*) → $variable() en post_content
      → Visual Builder reconoce colores globales
```

---

## 4. ⭐ Flujo de CSS de Marca (sin redundancia)

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

## 5. Cómo Crear una Nueva Marca

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
python DAW_bundle/site/<DAW_SITE>/page-defs/combine.py `
  DAW_bundle/site/<DAW_SITE>/page-defs/<slug>.json `
  --out DAW_bundle/site/<DAW_SITE>/page-defs/<slug>-combined.json
.\php.bat DAW_bundle/divi-agentic-core/bin/build_page.php `
  --def="<slug>-combined.json" --deploy
```

---

## 6. Prerrequisito: Global Colors (gcid)

Antes del primer deploy, sincronizar colores:

| Acción | Comando |
|--------|---------|
| Sincronizar | `.\wp.bat agentic global_colors sync --design-system="DAW_bundle/site/<DAW_SITE>/design-system/divitheme.json"` |
| Verificar estado | `.\wp.bat agentic global_colors status --design-system="..."` |
| Listar activos | `.\wp.bat agentic global_colors list` |

Si no hay gcids sincronizados, `deploy_page` emite warning y resuelve a hex.

---

## 7. Reglas DAW

1. No editar `divitheme.json` a mano — regenerar con `build_design_system.py`.
2. No usar `divi/code` como comodín — consultar `blocks-dictionary.md` primero.
3. No usar `et_pb_*` (shortcodes Divi 4) — solo namespace `divi/*`.
4. Colores siempre como `{{design:color:*}}`, nunca hex hardcodeados en schemas.
5. `build_page.php` con resolved=true (default) expande presets inline y resuelve tokens.
6. **Sin CSS en BD.** El CSS de marca vive en disco y se encola como stylesheet nativo. `sync_css` no escribe — solo limpia legacy.
7. **brand.css por marca.** `build_design_system.py` escribe a `site/<DAW_SITE>/brand/assets/css/brand.css`.
8. **Frontera site/:** Todo dato de proyecto va en `site/<DAW_SITE>/`. El framework no contiene datos de proyecto.
9. **Pipeline de página:** `page-defs/<slug>.json` (manifiesto) → `combine.py` → `build_page.php --deploy` → página en WP.
10. **VIE (Visual Impact Engine):** Alternativa automática: `brief → vie/cli.py → plans/ → build_page.php`.
11. **DIE (ML):** Archivado en `_archive/die_pipeline/`. No usar para páginas nuevas.
12. Cada directorio en `site/` tiene su propio `brand/assets/css/brand.css`. `DAW_SITE` en `.env` define cuál usar.
13. **Sin fallbacks silenciosos:** Si `DAW_SITE` no está definido, el pipeline falla inmediatamente.

---

## 8. Arquitectura en Capas

```
┌──────────────────────────────────────────────────────────────┐
│ CAPA 3 — CLI / Orquestador                                   │
│   workspace/build_design_system.py                           │
│   workspace/automation/{ux_pro,m}_brief_generator.py         │
│   divi-agentic-core/bin/build_page.php (PHP)                 │
├──────────────────────────────────────────────────────────────┤
│ CAPA 2 — Aplicación                                          │
│   vie/                — Visual Impact Engine (13 módulos)    │
│   └── vie/handlers/   — SectionHandler registry (OCP)        │
│   └── vie/strategies/ — StrategyProfile                      │
├──────────────────────────────────────────────────────────────┤
│ CAPA 1 — Shared Kernel                                       │
│   daw/cfg.py, types.py, tokens.py, constants.py, exc.py     │
└──────────────────────────────────────────────────────────────┘
```

---

## 9. Referencias

| Recurso | Path | Propósito |
|---------|------|-----------|
| SKILL.md (4 fases) | `daw-skill/SKILL.md` | Orquestación completa análisis → diseño → mapeo → CLI |
| Diccionario de bloques | `daw-skill/references/blocks-dictionary.md` | Guía de 102 módulos Divi 5 |
| Lógica del Ingeniero | `daw-skill/references/engineer.md` | Comandos CLI, deploy, verificación |
| Lógica del Diseñador | `daw-skill/references/designer.md` | Mapeo semántico → bloques, tokens, presets |
| Shared Kernel | `daw/` | Capa 1 — sin side effects al importar |
| VIE package | `vie/` | Visual Impact Engine |
| Inputs/Outputs del DS | `references/design-system-inputs.md` | Formatos de `_design_vars.json`, `_design_presets.json`, `_effects.css`, brief JSON, CLI de generadores |
