# DAW — Divi Agentic Workflow

Pipeline completo de diseño → deploy para Divi 5.9.0. Este documento describe el flujo real, no el idealizado.

Todos los paths del documento son relativos al directorio DAW (`<daw-root>/`) salvo que se indique. Los comandos se ejecutan desde ese mismo directorio.

El proyecto tiene dos raíces:
- **`$WpRoot`** — raíz de WordPress (contiene `wp.bat`, `wp-content/`, etc.)
- **`$DawRoot`** — directorio del framework DAW (contiene este `AGENTS.md`, `site/`, `workspace/`, etc.)

`$DawRoot` siempre está dentro de `$WpRoot`. Los scripts en `workspace/` resuelven ambas automáticamente.

### 0.1. Prerrequisito: wrapper `wp`

Debe existir un wrapper `wp` en `$WpRoot` que invoque WP-CLI. Los scripts en `workspace/` lo buscan como `wp.bat` (Windows) o `wp` (Unix) allí.

El wrapper debe ser un **passthrough directo** — sin lógica de detección ni validación en runtime. La validación se hace al CREAR el wrapper para tu entorno, no en cada ejecución.

Elige el que corresponda a tu entorno:

| Entorno | Contenido del wrapper |
|---------|----------------------|
| **WP-CLI global** (PATH) | `@ECHO OFF & wp %*` (Win) / `#!/bin/bash && exec wp "$@"` (Unix) |
| **phar local** (raíz del proyecto) | `@ECHO OFF & php "%~dp0wp-cli.phar" %*` (Win) / `#!/bin/bash && php "$(dirname "$0")/wp-cli.phar" "$@"` (Unix) |
| **Local by Flywheel** | `@ECHO OFF & "C:\Users\<user>\AppData\Local\Local\resources\extra-resources\php\php.exe" "%~dp0wp-cli.phar" %*` (ajustar ruta) |
| **XAMPP** | `@ECHO OFF & "C:\xampp\php\php.exe" "%~dp0wp-cli.phar" %*` (ajustar ruta) |

La raíz del proyecto es donde está este wrapper. Los scripts en `workspace/` solo apuntan a él.

---

## 1. Mapa del DAW

```
<wp-root>/                         ← $WpRoot (WordPress root)
├── wp.bat                         <- ⭐ Wrapper que invoca WP-CLI (ver §0.1)
├── wp-cli.phar                    <- WP-CLI binary (opcional si hay global)
├── wp-content/                    <- WordPress content
│   └── et-cache/                  <- Cache estática de Divi (flusheable)
│
└── <daw-root>/                    ← $DawRoot (DAW framework)
    ├── AGENTS.md                  <- Este archivo (fuente de verdad del pipeline)
    ├── README.md / RUNBOOK.md     <- Quickstart y runbook
    ├── .env.example               <- Template .env (DAW_SITE, WP_PATH, WP_URL)
    ├── .gitignore
    ├── site/                      <- ⭐ DATOS DE PROYECTO (separados del framework)
    │   ├── <DAW_SITE>/            <-    Marca apuntada por .env DAW_SITE
    │   │   ├── brand/             <-       _design_vars.json (único input de marca)
    │   │   ├── components/        <-       Componentes modulares (modules/, sections/)
    │   │   ├── page-defs/         <-       Definiciones de página (ver §4)
    │   │   │   ├── inicio/        <-          Página: inicio
    │   │   │   ├── header/        <-          Componente: header
    │   │   │   ├── footer/        <-          Componente: footer
    │   │   │   └── ...            <-          Más páginas/componentes
    │   │   ├── design-system/     <-       divitheme.json (presets + strategy)
    │   │   ├── content_state/     <-       Estado entre fases
    │   │   └── references/        <-       Referencias de diseño (HTML, briefs)
    │   └── example/               <-    Template para nuevas marcas (mantenida por check-example.php)
    ├── _archive/                  <- Código y marcas archivadas (VIE, DIE, legacy-catalog…)
    ├── daw-skill/                 <- Orquestación de 4 fases
    │   └── references/            <-    architect, design-lead, designer, engineer, knowledge, blocks-dictionary
    ├── _archive/daw/              <- Shared kernel Python (archivado — sin consumidores activos)
    ├── references/                <- design-system-inputs.md, skill-selection.md
    ├── workspace/                 <- Scripts transversales (no dependientes de site)
    │   ├── combine.py             <-    Resuelve manifiesto + secciones → JSON combinado
    │   ├── deploy.ps1             <-    Wrapper: combine + deploy_page + flush (páginas)
    │   ├── deploy-template.ps1    <-    Wrapper: combina + deploy_global_ecosystem + flush
    │   └── automation/            <-    extract_page.php, manage_content.php (genéricos)
    └── divi-agentic-core/         <- ⭐ Plugin WordPress (Layout Engine, CLI, metadata)
        ├── divi-agentic-core.php   <-    Boot del plugin (carga Loader + Module_Registry)
        ├── inc/
        │   ├── loader.php          <-    Autoloader PSR-4 (DAC\ + renderers)
        │   ├── cli/                <-    class-brand-command.php, class-agentic-command.php
        │   └── core/               <-    Layout Engine, renderers/, skills/, intelligence/
        ├── modules/               <-    Módulos Divi 5 custom (module.json + render.php + view.js)
        ├── data/                  <-    Metadata de módulos Divi (_all_modules_metadata.php, etc.)
        └── bin/
            ├── brand.php          <- Legacy (usar wp brand)
            ├── brand-sync.php     <- Legacy (usar wp brand sync)
            ├── brand-reset.php    <- Legacy (usar wp brand reset)
            ├── verify_page.php    <- Verificación post-deploy
            ├── lint_page_def.php  <- Valida la estructura del page-def
            └── ...                <- Utilidades (generate-module-schema, extract-module-meta, check-example, update-css…)
```

