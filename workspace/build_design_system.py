"""
Design System Builder v2.0 — Divi 5
=====================================
Data-driven: auto-discovers tokens from vars file, loads presets from JSON.
No hardcoded color/font/radius names — works with any brand variables.

Usage:
    python build_design_system.py                          # uses MINIMAL_VARS + default presets
    python build_design_system.py --vars my_vars.json       # loads from JSON file
    python build_design_system.py --presets my_presets.json # custom presets file
    python build_design_system.py --out custom.json         # custom output path
"""

import json, os, re, copy

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DAW_ROOT = os.path.dirname(SCRIPT_DIR)       # DAW_bundle/
DAW_SITE = os.environ.get('DAW_SITE', 'bibliotheca')
SITE_DIR = os.path.join(DAW_ROOT, 'site', DAW_SITE)
BRAND_DIR = os.path.join(SITE_DIR, 'brand')
OUT_DIR = os.path.join(SITE_DIR, 'design-system')
OUT_PATH = os.path.join(OUT_DIR, 'divitheme.json')

def _find_brand_file(filename):
    """Look for filename in any brand/<subdir>/ under BRAND_DIR."""
    if not os.path.isdir(BRAND_DIR):
        return None
    for entry in sorted(os.listdir(BRAND_DIR)):
        candidate = os.path.join(BRAND_DIR, entry, filename)
        if os.path.isfile(candidate):
            return candidate
    return None

# ═══════════════════════════════════════════════════════════════════
# ULTRA-PRO DEFAULT VARIABLES
# ═══════════════════════════════════════════════════════════════════

ULTRA_PRO_DEFAULTS = {
    "brand_name": "Ultra Pro Design System",
    "brand_description": "Ultra-pro design system for Divi 5. Refined, intentional, premium.",

    "color_accent":        "#8B6F47",
    "color_accent_hover":  "#6D5536",
    "color_premium":       "#C4A86A",
    "color_ink":           "#1C1A17",
    "color_ink_soft":      "#2E2B26",
    "color_parchment_50":  "#FCFAF5",
    "color_parchment_100": "#F5F1E8",
    "color_parchment_200": "#EAE4D4",
    "color_parchment_300": "#D6CCBA",
    "color_parchment_500": "#9E9282",
    "color_parchment_700": "#5C5244",
    "color_parchment_900": "#1C1A17",
    "color_sepia_100":     "#F7EFE0",
    "color_sepia_300":     "#C4A86A",
    "color_sepia_500":     "#8B6F47",
    "color_sepia_700":     "#6D5536",
    "color_sepia_900":     "#4A3515",
    "color_surface_deep":  "#1C1A17",
    "color_surface_mid":   "#2E2B26",
    "color_surface_light": "#F5F1E8",
    "color_surface_white": "#FCFAF5",
    "color_text_primary":  "#1C1A17",
    "color_text_secondary":"#5C5244",
    "color_text_on_dark":  "#FCFAF5",
    "color_success":       "#3D6B4F",
    "color_error":         "#8B3A3A",

    "font_display": "'Cormorant Garamond', Georgia, serif",
    "font_body":    "'Crimson Pro', Georgia, serif",
    "font_ui":      "'DM Sans', system-ui, sans-serif",

    "radius_sm":   "2px",
    "radius_md":   "4px",
    "radius_lg":   "8px",
    "radius_xl":   "16px",
    "radius_full": "100px",

    "space_xs":  "8px",
    "space_sm":  "16px",
    "space_md":  "24px",
    "space_lg":  "40px",
    "space_xl":  "48px",
    "space_2xl": "64px",
    "space_3xl": "96px",
    "space_4xl": "128px",
    "space_5xl": "160px",

    "customizer_primary":   "accent",
    "customizer_secondary": "premium",
    "customizer_heading":   "ink",
    "customizer_body":      "parchment-700",
    "customizer_link":      "accent",
}

# ═══════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════

