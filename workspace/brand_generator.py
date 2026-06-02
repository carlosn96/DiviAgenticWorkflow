"""
Brand Generator — Automatic Brand Files Creator for DAW
========================================================
Generates _design_vars.json and _design_presets.json automatically from minimal input.
Uses the same Visual Intelligence Engine (CIELCH, strategy detection) as build_design_system.py.

Usage:
    # From CLI arguments
    python brand_generator.py --site aletheia --name "Aletheia Institute" --accent "#CA8A04"
    
    # With optional tone override
    python brand_generator.py --site aletheia --name "Aletheia Institute" --accent "#CA8A04" --tone luxury
    
    # From structured DESIGN.md (YAML frontmatter)
    python brand_generator.py --from-design DAW_bundle/site/aletheia/DESIGN.md

Output:
    site/<site>/brand/_design_vars.json      (brand variables)
    site/<site>/brand/_design_presets.json   (64 base presets)
    site/<site>/brand/_content_bank.json     (copied from site/example/brand/ template)

Dependencies:
    pip install colour-science pyyaml
"""

import json, os, sys, argparse, re
from pathlib import Path

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DAW_ROOT = os.path.dirname(SCRIPT_DIR)

# Make DAW_bundle and the workspace itself importable so we can load
# build_design_system.py as a module without side effects (its
# DAW_SITE / SITE_DIR / BRAND_DIR / OUT_PATH are now lazy).
if DAW_ROOT not in sys.path:
    sys.path.insert(0, DAW_ROOT)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import build_design_system as bds  # noqa: E402


def generate_design_vars(site_name: str, brand_name: str, accent: str,
                         tone: str = None, description: str = "",
                         fonts: dict = None) -> dict:
    """Generate complete _design_vars.json from minimal input."""
    bds.init_site_paths()

    # Strategy detection
    strategy = bds.BrandStrategy.analyze(accent, brand_name)
    if tone:
        # Override strategy base if tone specified
        strategy['strategy'] = f"{tone}-{strategy['hue_type']}"
    
    # Generate full palette
    palette = bds.PaletteEngine.generate(accent, strategy)
    
    # Typography
    user_fonts = fonts or {}
    typography = bds.TypographyEngine.generate(strategy, user_fonts)
    fonts_dict = typography['fonts']
    rules = typography['rules']
    
    # Build vars
    vars_dict = {
        "brand_name": brand_name,
        "brand_description": description or f"{brand_name} — {strategy['strategy'].replace('-', ' ').title()}",
        
        # Core colors
        "color_accent": palette['accent'],
        "color_accent_hover": palette['accent-hover'],
        "color_premium": palette['premium'],
        "color_ink": palette['text-primary'],
        "color_ink_soft": palette['text-secondary'],
        
        # Surface scale
        "color_surface_deep": palette['surface-deep'],
        "color_surface_mid": palette['surface-mid'],
        "color_surface_light": palette['surface-light'],
        "color_surface_white": palette['surface-white'],
        
        # Text
        "color_text_primary": palette['text-primary'],
        "color_text_secondary": palette['text-secondary'],
        "color_text_on_dark": palette['text-on-dark'],
        
        # Functional
        "color_success": palette['success'],
        "color_error": palette['error'],
        
        # Parchment scale (legacy compatibility)
        "color_parchment_50": palette['surface-white'],
        "color_parchment_100": palette['surface-light'],
        "color_parchment_200": bds.ColorSpace.adjust_lightness(palette['surface-light'], 1.01),
        "color_parchment_300": bds.ColorSpace.adjust_lightness(palette['surface-light'], 0.95),
        "color_parchment_500": palette['text-secondary'],
        "color_parchment_700": bds.ColorSpace.adjust_lightness(palette['text-primary'], 1.15),
        "color_parchment_900": palette['text-primary'],
        
        # Sepia scale
        "color_sepia_100": palette['sepia-100'],
        "color_sepia_300": palette['sepia-300'],
        "color_sepia_500": palette['sepia-500'],
        "color_sepia_700": palette['sepia-700'],
        "color_sepia_900": palette['sepia-900'],
        
        # Fonts
        "font_display": fonts_dict['display'],
        "font_body": fonts_dict['body'],
        "font_ui": fonts_dict['ui'],
        
        # Typography sizes (fluid)
        "font_size_display_xxl": "clamp(2.5rem, 6vw, 5rem)",
        "font_size_display_xl": "clamp(2rem, 4.5vw, 3.75rem)",
        "font_size_display_lg": "clamp(1.5rem, 3vw, 2.5rem)",
        "font_size_heading_1": "clamp(1.75rem, 3.5vw, 2.75rem)",
        "font_size_heading_2": "clamp(1.375rem, 2.5vw, 2rem)",
        "font_size_heading_3": "clamp(1.125rem, 1.75vw, 1.5rem)",
        "font_size_body": "clamp(1rem, 1.25vw, 1.125rem)",
        "font_size_body_lg": "clamp(1.05rem, 1.5vw, 1.25rem)",
        "font_size_body_sm": "clamp(0.8rem, 0.9vw, 0.875rem)",
        "font_size_eyebrow": "clamp(0.7rem, 0.8vw, 0.75rem)",
        
        # Typography weights
        "font_weight_display": str(rules['display_weight']),
        "font_weight_display_xxl": "800",
        "font_weight_body": str(rules['body_weight']),
        "font_weight_body_bold": "600",
        "letter_spacing_display": rules['display_tracking'],
        "letter_spacing_eyebrow": "0.15em",
        
        # Radius
        "radius_sm": "6px",
        "radius_md": "10px",
        "radius_lg": "14px",
        "radius_xl": "20px",
        "radius_full": "9999px",
        
        # Spacing
        "space_xs": "4px",
        "space_sm": "8px",
        "space_md": "16px",
        "space_lg": "24px",
        "space_xl": "32px",
        "space_2xl": "48px",
        "space_3xl": "64px",
        "space_4xl": "96px",
        "space_5xl": "128px",
        
        # Customizer
        "customizer_primary": "accent",
        "customizer_secondary": "ink",
        "customizer_heading": "ink",
        "customizer_body": "ink-soft",
        "customizer_link": "accent",
    }
    
    return vars_dict