---

## 2. ⚡ Flujo Real

```
Brand vars (_design_vars.json)
  → [opcional] wp brand validate --skill=X   ← 54+ checks de calidad
  → [opcional] wp brand approve [--skill=X]  ← persiste aprobación con vars_hash
  → wp brand sync [--force]                  ← bloquea si no hay approve o si vars cambiaron
    → wp_options['et_divi'] (Customizer global)
    → divitheme.json (tokens + presets)
    → gcids via GlobalData::set_global_colors()
  → site/<DAW_SITE>/page-defs/<slug>/manifest.json + sections/*.json
  → python workspace/combine.py → <slug>-combined.json  (ver §4.4)
  → workspace\deploy.ps1 → página en WP con Divi 5 blocks  (ver §4.5)
  → (ó workspace\deploy-template.ps1 para templates globales, ver §5.5)
```

### 2.1 Brand Sync — quality gate integrado

```powershell
wp brand sync           # Falla si no hay .design-pass o si vars cambiaron y no pasan validación
wp brand sync --force   # Bypass total del quality gate
```

El quality gate tiene dos capas:

| Capa | Qué checkea | Cómo se saltea |
|------|-------------|----------------|
| Aprobación | `.design-pass` existe con `vars_hash` coincidente | `--force` |
| Validación mecánica | 54 checks: contraste WCAG AAA, escala headings/spaces/radii, armonía cromática, pairing tipográfico | `--force` |

Si `_design_vars.json` se edita después de `approve`, el hash cambia y sync re-valida automático.

```powershell
# Flujo completo recomendado
wp brand init <slug>                         # Crear vars
wp brand validate <slug> --suggest           # Ver calidad + sugerencias
wp brand approve <slug>                      # Aprobar (solo mecánico)
wp brand validate <slug> --skill=hallmark    # Validar con skill
wp brand approve <slug> --skill=hallmark     # Aprobar con skill
wp brand sync <slug>                         # Sincronizar
```

Lee `_design_vars.json` y sincroniza **todo** el ecosistema Divi:

| Destino | Qué escribe | Impacto |
|---------|-------------|---------|
| `wp_options['et_divi']` | Colores, fuentes, heading sizes h1-h6, botones (7 opciones), layout (3), performance (6), social (5), logo, favicon | Tema global completo |
| Global Colors (gcids) | Todos los colores via `GlobalData::set_global_colors()` | gcids vivos en páginas existentes y futuras |
| Global Variables (gvids) | Radios, espacios y fuentes via `GlobalData::set_global_variables()` | Variables nativas Divi 5 editables desde VB |
| `divitheme.json` | Solo presets + strategy | Design_Resolver los usa para merge estructural en deploy |

Divi regenera CSS automáticamente. Un solo comando, todo sincronizado.

### 2.2 Page Deploy

El deploy se hace con un solo comando usando el wrapper:

```powershell
.\workspace\deploy.ps1 -Slug inicio -Title "Inicio"
```

Esto ejecuta: combine.py → `wp agentic deploy_page` → cache flush. Usa `$env:DAW_SITE` para el site, o pásalo con `-Site <site>`.
---

## 3. Pipeline Diseño → Deploy (Capas)

