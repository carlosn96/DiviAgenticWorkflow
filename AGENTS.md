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
├── site/                          <- ⭐ DATOS DE PROYECTO (separados del framework)
│   ├── <DAW_SITE>/                <-    Marca apuntada por .env DAW_SITE
│   │   ├── brand/                 <-       _design_vars.json (único input de marca)
│   │   ├── page-defs/             <-       Definiciones de página
│   │   │   ├── <slug>.json        <-          Manifiesto: lista de secciones
│   │   │   └── sections/          <-          Archivos de sección individuales
│   │   ├── plans/                 <-       plan.json generado por VIE
│   │   ├── design-system/         <-       divitheme.json (gcids, presets)
│   │   ├── briefs/                <-       Briefs de diseño
│   │   └── content_state/         <-       Estado entre fases
│   └── example/                   <-    Template para nuevas marcas
├── _archive/                      <- Código y marcas archivadas
├── daw-skill/SKILL.md             <- ⭐ Orquestación de 4 fases
├── daw/                           <- Shared kernel (cfg, types, tokens)
├── vie/                           <- Visual Impact Engine
├── workspace/                     <- Scripts principales
│   ├── combine.py                 <-    Resuelve manifiesto + secciones → JSON combinado
│   └── automation/                <-    generate_brief.py, etc.
└── divi-agentic-core/
    ├── Plugin WordPress (Layout Engine, CLI, metadata)
    └── bin/
        ├── brand-sync.php         <- ⭐ Brand vars → wp_options['et_divi'] (Customizer)
        ├── build_page.php         <- Legacy (no usar)
        └── verify_page.php        <- Verificación post-deploy
