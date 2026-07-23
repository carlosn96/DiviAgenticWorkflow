# Design System Inputs & Outputs

> **Pipeline actual**: `inc/core/class-brand-sync-handler.php` (`Brand_Sync_Handler`) lee `_design_vars.json` y sincroniza a 4 destinos via `wp brand sync`: et_divi (Customizer), divitheme.json (solo presets + strategy), gcids (Global Colors), gvids (Global Variables: radios, espacios, fuentes, sombras, animaciones).

## 1. Inicialización (`wp brand init`)

**Source:** `inc/cli/class-brand-command.php` → `Brand_Init_Handler` (inline)

Crea el scaffold de archivos de marca a partir de un slug. No acepta parámetros de diseño — solo genera el archivo JSON vacío para que el diseñador lo edite.

```powershell
wp brand init <slug>
```

**Outputs** in `site/<slug>/brand/`:
- `_design_vars.json` — scaffold con keys vacías listas para editar
- No genera `_design_presets.json` ni `_content_bank.json` (se crean manualmente si se necesitan)

**Flujo recomendado tras init:**
1. Cargar un skill de dirección visual (`hallmark`, `impeccable`, `high-end-visual-design`)
2. Editar `_design_vars.json` con criterio de diseño real
3. Ejecutar `wp brand sync <slug>` para sincronizar a WordPress

---

## 2. Brief Format

**Path:** `workspace/automation/{ux_pro_brief_generator.py,generate_brief.py}`

Briefs are JSON files stored in `site/<DAW_SITE>/briefs/`.

```json
{
  "title": "Landing Page",
  "slug": "landing-page",
  "page_type": "landing|home|about|services|portfolio|pricing|contact|default",
  "tone": "cool_luxury|modern|editorial|premium|...",
  "description": "Brand - landing",
  "design_direction": {
    "mood": "cool_luxury",
    "hero_layout": "centered|asymmetric|split|fullscreen",
    "about_layout": "centered|image_left|image_right",
    "features_layout": "grid_3|grid_2|list|cards",
    "cta_layout": "centered|split|full_width",
    "motion_intensity": "subtle|moderate|high",
    "card_style": "glass|solid|outlined|elevated",
    "zone_dividers": true,
    "stagger_hero": true,
    "stagger_cta": true,
    "stagger_stats": true,
    "hero_divider_bottom": "curve|wave|tilt|none",
    "button_gradient": true|false,
    "heading_text_shadow": true|false,
    "grain_texture": true|false
  },
  "art_direction": {
    "page_type": "landing",
    "hero_visual": "product|people|abstract|space",
    "color_approach": "mono_accent|full_palette|analogous",
    "typography_mood": "contrast|harmonious|experimental",
    "lighting": "dramatic|soft|natural",
    "depth": "flat|layered|deep"
  },
  "sections": [
    {
      "section_type": "hero|features|stats|cta|team|process|testimonials|gallery|content|pricing|faq|trust-bar|contact",
      "eyebrow": "STRING",
      "title": "STRING",
      "text": "STRING",
      "btn_primary_text": "STRING",
      "btn_primary_url": "/",
      "image": "URL",
      "stats": [{"number": "10+", "label": "Años"}],
      "items": [{"title": "...", "icon": "...", "text": "..."}]
    }
  ]
}
```

Each `section_type` is a **semantic intent label**, not a visual slot. It maps to a `section_type` key in page-defs and gets expanded into Divi 5 blocks by the orchestrator.

---

## 3. `_design_vars.json`

**Path:** `site/<DAW_SITE>/brand/_design_vars.json`

| Prefix / Key | Variables | Mapeo Divi |
|---|---|---|
| `brand_name`, `brand_description` | strings | divitheme.json metadata |
| `color_` | `accent`, `accent_hover`, `ink`, `ink_soft`, `surface_deep/mid/light/white`, `text_primary/secondary/on_dark`, `success`, `error` | et_divi Customizer (38+ opciones) + gcids |
| `font_` | `display`, `body`, `ui` | et_divi font families + gvids fonts |
| `font_` sizing | `body_size`, `body_height`, `body_weight`, `heading_weight`, `heading_size_h1..h6` | et_divi font values + heading sizes |
| `customizer_` | `primary`, `secondary`, `heading`, `body`, `link` | Mapeo a gcid slots del Customizer |
| `radius_` | `sm`, `md`, `lg`, `xl`, `full` | gvids numbers |
| `space_` | `xs`, `sm`, `md`, `lg`, `xl`, `2xl`, `3xl` | gvids numbers |
| `shadow_` | `sm`, `md`, `lg`, `xl` | gvids numbers |
| `easing_` | `default`, `enter`, `exit` | gvids numbers |
| `duration_` | `fast`, `normal`, `slow` | gvids numbers |
| `button_` | `border_radius`, `border_width`, `font_size`, `font_style`, `text_color`, `text_color_hover`, `border_color` | et_divi button options |
| `layout_` | `content_width`, `fixed_nav`, `sidebar` | et_divi layout options |
| `perf_` | `dynamic_framework`, `dynamic_icons`, `critical_css`, `defer_block_css`, `jquery_body`, `disable_emojis` | et_divi performance options |
| `social_` | `facebook`, `twitter`, `instagram`, `youtube`, `linkedin` | et_divi social URLs |
| `logo_id`, `favicon_id`, `apple_icon_id` | attachment IDs | divi_logo, site_icon, divi_apple_touch_icon |