```
Capa 0 — Brand Vars
  site/<DAW_SITE>/brand/_design_vars.json
  → Define colores, fuentes, radios, espacios, logo, customizer mapping

Capa 1 — Brand Sync (todo en uno)
  wp brand sync
  → 1. Escribe et_divi (Customizer global — colores, fuentes, heading sizes h1-h6, botones, layout, performance, social, logo, favicon)
  → 2. Registra gcids via GlobalData::set_global_colors() (colores vivos en VB)
  → 3. Registra gvids via GlobalData::set_global_variables() (radios, espacios, fuentes, sombras, animaciones como variables nativas Divi 5)
  → 4. Actualiza divitheme.json (solo presets + metadata)
  → 5. Flush caché CSS de Divi

Capa 2 — Page Deploy
  wp agentic deploy_page
  → Compila combined.json a Divi 5 blocks
  → Resuelve {{design:color:*}} → var(--gcid-*)
  → Layout Engine con renderers modulares (inc/core/renderers/*.php)
```

---

## 4. Page Definition — Estructura y Deploy

> Los comandos de esta sección se ejecutan desde la raíz del proyecto.

### 4.1. Estructura

```
site/<DAW_SITE>/page-defs/
├── inicio/                 ← Cada carpeta = una página o componente
│   ├── manifest.json       ← Manifiesto (lista de secciones)
│   ├── sections/           ← Archivos de sección individuales
│   ├── css/                ← CSS freeForm por sección (mismo nivel que sections/)
│   └── inicio-combined.json ← Output de combine.py (no editar)
├── header/                 ← Componente template
│   ├── manifest.json
│   ├── sections/
│   ├── css/
│   └── header-combined.json
├── footer/
│   ├── manifest.json
│   ├── sections/
│   ├── css/
│   └── footer-combined.json
└── ...                     ← Más páginas/componentes
```

Los scripts `workspace/combine.py`, `workspace/deploy.ps1` y `workspace/deploy-template.ps1` son transversales — se usan desde cualquier site.

### 4.2. Crear el manifiesto

El manifiesto (`manifest.json`) solo define qué secciones incluir y en qué orden, dentro de la carpeta de cada página:

```json
{
  "_manifest": "v1",
  "title": "Título de la Página",
  "slug": "inicio",
  "sections": [
    "sections/hero.json",
    "sections/services.json",
    "sections/cta-final.json"
  ]
}
```

Los paths de `sections/` son **relativos al directorio de la página** (donde está `manifest.json`).

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
  "css": "",    ← LO LLENA combine.py DESDE css/<module>.css
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
10. El CSS de sección se almacena en `css/<module>.css` al mismo nivel que `sections/`, y lo inyecta `combine.py`. El campo `"css"` en el JSON se deja vacío (`""`).

### 4.4. Combinar

```powershell
python workspace/combine.py site/<DAW_SITE>/page-defs/<slug>/manifest.json --out site/<DAW_SITE>/page-defs/<slug>/<slug>-combined.json
```

Esto resuelve los paths relativos del manifiesto, junta todas las secciones en un solo JSON, y lo escribe en `<slug>-combined.json` dentro de la carpeta de la página/componente. Si existe `css/<section-name>.css` (al mismo nivel que `sections/`), `combine.py` lo inyecta automáticamente en el campo `"css"` de la sección (freeForm nativo Divi 5).

### 4.5. Desplegar (wrapper)

```powershell
.\workspace\deploy.ps1 -Slug inicio -Title "Inicio"
```

Opciones:
- `-Site` — nombre del site (default: `$env:DAW_SITE`)
- `-SkipCache` — saltar limpieza de caché

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