def substitute(obj, vars_dict):
    """Recursively replace {{key}} placeholders with resolved values."""
    if isinstance(obj, str):
        if "{{" in obj:
            for k, v in vars_dict.items():
                obj = obj.replace("{{" + k + "}}", str(v))
        return obj
    elif isinstance(obj, dict):
        return {k: substitute(v, vars_dict) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [substitute(i, vars_dict) for i in obj]
    return obj


# ═══════════════════════════════════════════════════════════════════
# BUILD: TOKENS  (auto-discovered by prefix)
# ═══════════════════════════════════════════════════════════════════

def build_tokens(v):
    """Auto-discover tokens from vars dict by key prefix.
    
    Convention:  color_accent → tokens.color.accent
                 font_display → tokens.font.display
                 radius_sm    → tokens.radius.sm
                 space_5xl    → tokens.space.5xl
    """
    colors = {}
    fonts = {}
    radii = {}
    spaces = {}
    for key, val in v.items():
        if key.startswith('color_'):
            name = key[6:].replace('_', '-')
            colors[name] = val
        elif key.startswith('font_'):
            fonts[key[5:]] = val
        elif key.startswith('radius_'):
            radii[key[7:]] = val
        elif key.startswith('space_'):
            spaces[key[6:]] = val
    return {
        "color": colors,
        "font": fonts,
        "radius": radii,
        "space": spaces,
    }


# ═══════════════════════════════════════════════════════════════════
# BUILD: CUSTOMIZER
# ═══════════════════════════════════════════════════════════════════

def build_customizer(v):
    """Auto-discover customizer_* mappings from vars."""
    mapping = {}
    for key, val in v.items():
        if key.startswith('customizer_'):
            mapping[key[11:]] = val
    return mapping


# ═══════════════════════════════════════════════════════════════════
# BUILD: PRESETS (from data file)
# ═══════════════════════════════════════════════════════════════════

def load_presets(path=None):
    """Load presets from a JSON file. Returns dict with category keys."""
    if path is None:
        path = _find_brand_file("_design_presets.json")
    if not path or not os.path.exists(path):
        print(f"[WARN] Presets file not found: {path}")
        return {}
    with open(path, encoding='utf-8') as f:
        presets = json.load(f)
    # Validate structure
    required = {'section', 'text', 'module', 'animation', 'scroll', 'transform'}
    missing = required - set(presets.keys())
    if missing:
        print(f"[WARN] Presets file missing categories: {missing}")
    return presets


# ═══════════════════════════════════════════════════════════════════
# BUILD: COMPLETE SCHEMA
# ═══════════════════════════════════════════════════════════════════

def build_complete_schema(v, presets_path=None):
    schema = {
        "name": v.get("brand_name", "Design System"),
        "description": v.get("brand_description", ""),
        "tokens": build_tokens(v),
        "customizer": build_customizer(v),
        "presets": load_presets(presets_path),
    }
    schema = substitute(schema, v)
    return schema


# ═══════════════════════════════════════════════════════════════════
# RESOLVE VARIABLES
# ═══════════════════════════════════════════════════════════════════

def resolve_variables(user_vars=None):
    resolved = dict(ULTRA_PRO_DEFAULTS)
    if user_vars:
        for k, v in user_vars.items():
            if v is not None and v != "":
                resolved[k] = v
    return resolved


# ═══════════════════════════════════════════════════════════════════
# MINIMAL VARIABLES
# ═══════════════════════════════════════════════════════════════════

MINIMAL_VARS = {
    "brand_name": "Bibliotheca",
    "brand_description": "Premium Digital Library — El Silencio del Conocimiento",

    "color_accent":        "#A67C40",
    "color_accent_hover":  "#7A5A28",
    "color_premium":       "#D4A96A",
    "color_ink":           "#1A1814",
    "color_ink_soft":      "#2D2A25",
    "color_parchment_50":  "#FDFBF7",
    "color_parchment_100": "#F5F1E8",
    "color_parchment_200": "#EAE4D4",
    "color_parchment_300": "#D6CCBA",
    "color_parchment_500": "#9E9282",
    "color_parchment_700": "#5C5244",
    "color_parchment_900": "#1A1814",
    "color_sepia_100":     "#F7EFE0",
    "color_sepia_300":     "#D4A96A",
    "color_sepia_500":     "#A67C40",
    "color_sepia_700":     "#7A5A28",
    "color_sepia_900":     "#4A3515",
    "color_surface_deep":  "#1A1814",
    "color_surface_mid":   "#1A1814",
    "color_surface_light": "#F5F1E8",
    "color_surface_white": "#FDFBF7",
    "color_text_primary":  "#1A1814",
    "color_text_secondary":"#5C5244",
    "color_text_on_dark":  "#FDFBF7",
    "color_success":       "#3D6B4F",
    "color_error":         "#8B3A3A",

    "font_display": "'Cormorant Garamond', Georgia, serif",
    "font_body":    "'Crimson Pro', Georgia, serif",
    "font_ui":      "'DM Sans', system-ui, sans-serif",
}


# ═══════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Divi 5 Design System Builder — v2.0 (data-driven)")
    parser.add_argument("--vars", "-v", type=str, default=None,
                        help="Path to JSON variables file (all keys optional)")
    parser.add_argument("--presets", "-p", type=str, default=None,
                        help="Path to JSON presets file (default: site/<DAW_SITE>/brand/_design_presets.json)")
    parser.add_argument("--out", "-o", type=str, default=None,
                        help="Output path (default: site/<DAW_SITE>/design-system/divitheme.json)")
    parser.add_argument("--minimal", "-m", action="store_true",
                        help="Use built-in minimal variables (quick start)")
    args = parser.parse_args()

    user_vars = {}

    if args.vars:
        with open(args.vars, encoding='utf-8') as f:
            user_vars = json.load(f)
        print(f"[OK] Loaded variables from: {args.vars}")
    elif args.minimal:
        user_vars = dict(MINIMAL_VARS)
        print("[OK] Using minimal variables (quick start mode).")
    else:
        # Default: load from brand/<marca>/_design_vars.json
        default_vars_path = _find_brand_file("_design_vars.json")
        if default_vars_path and os.path.exists(default_vars_path):
            with open(default_vars_path, encoding='utf-8') as f:
                user_vars = json.load(f)
            print(f"[OK] Loaded variables from: {default_vars_path}")
        else:
            print("[OK] Using ultra-pro defaults (no vars file found).")

    v = resolve_variables(user_vars)
    schema = build_complete_schema(v, presets_path=args.presets)

    out_path = args.out or OUT_PATH
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)

    # Stats
    tokens = schema.get('tokens', {})
    presets = schema.get('presets', {})
    total_tokens = sum(len(v) for v in tokens.values())
    total_presets = sum(len(v) for v in presets.values())
    vars_used = sum(1 for k in v if k in list(user_vars.keys()) + list(ULTRA_PRO_DEFAULTS.keys()))

    print(f"[OK] Design system generated: {out_path}")
    print(f"    Tokens: {total_tokens} ({', '.join(f'{k}: {len(v)}' for k, v in tokens.items())})")
    print(f"    Presets: {total_presets} total")
    for cat, pset in presets.items():
        print(f"      - {cat}: {len(pset)}")
    print(f"    Variables used: {vars_used}")
    print()
    print(f"    Usage: wp agentic global_colors sync --design-system=\"{out_path}\"")


if __name__ == "__main__":
    main()
