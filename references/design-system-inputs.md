# Design System Inputs & Outputs

## 1. Brand Generator (`brand_generator.py`)

**Path:** `workspace/brand_generator.py`

Generates initial brand files from minimal input.

```powershell
python DAW_bundle/workspace/brand_generator.py --site <slug> --name "<Brand>" --accent "#HEX" [--tone luxury|tech|organic|minimal] [--from-design DESIGN.md]
```

**Outputs** in `site/<slug>/brand/`:
- `_design_vars.json` — brand variables (colors, fonts, radii, spaces)
- `_design_presets.json` — 64 empty preset placeholders
- `_content_bank.json` — copy, page_layouts, design_direction (copied from `site/example/brand/` template)

Tone override writes `strategy` field with `<tone>-<hue_type>`. Strategy detection uses CIELCH + semantic analysis (BrandStrategy class in build_design_system.py).

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

| Prefix | Variables | Example |
|--------|-----------|---------|
| `color_` | `accent`, `accent_hover`, `ink`, `ink_soft`, `surface_deep/mid/light/white`, `text_primary/secondary/on_dark`, `success`, `error` | `"#2A9D8F"` |
| `font_` | `display`, `body`, `ui` | `"'Fredoka', sans-serif"` |
| `customizer_` | `primary`, `secondary`, `heading`, `body`, `link` | `"accent"` |
| `radius_` | `sm`, `md`, `lg`, `xl`, `full` | `"8px"` |
| `space_` | `xs`, `sm`, `md`, `lg`, `xl`, `2xl`, `3xl` | `"24px"` |
| `brand_name`, `brand_description` | strings | `"Misiu Clínica Felina"` |

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

Each preset body follows Divi 5 module attribute structure. Values are deep-merged into auto-generated presets from `build_design_system.py`. Empty dicts `{}` are filtered out silently.

---

## 5. `_effects.css`

**Path:** `site/<DAW_SITE>/brand/_effects.css`

Optional. Custom CSS appended verbatim to `brand.css` during `build_design_system.py`. Used for per-brand animations, blob backgrounds, badge positioning, button overrides, etc. Not required — if missing, only auto-generated `daw-*` classes go into `brand.css`.

---

## 6. `build_design_system.py`

**Path:** `workspace/build_design_system.py`

### Input

| Source | File | Purpose |
|--------|------|---------|
| Auto-discovered | `site/<DAW_SITE>/brand/_design_vars.json` | Brand variables (colors, fonts, radii, spaces) |
| Auto-discovered | `site/<DAW_SITE>/brand/_design_presets.json` | User override presets (optional) |
| Auto-discovered | `site/<DAW_SITE>/brand/_effects.css` | Custom CSS appended to output (optional) |
| CLI `--vars` | Explicit path | Override auto-discovered vars |
| CLI `--presets` | Explicit path | Override auto-discovered presets |
| CLI `--out` | Explicit path | Override output path |
| Environment | `.env` → `DAW_SITE` | Determines which `site/` directory to use |

### Output

| File | Path | Contents |
|------|------|----------|
| `divitheme.json` | `site/<DAW_SITE>/design-system/divitheme.json` | Full schema: name, strategy, tokens (color/font/radius/space), customizer mapping, 58 presets |
| `brand.css` | `site/<DAW_SITE>/brand/assets/css/brand.css` | CSS custom properties `--daw-*` + utility classes + `_effects.css` appendage |

### `divitheme.json` top-level keys

```json
{
  "name": "Brand Name",
  "description": "Brand description",
  "strategy": "cool-luxury|warm-premium|...",
  "tokens": {
    "color": { ... },
    "font": { ... },
    "radius": { ... },
    "space": { ... }
  },
  "customizer": {
    "primary": "accent",
    "secondary": "accent-hover",
    "heading": "text-primary",
    "body": "text-secondary",
    "link": "accent"
  },
  "presets": {
    "section": { "hero-dark": {...}, "hero-glass": {...}, "light": {...}, "dark": {...}, "white": {...}, "trust-bar": {...}, ... },
    "text": { "eyebrow": {...}, "display": {...}, "heading-*": {...}, "body": {...}, "body-sm": {...}, "stat-num-dark": {...}, "stat-label-dark": {...}, ... },
    "module": { "glass-card": {...}, "glass-card-dark": {...}, "hover-glow": {...}, "hover-lift": {...}, "glass-button": {...}, "glass-input": {...}, ... },
    "divider": { "curve-bottom": {...}, "wave-top": {...}, "tilt-top": {...}, ... },
    "animation": { "fade-in": {...}, "slide-up": {...}, "zoom-in": {...}, "stagger-reveal": {...}, "blur-reveal": {...}, ... },
    "scroll": { "fade-in": {...}, "parallax-up": {...}, "reveal": {...}, "blur-in": {...}, ... },
    "transform": { "hover-lift": {...}, "hover-scale": {...}, "hover-glow": {...}, "hover-expand": {...}, ... }
  }
}
```

### CLI Flags

```
  -v, --vars PATH         Explicit vars file (override auto-discover)
  -p, --presets PATH      Explicit presets file (override auto-discover)
  -o, --out PATH          Output path (override auto-discover)
  --no-enrich             Skip intelligence: raw vars only, no palette/presets
  --validate-only         Validate only, no write
  -q, --quiet             Minimal output
  --substitute-colors     Replace {{design:color:...}} with hex values in output
```

### CIELCH Pipeline

```
accent HEX → BrandStrategy.analyze() → strategy dict (hue_type, semantic, glass_viable, ...)
                                  ↓
accent + strategy → PaletteEngine.generate() → full palette (25+ colors: accent variants, surface scale, text, glass, glow, aura, borders, functional)
                                  ↓
strategy → TypographyEngine.generate() → fonts dict + rules (weights, line heights, tracking) + sizes (clamp())
                                  ↓
palette + strategy + typography → PresetBuilder.build() → 58 presets across 7 categories
                                  ↓
VisualValidator.validate() → WCAG AA/AAA + Delta E harmony checks
                                  ↓
build_complete_schema() → divitheme.json + brand.css
```

### Notes

- `_effects.css` is appended to `brand.css` after auto-generated classes.
- `brand.css` is the **single source of truth** for brand CSS. No DB storage.
- Switch `--no-enrich` to skip CIELCH intelligence (pass through raw vars only).
- Run `wp agentic global_colors sync --design-system="..."` after each design system change.
- `brand.css` lives per-brand: `site/<DAW_SITE>/brand/assets/css/brand.css`. Plugin enqueues the correct one via `DAW_SITE` env var.