**Dónde almacenar CSS de sección** (al mismo nivel que `sections/`):
```
css/
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

---

## 5. Theme Builder Ecosystem — Templates Globales

El pipeline desplega componentes del Theme Builder (header, footer, body) y los asigna a templates con alcance definido.

### 5.0. Comandos atómicos (CQRS)

Cada comando hace una sola cosa y es componible:

| Comando | Propósito |
|---------|-----------|
| `template_create --use-on="x" --title="y"` | Crea template. Falla si --use-on ya existe |
| `template_find --use-on="x"` | Retorna ID del template o 0 si no existe |
| `template_ensure --use-on="x" --title="y"` | Crea si no existe, retorna ID existente si ya está |
| `template_default` | Retorna el template default (lo crea si no existe) |
| `template_show <id>` | Muestra el template (use-on, layouts asignados, enabled) |
| `template_update <id> --title --use-on` | Actualiza título y/o use-on de un template existente |
| `template_delete <id>` | Trashes el template y lo desvincula del Theme Builder (soft delete) |
| `template_wire <id> --*-id=<x> [--*-enabled=1] [--*-global=1]` | Asigna layouts, enabled, y global flags a un template |
| `layout_deploy <type> --schema=<path> [--design-system=...]` | Crea un nuevo layout (nunca sobrescribe). Retorna ID |
| `layout_ensure <type> --schema=<path> --by-id=<id> [--design-system=...]` | Actualiza un layout existente por ID |
| `layout_list <type>` | Lista layouts existentes con ID y título |
| `deploy_page --title= --slug= --schema= [--design-system=] [--front]` | Crea/actualiza una página desde un JSON combinado (ver §4.5) |
| `export_page --slug=<slug>` | Exporta una página WP con bloques Divi 5 a schema JSON editable |
| `global_colors {sync,status,list} [--design-system=]` | Sincroniza/verifica/lista Global Colors (gcids) (ver §8) |
| `deploy_global_ecosystem ...` | Convenience wrapper: header + footer + body + template (ver §5.2) |
| `sync_css` | Legacy: sincroniza brand.css → Custom CSS. No necesario en el pipeline actual (§6) |

Uso típico combinado:

```powershell
# Crear template + layouts desde cero
$tid = wp agentic template_create --use-on="singular:post_type:page:all" --title="Pages"
$hid = wp agentic layout_deploy header --schema="site/<site>/page-defs/header/header-combined.json"
$fid = wp agentic layout_deploy footer --schema="site/<site>/page-defs/footer/footer-combined.json"
$bid = wp agentic layout_deploy body --schema="site/<site>/page-defs/body/body-combined.json"
wp agentic template_wire $tid --header-id=$hid --footer-id=$fid --body-id=$bid

# Hotfix: actualizar solo footer
wp agentic layout_ensure footer --schema="site/<site>/page-defs/footer/footer-combined.json" --by-id=456
```

### 5.1. Estructura de componentes

Los componentes (header, footer, body) usan la misma estructura que las páginas:

```
site/<DAW_SITE>/page-defs/
├── header/                  ← Componente: header global
│   ├── manifest.json
│   ├── sections/
│   ├── css/
│   └── header-combined.json
├── footer/                  ← Componente: footer global
│   ├── manifest.json
│   ├── sections/
│   ├── css/
│   └── footer-combined.json
└── body/                    ← Componente: body (ej. 404, landing)
    ├── manifest.json
    ├── sections/
    ├── css/
    └── body-combined.json
```

### 5.2. Comando: `deploy_global_ecosystem`

Despliega los 3 componentes y los asigna a un template. El flag `--mode` define el comportamiento (default: `create`):

| Modo | Qué hace | Cuándo usarlo |
|------|----------|---------------|
| `create` | Solo crea. Falla si el template o layout ya existe | Seguro por defecto — evita sobreescrituras accidentales |
| `update` | Solo actualiza. Requiere `--template-id` o `--*-id` | Hotfix sobre un ID específico |
| `upsert` | Crea si no existe, actualiza si ya existe | Scripts automatizados donde da igual crear/actualizar |

```powershell
.\wp.bat agentic deploy_global_ecosystem \
  --header="site/<DAW_SITE>/page-defs/header/header-combined.json" \
  --footer="site/<DAW_SITE>/page-defs/footer/footer-combined.json" \
  --body="site/<DAW_SITE>/page-defs/body/body-combined.json" \
  [--mode=upsert|create|update] \
  [--design-system="site/<DAW_SITE>/design-system/divitheme.json"] \
  [--use-on="singular:post_type:page:all"] \
  [--title="Mi Template"] \
  [--template-id=<id>] \
  [--header-id=<id>] [--footer-id=<id>] [--body-id=<id>] \
  [--header-enabled=<0|1>] [--footer-enabled=<0|1>] [--body-enabled=<0|1>]