def generate_design_presets() -> dict:
    """Generate base _design_presets.json with 64 presets."""
    return {
        "section": {
            "hero-dark": {},
            "hero-image-dark": {},
            "hero-video": {},
            "cta-epic": {},
            "light": {},
            "dark": {},
            "white": {},
            "trust-bar": {}
        },
        "text": {
            "eyebrow": {},
            "eyebrow-dark": {},
            "hero-title": {},
            "display-xl": {},
            "display-md": {},
            "display-md-light": {},
            "headline": {},
            "headline-light": {},
            "headline-3": {},
            "lead": {},
            "lead-dark": {},
            "body-md": {},
            "stat-num": {},
            "stat-label": {},
            "quote-serif": {},
            "caption": {}
        },
        "module": {
            "card": {},
            "feature-card": {},
            "glass-card": {},
            "stat-item": {},
            "testimonial-card": {},
            "image-shadow": {},
            "accent-line": {},
            "btn-primary": {},
            "btn-outline": {},
            "btn-ghost": {}
        },
        "divider": {
            "curve-top": {},
            "curve-bottom": {},
            "wave-top": {},
            "wave-bottom": {},
            "tilt-top": {}
        },
        "animation": {
            "fade-in": {},
            "fade-in-fast": {},
            "slide-up": {},
            "slide-down": {},
            "slide-left": {},
            "slide-right": {},
            "reveal-up": {},
            "zoom-in": {},
            "bounce-up": {},
            "flip": {},
            "fold": {},
            "roll": {}
        },
        "scroll": {
            "fade-in": {},
            "parallax-up": {},
            "parallax-down": {},
            "scale-in": {},
            "reveal": {},
            "rotate": {},
            "blur-in": {}
        },
        "transform": {
            "hover-lift": {},
            "hover-scale": {},
            "hover-glow": {},
            "hover-expand": {}
        }
    }