```

---

## 2. ⚡ Flujo Real

```
Brand vars (_design_vars.json)
  → brand-sync.php
    → wp_options['et_divi'] (Customizer global)
    → divitheme.json (tokens + presets)
    → gcids via GlobalData::set_global_colors()
  → page-defs/<slug>.json (manifiesto) + sections/*.json
  → python workspace/combine.py → <slug>-combined.json
  → wp agentic deploy_page → post_content en WP
```

### 2.1 Brand Sync (único comando)

```powershell
wp eval-file bin/brand-sync.php
```

Lee `_design_vars.json` y sincroniza **todo** el ecosistema Divi:

| Destino | Qué escribe | Impacto |
|---------|-------------|---------|
| `wp_options['et_divi']` | 38+ opciones de color + 5 fuentes + logo + font sizes/weights | Tema global (header, footer, menú, tipografía) |
| Global Colors (gcids) | Todos los colores via `GlobalData::set_global_colors()` | gcids vivos en páginas existentes y futuras |
| Global Variables (gvids) | Radios, espacios y fuentes via `GlobalData::set_global_variables()` | Variables nativas Divi 5 editables desde VB |
| `divitheme.json` | Solo presets + strategy | Design_Resolver los usa para merge estructural en deploy |

Divi regenera CSS automáticamente. Un solo comando, todo sincronizado.

### 2.2 Page Deploy

```powershell
# 1. Combinar manifiesto + secciones
python DAW_bundle/workspace/combine.py `
  DAW_bundle/site/<DAW_SITE>/page-defs/<slug>.json `
  --out DAW_bundle/site/<DAW_SITE>/page-defs/<slug>-combined.json

# 2. Deploy
.\wp.bat agentic deploy_page `
  --title="Título" --slug="<slug>" `
  --schema="DAW_bundle/site/<DAW_SITE>/page-defs/<slug>-combined.json" `
  --design-system="DAW_bundle/site/<DAW_SITE>/design-system/divitheme.json"
```

---

## 3. Pipeline Diseño → Deploy (Capas)

```
Capa 0 — Brand Vars
  site/<DAW_SITE>/brand/_design_vars.json
  → Define colores, fuentes, radios, espacios, logo, customizer mapping

Capa 1 — Brand Sync (todo en uno)
  wp eval-file bin/brand-sync.php
  → 1. Escribe et_divi (Customizer global — header, footer, menú, tipografía, font sizes)
  → 2. Registra gcids via GlobalData::set_global_colors() (colores vivos en VB)
  → 3. Registra gvids via GlobalData::set_global_variables() (radios, espacios, fuentes como variables nativas Divi 5)
  → 4. Actualiza divitheme.json (solo presets + metadata)
  → 5. Flush caché CSS de Divi

Capa 2 — Page Deploy
  wp agentic deploy_page
  → Compila combined.json a Divi 5 blocks
  → Resuelve {{design:color:*}} → var(--gcid-*)
  → Layout Engine con renderers modulares (inc/core/renderers/*.php)
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

Cada archivo en `sections/` contiene UNA sección de Divi 5. Sigue esta estructura:

```json
{
  "module_class": "daw-hero",
  "decoration": {
    "background": { "video": { "mp4": "..." } },
    "spacing": {
      "desktop": { "value": { "padding": { "top": "96px", ... } } },
      "tablet": { "value": { "padding": { ... } } },
      "phone": { "value": { "padding": { ... } } }
    },
    "sizing": {
      "desktop": { "value": { "innerWidth": "900px", "minHeight": "100vh" } }
    },
    "animation": { "style": "fade", "duration": "800ms", "easing": "easeOutExpo" }
  },
  "advanced": {
    "css": { "className": "daw-hero" },
    "htmlAttributes": {
      "desktop": { "value": { "class": "daw-hero", "id": "mi-seccion" } }
    }
  },
  "css": "",    ← LO LLENA combine.py DESDE sections/css/<module>.css
  "rows": [
    {
      "column_structure": "1_1",
      "decoration": {
        "sizing": { "gutter": "0%" },
        "spacing": { "padding": { "top": "0px", ... }, "margin": { "top": "0px", ... } },
        "layout": { "flexWrap": "wrap" }
      },
      "columns": [
        {
          "type": "1_1",
          "decoration": {
            "sizing": {
              "desktop": { "value": { "flexType": "24_24" } },
              "tablet": { "value": { "flexType": "24_24" } },
              "phone": { "value": { "flexType": "24_24" } }
            }
          },
          "advanced": {
            "type": {
              "desktop": { "value": "1_1" },
              "tablet": { "value": "1_1" },
              "phone": { "value": "vertical" }
            }
          },
          "modules": [
            {
              "type": "divi/text",
              "decoration": { "animation": { ... }, "spacing": { ... } },
              "advanced": {
                "text": { "text": { "desktop": { "value": { "color": "light", "textAlign": "center" } } } },
                "alignment": { "desktop": { "value": "center" } },
                "css": { "className": "daw-hero-title" },
                "htmlAttributes": { "desktop": { "value": { "class": "daw-hero-title" } } }
              },
              "module_class": "daw-hero-title",
              "content": "<h1>Título</h1>",
              "bodyFont": {
                "p": {
                  "font": {
                    "desktop": { "value": { "fontFamily": "var(--font-ui)", "size": "16px" } }
                  }
                }
              }
            }
          ]
        }
      ]
    }
  ],
  "_section": true
}
```

**Reglas para crear secciones Divi 5 nativas:**

1. Clase CSS: `advanced.css.className` + `advanced.htmlAttributes.desktop.value.class` + `module_class` — los 3 iguales.
2. ID de sección: `advanced.htmlAttributes.desktop.value.id` + `module_id` — ambos iguales.
3. Animaciones: Usar `decoration.animation` (fade, slide) con `style`, `duration`, `delay`, `easing`. NO CSS keyframes manuales.
4. Responsive: `decoration.spacing`, `decoration.sizing` con 3 breakpoints (desktop, tablet, phone). Divi 5 requiere `{ "desktop": { "value": { ... } } }`.
5. Columnas: `column_structure` en row (ej. `"1_2,1_2"`) + `type` + `flexType` en column. Phone usa `"vertical"`.
6. Contenido: `content` string con HTML plano. NO markdown.
7. Tipografía: `bodyFont.p.font.desktop.value` con `fontFamily`, `size`, `weight`, `color`, etc. NO CSS manual.
8. **CSS freeForm** (campo `"css"`): Solo para lo que no tiene atributo nativo. Y **sin `<` en ninguna parte** (ver §4.6).
9. Botones: `type: "divi/button"` con `decoration.button.desktop.value.backgroundColor`, `textColor`, etc. + `button_text`, `button_url`.
10. El CSS de sección se almacena en `sections/css/<module>.css` y lo inyecta `combine.py`. El campo `"css"` en el JSON se deja vacío (`""`).

### 4.6. ⚠️ Pipeline del freeForm CSS — peligro de `<`

Divi 5 procesa el CSS de sección (freeForm) así:

```
section["css"] (en JSON)
  → Layout Engine → attrs.css.desktop.value.freeForm (en post_content)
  → CssStyleUtils::get_statements() (CssStyleUtils.php:381):
    wp_strip_all_tags($modified_css_declaration)
  → Renderizado en <style id="et-builder-module-design-...-cached-inline-styles">
```

**Problema**: `wp_strip_all_tags()` aplica PHP `strip_tags` al CSS. CUALQUIER `<` en el CSS (incluso en comentarios) activa la limpieza. Si no hay un `>` de cierre, `strip_tags` elimina todo el resto del string.

**Ejemplo real**: `/* Mobile (<1024px) */`
- `strip_tags` ve `<1024px)` como etiqueta HTML y trunca desde ese punto
- 14,438 chars → 3,329 chars (pérdida de 11K chars de estilos)
- Selectores después del `<` en el archivo desaparecen del frontend

**Regla**: NINGÚN `<` en el CSS de sección. Ni siquiera en comentarios.

**Dónde almacenar CSS de sección**:
```
sections/css/
├── hero.css       ← combine.py lo lee y lo inyecta en section["css"]
└── ...
```

**❌ NO inline `<style>` en module content**: Inyectar CSS como `<style>` tag dentro del `content` de un módulo se pierde si el usuario edita via Visual Builder y guarda. Usar exclusivamente `section["css"]` (freeForm nativo). Excepción: módulos `divi/code` específicos para CSS global que no se editan por VB.

### Sanitización de `@import` — el segundo trap

Además de `wp_strip_all_tags` en rendering, Divi tiene **otra sanitización en el guardado VB**: `sanitize_css()` en `SavingUtility.php:1423-1482` **siempre elimina `@import`** (línea 1444-1448). Esto aplica a `_et_pb_custom_css` (page-level CSS), no a freeForm de bloques.

**Solución estándar**: separar `@import` del CSS de página:
- `@import` → **WordPress Additional CSS** (`wp_update_custom_css_post()`)
  - Divi no sanitiza esto (es core de WordPress)
  - Usar delimitadores (`/* === DAW External Imports === */`) para evitar duplicación
- CSS puro → `_et_pb_custom_css` (post meta)
  - Sin `@import` → `sanitize_css()` no toca nada → sobrevive VB save

**Ejemplo de separación de `@import`:**
```php
// Extraer @import con regex correcta
preg_match_all('/@import\s+url\([^)]+\)\s*;/', $css, $matches);
$imports = implode("\n", $matches[0]);
$page_css = preg_replace('/@import\s+url\([^)]+\)\s*;\s*/', '', $css);