```

| Parámetro | Requerido | Descripción |
|-----------|-----------|-------------|
| `--header` | sí | Path al JSON combinado del header |
| `--footer` | sí | Path al JSON combinado del footer |
| `--body` | sí | Path al JSON combinado del body |
| `--mode` | no | `create` (default) | `create` (falla si existe), `update` (requiere IDs), `upsert` (crea o actualiza) |
| `--design-system` | no | Path a `divitheme.json` para resolver tokens |
| `--use-on` | var | Alcance del template (ver §5.4). Requerido en `create` |
| `--title` | var | Título del template. Requerido en `create` |
| `--template-id` | no | Template existente a actualizar. Requerido en `update` sin `--use-on` |
| `--header-id` | no | Layout de header específico. Requerido en `update` para layouts |
| `--footer-id` | no | Layout de footer específico. Requerido en `update` para layouts |
| `--body-id` | no | Layout de body específico. Requerido en `update` para layouts |
| `--header-enabled` | no | `1` o `0`. Default: `1` |
| `--footer-enabled` | no | `1` o `0`. Default: `1` |
| `--body-enabled` | no | `1` o `0`. Default: `1` |

### 5.3. Comportamiento del pipeline

**Resolución de template** (según `--mode`):

| Modo | `--template-id` | `--use-on` match 1 | `--use-on` match varios | `--use-on` match 0 |
|------|----------------|--------------------|------------------------|-------------------|
| `create` | error | error (ya existe) | error (ya existe) | crea nuevo |
| `update` | usa ese ID | error (ambiguo, usa `--template-id`) | error (ambiguo) | error (no existe) |
| `upsert` | usa ese ID | actualiza ese | error, pide `--template-id` | crea nuevo |

**Resolución de layouts (header/footer/body)** (según `--mode`):

| Modo | `--*-id` dado | Sin `--*-id` |
|------|---------------|--------------|
| `create` | error (no puede targetear un layout existente) | crea nuevo layout |
| `update` | actualiza ese ID | error (requiere `--*-id`) |
| `upsert` | actualiza ese ID | busca más referenciado → menor ID → crea |

**Meta asignado a cada layout (`apply_divi_meta`):**
```php
_et_pb_use_builder = on
_et_pb_use_divi_5 = on
_et_pb_show_page_creation = off
_et_pb_built_with_d5 = 1
_et_pb_built_for_post_type = page
_et_pb_gutter_width = 3
_et_pb_enable_shortcode_tracking = ''
_et_pb_custom_css = ''
_et_pb_first_image = ''
_et_pb_truncate_post = ''
_et_pb_truncate_post_date = ''
_et_builder_version = (versión actual de Divi)
_et_theme_builder_marked_as_unused → eliminado
```

### 5.4. Valores válidos para `--use-on`

El pipeline valida contra patrones que Divi reconoce:

| Valor | Descripción |
|-------|-------------|
| `404` | Página 404 |
| `search` | Resultados de búsqueda |
| `homepage` | Página de inicio |
| `singular:post_type:<type>:all` | Todos los posts de un tipo (ej. `page`, `post`) |
| `singular:post_type:<type>:id:<id>` | Post específico por ID |
| `singular:post_type:<type>:children:id:<id>` | Hijos de un post |
| `singular:taxonomy:<tax>:term:id:<id>` | Término de taxonomía |
| `archive:all` | Todos los archivos |
| `archive:post_type:<type>` | Archivo por post type |
| `archive:taxonomy:<tax>:all` | Archivos de taxonomía |
| `archive:taxonomy:<tax>:term:id:<id>` | Término específico |
| `archive:user:all` | Todos los autores |
| `archive:user:id:<id>` | Autor específico |
| `archive:user:role:<role>` | Rol de autor |
| `archive:date:all` | Archivos por fecha |

### 5.5. Wrapper: `deploy-template.ps1`

Wrapper que usa comandos atómicos internamente. **Despliega solo los componentes que se le indiquen**, no requiere header+footer+body juntos. Despliega templates **default** (`-Default`, aplica a todas las páginas) o **custom** (`-UseOn`, condiciones específicas).

```powershell
.\workspace\deploy-template.ps1 -UseOn "singular:post_type:page:all" -Title "Todas las páginas"
```

El término "global" en los flags `-*Global` se refiere exclusivamente a si el **layout** es **compartido** entre varios templates (`=1`) o **exclusivo** de este template (`=0`). No confundir con template default.

```powershell
# Default — aplica a TODAS las páginas (template con _et_default=1)
.\workspace\deploy-template.ps1 -Default -Title "Footer"