def _copy_content_bank(src: str, dst: str) -> bool:
    """Copy _content_bank.json from example template if source exists."""
    example_path = os.path.join(DAW_ROOT, 'site', 'example', 'brand', '_content_bank.json')
    if os.path.exists(example_path):
        with open(example_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        with open(dst, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"[OK] Copied content bank from template: {dst} ({len(data)} content keys)")
        print(f"     Edit this file to customize copy for your brand.")
        return True
    print(f"[SKIP] No template found at {example_path}. Create {dst} manually.")
    return False


def parse_design_md(path: str) -> dict:
    """Parse DESIGN.md with YAML frontmatter."""
    try:
        import yaml
    except ImportError:
        print("[ERROR] PyYAML required for --from-design. Install: pip install pyyaml")
        sys.exit(1)
    
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract YAML frontmatter between ---
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if not match:
        print("[ERROR] No YAML frontmatter found in DESIGN.md")
        sys.exit(1)
    
    frontmatter = yaml.safe_load(match.group(1))
    
    # Also extract inline tokens from body
    body = content[match.end():]
    tokens = {}
    
    # color.surface.base=#000000 style
    for line in body.split('\n'):
        for m in re.finditer(r'color\.([\w.]+)=([#\w]+)', line):
            tokens[f"color_{m.group(1).replace('.', '_')}"] = m.group(2)
        for m in re.finditer(r'font\.([\w.]+)=([^,\s]+)', line):
            tokens[f"font_{m.group(1).replace('.', '_')}"] = m.group(2)
    
    return {
        'site': frontmatter.get('site', 'unnamed'),
        'name': frontmatter.get('brand_name', 'Brand'),
        'accent': frontmatter.get('color_accent', '#8B6F47'),
        'tone': frontmatter.get('tone'),
        'description': frontmatter.get('brand_description', ''),
        'fonts': {
            'display': frontmatter.get('font_display'),
            'body': frontmatter.get('font_body'),
            'ui': frontmatter.get('font_ui'),
        },
        'tokens': tokens
    }


def main():
    parser = argparse.ArgumentParser(
        description='Brand Generator — Automatic _design_vars.json + _design_presets.json creator',
        epilog='Uses Visual Intelligence Engine (CIELCH) for perceptual palette generation'
    )
    parser.add_argument('--site', '-s', type=str, help='Site folder name (e.g., aletheia)')
    parser.add_argument('--name', '-n', type=str, help='Brand name (e.g., "Aletheia Institute")')
    parser.add_argument('--accent', '-a', type=str, help='Accent color hex (e.g., #CA8A04)')
    parser.add_argument('--tone', '-t', type=str, choices=['luxury', 'tech', 'organic', 'minimal'],
                        help='Override tone (optional, auto-detected if omitted)')
    parser.add_argument('--description', '-d', type=str, help='Brand description')
    parser.add_argument('--font-display', type=str, help='Display font family')
    parser.add_argument('--font-body', type=str, help='Body font family')
    parser.add_argument('--from-design', type=str, help='Path to DESIGN.md with YAML frontmatter')
    parser.add_argument('--yes', '-y', action='store_true', help='Skip confirmation')
    args = parser.parse_args()
    
    # Parse from DESIGN.md or CLI
    if args.from_design:
        design = parse_design_md(args.from_design)
        site = design['site']
        name = design['name']
        accent = design['accent']
        tone = design['tone']
        description = design['description']
        fonts = {k: v for k, v in design['fonts'].items() if v}
    else:
        if not args.site or not args.name or not args.accent:
            print("[ERROR] Required: --site, --name, --accent (or --from-design)")
            parser.print_help()
            sys.exit(1)
        site = args.site
        name = args.name
        accent = args.accent
        tone = args.tone
        description = args.description or ""
        fonts = {}
        if args.font_display:
            fonts['display'] = args.font_display
        if args.font_body:
            fonts['body'] = args.font_body
    
    # Paths
    site_dir = os.path.join(DAW_ROOT, 'site', site)
    brand_dir = os.path.join(site_dir, 'brand')
    vars_path = os.path.join(brand_dir, '_design_vars.json')
    presets_path = os.path.join(brand_dir, '_design_presets.json')
    content_path = os.path.join(brand_dir, '_content_bank.json')
    
    # Check existing
    if os.path.exists(vars_path) and not args.yes:
        response = input(f"[CONFIRM] _design_vars.json already exists at {vars_path}. Overwrite? [y/N]: ")
        if response.lower() != 'y':
            print("[CANCEL] Operation cancelled.")
            sys.exit(0)
    
    # Generate
    print(f"[GEN] Generating brand files for: {name}")
    print(f"[GEN] Accent: {accent}")
    
    vars_dict = generate_design_vars(site, name, accent, tone, description, fonts)
    presets_dict = generate_design_presets()
    
    # Write
    os.makedirs(brand_dir, exist_ok=True)
    
    with open(vars_path, 'w', encoding='utf-8') as f:
        json.dump(vars_dict, f, indent=2, ensure_ascii=False)
    print(f"[OK] Written: {vars_path} ({len(vars_dict)} variables)")
    
    with open(presets_path, 'w', encoding='utf-8') as f:
        json.dump(presets_dict, f, indent=2, ensure_ascii=False)
    print(f"[OK] Written: {presets_path} ({sum(len(v) for v in presets_dict.values())} presets)")
    
    # Copy content bank from example template if it doesn't exist
    if not os.path.exists(content_path):
        _copy_content_bank(DAW_ROOT, content_path)
    else:
        print(f"[SKIP] {content_path} already exists — edit manually to customize brand copy.")
    
    print(f"\n[NEXT] Run design system builder:")
    print(f"  python DAW_bundle/workspace/build_design_system.py --vars {vars_path}")
    print(f"\n[NEXT] Generate brief and deploy:")
    print(f"  python DAW_bundle/workspace/automation/generate_brief.py --site {site} ...")


if __name__ == '__main__':
    main()