// @import → WordPress Additional CSS
$existing = wp_get_custom_css();
$existing = preg_replace('/DAW External Imports.*?\/DAW External Imports/s', '', $existing);
wp_update_custom_css_post($imports_block . $existing);

// Resto → _et_pb_custom_css
update_post_meta($page_id, '_et_pb_custom_css', wp_slash($page_css));
```

### 4.4. Combinar

```powershell
python DAW_bundle/workspace/combine.py `
  DAW_bundle/site/<DAW_SITE>/page-defs/<slug>.json `
  --out DAW_bundle/site/<DAW_SITE>/page-defs/<slug>-combined.json
```

Esto resuelve los paths relativos del manifiesto, junta todas las secciones en un solo JSON, y lo escribe en `<slug>-combined.json`. Si existe `sections/css/<section-name>.css`, `combine.py` lo inyecta automáticamente en el campo `"css"` de la sección (freeForm nativo Divi 5).

### 4.5. Desplegar

```powershell
.\wp.bat agentic deploy_page `
  --title="Título" --slug="<slug>" `
  --schema="DAW_bundle/site/<DAW_SITE>/page-defs/<slug>-combined.json" `
  --design-system="DAW_bundle/site/<DAW_SITE>/design-system/divitheme.json"
```

---

## 5. ⭐ Brand → Divi Customizer (Pipeline Actual)

El brand ya no genera CSS propio. Divi renderiza todo desde sus opciones nativas de Customizer.

El comando `brand-sync.php` ahora lo hace **todo**: Customizer + gcids + gvids + divitheme.json.

Los tokens (color, font, radius, space) ya no están en `divitheme.json`. `Design_Resolver` v2.0 los lee directamente de stores nativos Divi 5:
- `GlobalData::get_global_colors()` → `{{design:color:*}}`
- `GlobalData::get_global_variables()` → `{{design:radius:space:font:*}}`

`divitheme.json` queda solo con presets + strategy.