# Custom — solo páginas que cumplan la condición
.\workspace\deploy-template.ps1 -UseOn "singular:post_type:page:all" -Title "Footer Pages"
```

**Resolución de componentes:**
- Si se pasa algún `-HeaderPath`, `-FooterPath` o `-BodyPath` → despliega **solo esos** (standalone)
- Si no se pasa ningún path → usa los paths por defecto (`page-defs/header/`, `page-defs/footer/`, `page-defs/body/`)

**Reuso de layouts:** cuando no se especifica `-*Id`, el script consulta si el template ya tiene un layout asignado para ese componente. Si existe, lo actualiza (no duplica). Si no, crea uno nuevo.

Parámetros:

| Parámetro | Requerido | Default | Descripción |
|-----------|-----------|---------|-------------|
| `-Title` | sí | — | Nombre del template |
| `-UseOn` | var | — | Condición para template personalizado (§5.4). Requerido si no `-Default` |
| `-Default` | var | — | Template default (aplica a todas las páginas). Excluye `-UseOn` |
| `-Site` | no | `$env:DAW_SITE` | Site/DAW_SITE |
| `-Mode` | no | `create` | create (default), update o upsert |
| `-TemplateId` | no | 0 | Template ID específico a actualizar |
| `-HeaderPath` | no | default global | Path custom al combined JSON del header |
| `-FooterPath` | no | default global | Path custom al combined JSON del footer |
| `-BodyPath` | no | default global | Path custom al combined JSON del body |
| `-HeaderId` | no | 0 | Layout ID a actualizar (si no se da, reusa existente del template o crea) |
| `-FooterId` | no | 0 | Layout ID a actualizar (si no se da, reusa existente del template o crea) |
| `-BodyId` | no | 0 | Layout ID a actualizar (si no se da, reusa existente del template o crea) |
| `-HeaderEnabled` | no | 1 | 0 deshabilita header en este template |
| `-FooterEnabled` | no | 1 | 0 deshabilita footer en este template |
| `-BodyEnabled` | no | 1 | 0 deshabilita body en este template |
| `-HeaderGlobal` | no | 1 | 0 si layout de header es exclusivo de este template (no compartido) |
| `-FooterGlobal` | no | 1 | 0 si layout de footer es exclusivo de este template |
| `-BodyGlobal` | no | 1 | 0 si layout de body es exclusivo de este template |
| `-SkipCombine` | no | — | Saltar combinación de manifests |
| `-SkipCache` | no | — | Saltar flush de caché |

Ejemplos:

```powershell
# Footer default (todas las páginas)
.\workspace\deploy-template.ps1 -Default -Title "Footer Principal" -FooterPath "site/<site>/page-defs/footer/footer-combined.json"

# Footer custom (solo páginas)
.\workspace\deploy-template.ps1 -UseOn "singular:post_type:page:all" -Title "Footer Pages" -FooterPath "site/<site>/page-defs/footer/footer-combined.json"

# Footer + header, sin body
.\workspace\deploy-template.ps1 -UseOn "singular:post_type:landing:all" -Title "Landings" -HeaderPath "..." -FooterPath "..."

# Solo body, layout exclusivo (no compartido)
.\workspace\deploy-template.ps1 -UseOn "404" -Title "Error 404" -BodyPath "..." -BodyGlobal 0 -HeaderEnabled 0 -FooterEnabled 0

# Actualizar template existente, solo body
.\workspace\deploy-template.ps1 -UseOn "singular:post_type:post:all" -Title "Blog" -TemplateId 123 -BodyId 456
```

## 6. ⭐ Brand → Divi Customizer (Pipeline Actual)

El brand ya no genera CSS propio. Divi renderiza todo desde sus opciones nativas de Customizer.

El comando `wp brand sync` (registrado por el plugin, no `brand-sync.php`) ahora lo hace **todo**: Customizer + gcids + gvids + divitheme.json.

Los tokens (color, font, radius, space) ya no están en `divitheme.json`. `Design_Resolver` v2.0 los lee directamente de stores nativos Divi 5:
- `GlobalData::get_global_colors()` → `{{design:color:*}}`
- `GlobalData::get_global_variables()` → `{{design:radius:space:font:*}}`

`divitheme.json` queda solo con presets + strategy.

### Lo que ya NO existe ni se necesita
- ❌ `build_design_system.py` — integrado en brand-sync
- ❌ `global_colors sync` como paso aparte — brand-sync lo hace inline (el subcomando `wp agentic global_colors sync` sigue existiendo para uso manual)
- ❌ `brand/assets/css/brand.css` — no se genera
- ❌ `daw-brand-css` enqueue — no se encola
- ❌ `wp agentic sync_css` — sigue registrado como subcomando, pero es legacy: sincroniza `brand.css` (pipeline viejo). En el pipeline actual Divi genera el CSS desde Customizer, así que no se necesita.
- ❌ Tokens en `divitheme.json` — se leen desde stores nativos Divi 5

---

## 7. Cómo Crear una Nueva Marca

> **UN SOLO COMANDO**: `wp brand`. Sin `eval-file`. Sin scripts sueltos.

```powershell
# Con .env (DAW_SITE=nombre-de-tu-marca)
.\wp brand init
.\wp brand sync