---

## 4. `_design_presets.json`

**Path:** `site/<DAW_SITE>/brand/_design_presets.json`

Optional user override presets. Dict keyed by preset category name:

```json
{
  "section": { "my-dark": { "decoration": { "background": { ... } } } },
  "text":    { "lead-dark": { "bodyFont": { "body": { "font": { "desktop": { "value": { ... } } } } } } }
}
```

Categories: `section`, `text`, `module`, `divider`, `animation`, `scroll`, `transform`.

Each preset body follows Divi 5 module attribute structure. Values are deep-merged into auto-generated presets from `Brand_Sync_Handler::sync_divitheme()`. Empty dicts `{}` are filtered out silently.

---

## 5. `_effects.css`

**Path:** `site/<DAW_SITE>/brand/_effects.css`

Optional. Custom CSS intended for per-brand animations, blob backgrounds, badge positioning, button overrides, etc. Not processed by the PHP handler — consumed by the external `build_design_system.py` (legacy) or enqueued manually. Not required for the `wp brand sync` flow.

---

## 6. `Brand_Sync_Handler` (Pipeline Actual)

**Source:** `inc/core/class-brand-sync-handler.php`

### Input

| Source | File | Purpose |
|--------|------|---------|
| **Único** | `site/<DAW_SITE>/brand/_design_vars.json` | Brand variables (colors, fonts, radii, spaces, buttons, layout, perf, social, logo) |

The handler reads `_design_vars.json` and writes to **4 Divi stores** in a single pass. No intermediate files, no CIELCH pipeline, no palette generation.

### Output

| Destino | API / Mecanismo | Qué escribe |
|---------|-----------------|-------------|
| `wp_options['et_divi']` | `update_option()` | 40+ keys: colores, fuentes, heading sizes h1–h6, botones (7), layout (3), performance (6), social (5), logo, favicon |
| Global Colors (gcids) | `GlobalData::set_global_colors()` | ~10 colores: accent, surface scale, text, functional |
| Global Variables (gvids) | `GlobalData::set_global_variables()` | ~22 vars: radios (5), espacios (7), sombras (4), easings (3), duraciones (3) |
| `divitheme.json` | `file_put_contents()` | Solo `presets` + `strategy` (sin tokens — se leen de stores nativos Divi 5) |

### Flujo interno

```
Brand_Sync_Handler::run($site)
  ├── validate($site)               ← checks vars file exists + required tokens
  ├── load_json($vars_path)         ← reads _design_vars.json
  ├── resolve_paths($site, $vars)   ← resolves divitheme.json path
  ├── sync_et_divi($site, $vars)    ← update_option('et_divi', ...)
  ├── sync_divitheme($vars)         ← escribe presets + strategy
  ├── sync_global_colors($vars)     ← GlobalData::set_global_colors()
  ├── sync_global_variables($vars)  ← GlobalData::set_global_variables()
  └── flush_divi_cache()            ← delete et-cache + core caches
```

### Lo que NO hace

- ❌ No genera paletas (no hay CIELCH, PaletteEngine, ni inteligencia de color)
- ❌ No genera CSS (`brand.css` no se crea ni se encola)
- ❌ No genera presets (solo copia los que vienen en `_design_vars.json` si existen)
- ❌ No resuelve `{{design:color:*}}` — eso lo hace `Design_Resolver` durante `deploy_page`
- ❌ No hay `build_design_system.py` — ese pipeline fue reemplazado

### Notas

- Los tokens (color, font, radius, space) se almacenan en stores nativos Divi 5 (`GlobalData`), no en `divitheme.json`.
- `divitheme.json` queda solo con `presets` + `strategy` para consumo del Layout Engine durante deploy.
- El CSS del brand lo genera Divi automáticamente desde `et_divi` options. No hay CSS propio de marca.
- `wp brand reset` revierte todo: elimina `et_divi`, limpia gcids/gvids, vacía `divitheme.json` y flushes cachés.