### Lo que ya NO existe ni se necesita
- ❌ `build_design_system.py` — integrado en brand-sync
- ❌ `global_colors sync` como paso aparte — brand-sync lo hace inline
- ❌ `brand/assets/css/brand.css` — no se genera
- ❌ `daw-brand-css` enqueue — no se encola
- ❌ `sync_css` — no existe
- ❌ Tokens en `divitheme.json` — se leen desde stores nativos Divi 5

---

## 6. Cómo Crear una Nueva Marca

```powershell
# 1. Editar .env — DAW_SITE=nombre-de-tu-marca

# 2. Editar site/<DAW_SITE>/brand/_design_vars.json con colores, fuentes, logo, radios, espacios

# 3. Sincronizar TODO (Customizer + divitheme.json + gcids)
.\wp eval-file DAW_bundle/divi-agentic-core/bin/brand-sync.php

# 4. Crear page-defs + sections (ver §4)

# 5. Combinar y desplegar
python DAW_bundle/workspace/combine.py `
  DAW_bundle/site/<DAW_SITE>/page-defs/<slug>.json `
  --out DAW_bundle/site/<DAW_SITE>/page-defs/<slug>-combined.json
.\wp.bat agentic deploy_page `
  --title="Título" --slug="<slug>" `
  --schema="DAW_bundle/site/<DAW_SITE>/page-defs/<slug>-combined.json" `
  --design-system="DAW_bundle/site/<DAW_SITE>/design-system/divitheme.json"
```

---

## 7. Global Colors (gcids)

Los gcids se sincronizan automáticamente al ejecutar `brand-sync.php`. No es necesario un paso aparte.

Para verificar estado:

| Acción | Comando |
|--------|---------|
| Verificar | `.\wp.bat agentic global_colors status --design-system="DAW_bundle/site/<DAW_SITE>/design-system/divitheme.json"` |
| Listar | `.\wp.bat agentic global_colors list` |

Si no hay gcids sincronizados, `deploy_page` emite warning y resuelve a hex.

---

## 8. Reglas DAW

1. No editar `divitheme.json` a mano — se genera desde `_design_vars.json`. Editar `_design_vars.json` y re-sincronizar.
2. No usar `divi/code` como comodín — consultar `blocks-dictionary.md` primero.
3. No usar `et_pb_*` (shortcodes Divi 4) — solo namespace `divi/*`.
4. Colores siempre como `{{design:color:*}}`, nunca hex hardcodeados en schemas.
5. **Deploy directo.** Usar `wp agentic deploy_page`, no `build_page.php`.
6. **CSS vía Divi Customizer.** El brand se sincroniza a `et_divi` opciones; Divi genera el CSS automáticamente. No hay CSS propio de marca.
7. **Brand sync único.** `brand-sync.php` lee `_design_vars.json` y escribe a `wp_options['et_divi']`. No hay otro paso.
8. **Frontera site/:** Todo dato de proyecto va en `site/<DAW_SITE>/`. El framework no contiene datos de proyecto.
9. **Pipeline de página:** `page-defs/<slug>.json` (manifiesto) → `workspace/combine.py` → `wp agentic deploy_page` → página en WP.
10. **Layout Engine refactorizado:** Renderers modulares en `inc/core/renderers/`.
11. **VIE (Visual Impact Engine):** Alternativa automática: `brief → vie/cli.py → plans/ → deploy_page`.
12. **DIE (ML):** Archivado en `_archive/die_pipeline/`. No usar para páginas nuevas.
13. **Sin fallbacks silenciosos:** Si `DAW_SITE` no está definido, el pipeline falla inmediatamente.
14. **CSS de sección autocontenido:** Cada sección lleva su propio CSS inline (freeForm en el atributo `css`). CSS global de página va en el Custom CSS de la página vía WordPress.
15. **⚠️ Sin `<` en freeForm CSS:** `wp_strip_all_tags()` trunca el CSS al encontrar `<`. Almacenar CSS en `sections/css/<module>.css` (lo inyecta `combine.py`).

---

## 9. Arquitectura en Capas

```
┌──────────────────────────────────────────────────────────────┐
│ CAPA 3 — CLI / Orquestador                                   │
│   divi-agentic-core/bin/brand-sync.php                       │
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
│ CAPA 1 — Brand Vars → Divi Customizer                        │
│   site/<DAW_SITE>/brand/_design_vars.json                    │
│   divi-agentic-core/bin/brand-sync.php                       │
│     → Mapea 38 opciones de color + fuentes a et_divi        │
│     → Divi genera CSS automáticamente                        │
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