# Con slug directo (sin tocar .env)
.\wp brand init <sitio>
.\wp brand sync <sitio>
```

### Pasos detallados

```powershell
# 1. Editar .env — DAW_SITE=nombre-de-tu-marca

# 2. Generar _design_vars.json con scaffold genérico o con skill
.\wp brand init                                    # scaffold genérico
.\wp brand init --skill=hallmark                    # scaffold con valores hallmark

# 3. Validar calidad de diseño (opcional, recomendado)
.\wp brand validate <slug>                          # 54 checks mecánicos
.\wp brand validate <slug> --suggest               # + sugerencias correctivas
.\wp brand validate <slug> --skill=hallmark         # + validación contra skill

# 4. Aprobar para habilitar sync (opcional)
.\wp brand approve <slug>                           # solo mecánico
.\wp brand approve <slug> --skill=hallmark          # mecánico + skill

# 5. Sincronizar TODO (Customizer + divitheme.json + gcids + gvids)
.\wp brand sync <slug>                              # respeta quality gate
.\wp brand sync <slug> --force                      # bypass total

# 6. Crear page-defs + sections (ver §4)

# 7. Combinar y desplegar

```powershell
.\workspace\deploy.ps1 -Slug inicio -Title "Inicio"
```

---

## 8. Global Colors (gcids)

Los gcids se sincronizan automáticamente al ejecutar `wp brand sync`. No es necesario un paso aparte.

Para verificar estado:

| Acción | Comando |
|--------|---------|
| Verificar | `.\wp.bat agentic global_colors status --design-system="site/<DAW_SITE>/design-system/divitheme.json"` |
| Listar | `.\wp.bat agentic global_colors list` |

Si no hay gcids sincronizados, `deploy_page` emite warning y resuelve a hex.

---

## 9. Reglas DAW

1. No editar `divitheme.json` a mano — se genera desde `_design_vars.json`. Editar `_design_vars.json` y re-sincronizar.
2. No usar `divi/code` como comodín — consultar `blocks-dictionary.md` primero.
3. No usar `et_pb_*` (shortcodes Divi 4) — solo namespace `divi/*`.
4. Colores siempre como `{{design:color:*}}`, nunca hex hardcodeados en schemas.
5. **Deploy via wrapper scripts.** Usar `.\workspace\deploy.ps1` para páginas (§4.5) o `.\workspace\deploy-template.ps1` para templates (§5.5). No usar comandos sueltos. (`build_page.php` ya no existe — el Layout Engine refactorizado lo reemplazó.)
6. **CSS vía Divi Customizer.** El brand se sincroniza a `et_divi` opciones; Divi genera el CSS automáticamente. No hay CSS propio de marca.
7. **Brand sync único.** `wp brand sync` lee `_design_vars.json` y escribe a `wp_options['et_divi']`. No hay otro paso.
8. **Frontera site/:** Todo dato de proyecto va en `site/<DAW_SITE>/`. El framework no contiene datos de proyecto.
9. **Pipeline de página:** `site/<DAW_SITE>/page-defs/<slug>/manifest.json` → `workspace/combine.py` → `wp agentic deploy_page` → página en WP.
10. **Layout Engine refactorizado:** Renderers modulares en `inc/core/renderers/`.
11. **VIE (Visual Impact Engine):** **Archivado** en `_archive/vie/`. No es parte del pipeline activo (el flujo es el de las 4 fases + `combine.py` + `deploy_page`).
12. **DIE (ML):** Archivado en `_archive/die_pipeline/`. No usar para páginas nuevas.
13. **Sin fallbacks silenciosos:** Si `DAW_SITE` no está definido, el pipeline falla inmediatamente.
14. **CSS de sección autocontenido:** Cada sección lleva su propio CSS inline (freeForm en el atributo `css`). CSS global de página va en el Custom CSS de la página vía WordPress.
15. **⚠️ Sin `<` en freeForm CSS:** `wp_strip_all_tags()` trunca el CSS al encontrar `<`. Almacenar CSS en `css/<module>.css` (mismo nivel que `sections/`, lo inyecta `combine.py`).
16. **Mantener `site/example` sincronizado:** El template de marcas nuevas debe reflejar el schema real de `Token_Registry`. Tras tocar `Token_Registry` o la estructura de `site/`, correr `php divi-agentic-core/bin/check-example.php` (o `--fix` para regenerar). También valida sitios productivos: `--active` (DAW_SITE) o `--site=<slug>` detectan keys obsoletas/faltantes antes de que dañen el sync. No editarlo a mano ni dejar que diverja.

---

## 10. Arquitectura en Capas

```
┌──────────────────────────────────────────────────────────────┐
│ CAPA 3 — CLI / Orquestador                                   │
│   wp brand sync                                              │
│   wp brand init                                              │
│   wp brand reset                                             │
│   wp agentic deploy_page                                     │
├──────────────────────────────────────────────────────────────┤
│ CAPA 2 — Aplicación / Layout Engine                          │
│   divi-agentic-core/inc/core/class-layout-engine.php         │
│     → Dispatcher delgado con renderers modulares             │
│   divi-agentic-core/inc/core/renderers/*.php                 │
│     → 13 renderers (structural, text, button, media, form,   │
│       content-module, container, dynamic, woo, generic,      │
│       dgbm, dgpc, base + trait helpers)                      │
│   divi-agentic-core/inc/core/skills/                         │
│     → hallmark, high-end, impeccable (wp brand --skill)      │
│   divi-agentic-core/inc/core/intelligence/db/                │
│     → Catálogos CSV (UX_Engine): ux-guidelines, styles, etc. │
├──────────────────────────────────────────────────────────────┤
│ CAPA 1 — Brand Vars → Divi Customizer                        │
│   site/<DAW_SITE>/brand/_design_vars.json                    │
│   wp brand sync                                              │
│     → Mapea colores, fuentes, heading sizes, botones, layout, performance, social, favicon a et_divi │
│     → Divi genera CSS automáticamente                        │
└──────────────────────────────────────────────────────────────┘
```

---

## 11. Referencias

| Recurso | Path | Propósito |
|---------|------|-----------|
| SKILL.md (4 fases) | `daw-skill/SKILL.md` | Orquestación completa análisis → diseño → mapeo → CLI |
| Diccionario de bloques | `daw-skill/references/blocks-dictionary.md` | Guía de módulos Divi 5 |
| Arquitecto | `daw-skill/references/architect.md` | Análisis semántico (Fase 1) |
| Design Lead | `daw-skill/references/design-lead.md` | 6 Leyes de Calidad Autónoma (Fase 2, bloqueante) |
| Lógica del Ingeniero | `daw-skill/references/engineer.md` | Comandos CLI, deploy, verificación |
| Lógica del Diseñador | `daw-skill/references/designer.md` | Mapeo semántico → bloques, tokens, presets |
| Conocimiento técnico | `daw-skill/references/knowledge.md` | Reglas técnicas del proyecto |
| Brand Commands | `wp brand {init,validate,approve,revoke,sync,reset,status}` | Gestión completa del sistema de diseño |
| Agentic Commands | `wp agentic {deploy_page,export_page,global_colors,layout_*,template_*,deploy_global_ecosystem,sync_css}` | Deploy de páginas y templates (ver §5.0) |
| Skill Selection | `references/skill-selection.md` | Qué skill cargar según tipo de proyecto |
| Inputs/Outputs del DS | `references/design-system-inputs.md` | Formatos de `_design_vars.json`, `_design_presets.json`, brief JSON, CLI de generadores |
| Design Validator | `divi-agentic-core/inc/core/class-design-validator.php` | 54+ checks: contraste WCAG AAA, escala, armonía deltaE, pairing tipográfico |
| Layout Engine | `divi-agentic-core/inc/core/class-layout-engine.php` | Dispatcher con renderers modulares |
| Renderers | `divi-agentic-core/inc/core/renderers/*.php` | 13 renderers (structural, text, button, media, form, content-module, container, dynamic, woo, generic, dgbm, dgpc, base) |
| Module Registry | `divi-agentic-core/inc/core/class-module-registry.php` | Registra módulos Divi 5 custom desde `modules/` |
| Skills de diseño | `divi-agentic-core/inc/core/skills/*.php` | hallmark, high-end, impeccable — usados por `wp brand --skill` |
| Refactor Plan | `divi-agentic-core/inc/core/REFACTOR-PLAN.md` | Plan de migración del monolito a renderers |
| Example Checker | `divi-agentic-core/bin/check-example.php` | Mantiene `site/example` sincronizado con `Token_Registry` + estructura (`--fix` regenera) |
| Shared Kernel | `_archive/daw/` | Kernel Python (archivado — sin consumidores activos) |
| VIE package | `_archive/vie/vie/` | Visual Impact Engine (archivado, no usar) |
