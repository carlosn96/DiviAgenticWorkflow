"""
Design System Builder v4.0 — Visual Intelligence Engine
=========================================================
Deterministic, perceptually-aware design system generation from brand variables.
Uses CIELCH color space for perceptually-uniform palette derivation.

Dependencies:
    pip install colour-science colormath numpy

Features:
  - CIELCH perceptual color analysis (no naive HSL)
  - Brand strategy detection from color + name semantics
  - Automatic palette: surfaces, glass, glow, aura, borders
  - Smart preset generation: glass-card, hover-glow, hero-aura
  - Per-strategy typography rules (spacing, weight, tracking)
  - WCAG AA/AAA + Delta E harmony validation

Usage:
    python build_design_system.py                    # auto-discovers brand/ files
    python build_design_system.py --vars vars.json   # explicit vars
    python build_design_system.py --validate-only     # check only
"""

import json, os, re, copy, math, argparse, sys
from typing import Dict, List, Tuple, Any, Optional

# --- Optional colour-science for perceptual color ---
try:
    import colour
    HAS_COLOUR = True
except Exception:
    HAS_COLOUR = False
    print("[WARN] colour-science not available; install with: pip install colour-science")

# --- Paths ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DAW_ROOT = os.path.dirname(SCRIPT_DIR)

# Lazy site resolver — defers DAW_SITE / SITE_DIR / BRAND_DIR / OUT_PATH until used,
# so importing this module no longer triggers ConfigError at import time.
sys.path.insert(0, DAW_ROOT)
from daw.cfg import (  # noqa: E402
    load_daw_site as _load_daw_site,
    get_site_dir as _get_site_dir,
    get_brand_dir as _get_brand_dir,
    get_design_system_path as _get_design_system_path,
)


def _site_paths():
    site = _load_daw_site()
    site_dir = os.path.join(DAW_ROOT, 'site', site)
    return {
        'DAW_SITE': site,
        'SITE_DIR': site_dir,
        'BRAND_DIR': os.path.join(site_dir, 'brand'),
        'OUT_PATH': os.path.join(site_dir, 'design-system', 'divitheme.json'),
    }


def _maybe_site_paths():
    """Resolve site paths only when explicitly called (main(), functions, etc).

    The module-level constants DAW_SITE/SITE_DIR/BRAND_DIR/OUT_PATH below are
    kept as None placeholders so legacy code reading them at import time does
    not break — they will be populated by `init_site_paths()` or directly when
    `main()` runs.
    """
    try:
        return _site_paths()
    except Exception:
        if '-h' in sys.argv or '--help' in sys.argv:
            return {
                'DAW_SITE': 'example',
                'SITE_DIR': os.path.join(DAW_ROOT, 'site', 'example'),
                'BRAND_DIR': os.path.join(DAW_ROOT, 'site', 'example', 'brand'),
                'OUT_PATH': os.path.join(DAW_ROOT, 'site', 'example', 'design-system', 'divitheme.json'),
            }
        raise

DAW_SITE = None
SITE_DIR = None
BRAND_DIR = None
OUT_PATH = None


def init_site_paths():
    """Populate module-level DAW_SITE / SITE_DIR / BRAND_DIR / OUT_PATH.

    Call this from main() (and from any legacy helper that needs them) to
    keep import-time side-effect-free.
    """
    global DAW_SITE, SITE_DIR, BRAND_DIR, OUT_PATH
    paths = _maybe_site_paths()
    DAW_SITE = paths['DAW_SITE']
    SITE_DIR = paths['SITE_DIR']
    BRAND_DIR = paths['BRAND_DIR']
    OUT_PATH = paths['OUT_PATH']


# Backwards-compat alias: legacy code may still call _load_daw_site() directly.
def _legacy_load_daw_site() -> str:  # pragma: no cover - legacy shim
    return _load_daw_site()


PRESET_CATEGORIES = {'section', 'text', 'module', 'divider', 'animation', 'scroll', 'transform'}


# ===============================================================
# 1. PERCEPTUAL COLOR ENGINE (CIELCH)
# ===============================================================

class ColorSpace:
    """Unified color operations using CIELCH when available, RGB fallback."""

    @staticmethod
    def hex_to_rgb(hex_color: str) -> Tuple[float, float, float]:
        h = hex_color.lstrip('#')
        return tuple(int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4))

    @staticmethod
    def rgb_to_hex(r: float, g: float, b: float) -> str:
        return f'#{int(round(r*255)):02X}{int(round(g*255)):02X}{int(round(b*255)):02X}'

    @classmethod
    def hex_to_lch(cls, hex_color: str) -> Tuple[float, float, float]:
        """Return (Lightness, Chroma, Hue) in CIELCH."""
        if HAS_COLOUR:
            rgb = cls.hex_to_rgb(hex_color)
            xyz = colour.sRGB_to_XYZ(rgb)
            lab = colour.XYZ_to_Lab(xyz)
            lch = colour.Lab_to_LCHab(lab)
            return float(lch[0]), float(lch[1]), float(lch[2])
        # Fallback: approximate via RGB -> HSL
        r, g, b = cls.hex_to_rgb(hex_color)
        mx, mn = max(r, g, b), min(r, g, b)
        L = (mx + mn) / 2
        if mx == mn:
            return L * 100, 0.0, 0.0
        D = mx - mn
        S = D / (1 - abs(2*L - 1))
        if mx == r:
            H = ((g - b) / D) % 6
        elif mx == g:
            H = (b - r) / D + 2
        else:
            H = (r - g) / D + 4
        H = (H * 60) % 360
        return L * 100, S * 100, H

    @classmethod
    def lch_to_hex(cls, L: float, C: float, H: float) -> str:
        """CIELCH -> RGB hex."""
        if HAS_COLOUR:
            lab = colour.LCHab_to_Lab([L, C, H])
            xyz = colour.Lab_to_XYZ(lab)
            rgb = colour.XYZ_to_sRGB(xyz)
            return cls.rgb_to_hex(*[max(0, min(1, c)) for c in rgb])
        # Naive fallback
        return "#888888"  # Should not happen if colour is installed

    @classmethod
    def adjust_lightness(cls, hex_color: str, factor: float) -> str:
        L, C, H = cls.hex_to_lch(hex_color)
        new_L = max(0, min(100, L * factor))
        return cls.lch_to_hex(new_L, C, H)

    @classmethod
    def adjust_chroma(cls, hex_color: str, factor: float) -> str:
        L, C, H = cls.hex_to_lch(hex_color)
        new_C = max(0, C * factor)
        return cls.lch_to_hex(L, new_C, H)

    @classmethod
    def rotate_hue(cls, hex_color: str, degrees: float) -> str:
        L, C, H = cls.hex_to_lch(hex_color)
        new_H = (H + degrees) % 360
        return cls.lch_to_hex(L, C, new_H)

    @classmethod
    def contrast_ratio(cls, hex1: str, hex2: str) -> float:
        """WCAG relative luminance contrast."""
        def lum(c):
            r, g, b = cls.hex_to_rgb(c)
            def lin(x):
                return x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4
            return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)
        l1, l2 = lum(hex1), lum(hex2)
        lighter, darker = max(l1, l2), min(l1, l2)
        return (lighter + 0.05) / (darker + 0.05)

    @classmethod
    def delta_e(cls, hex1: str, hex2: str) -> float:
        """CIEDE2000 perceptual distance (requires colour-science)."""
        if not HAS_COLOUR:
            return 999.0  # Cannot compute without colour-science
        rgb1 = cls.hex_to_rgb(hex1)
        rgb2 = cls.hex_to_rgb(hex2)
        xyz1 = colour.sRGB_to_XYZ(rgb1)
        xyz2 = colour.sRGB_to_XYZ(rgb2)
        lab1 = colour.XYZ_to_Lab(xyz1)
        lab2 = colour.XYZ_to_Lab(xyz2)
        return float(colour.delta_E(lab1, lab2))

    @classmethod
    def is_dark(cls, hex_color: str) -> bool:
        L, _, _ = cls.hex_to_lch(hex_color)
        return L < 50


# ===============================================================
# 2. BRAND STRATEGY INTELLIGENCE
# ===============================================================

class BrandStrategy:
    """Detects design strategy from color properties + brand semantics."""

    WARM_HUES = (0, 45, 75)       # Red, Orange, Gold
    COOL_HUES = (180, 240, 280)   # Cyan, Blue, Purple
    NEUTRAL_HUES = (0, 360)       # Achromatic (low chroma)

    LUXURY_TERMS = {'institute', 'luxury', 'premium', 'royal', 'atelier',
                    'exclusive', 'bespoke', 'concierge'}
    TECH_TERMS = {'tech', 'digital', 'software', 'ai', 'app', 'data',
                  'cloud', 'system', 'labs', 'studio'}
    ORGANIC_TERMS = {'wellness', 'nature', 'organic', 'bio', 'green',
                     'health', 'life', 'fresh', 'eco'}
    MINIMAL_TERMS = {'minimal', 'mono', 'clean', 'simple', 'space',
                     'void', 'blank', 'raw'}

    @classmethod
    def analyze(cls, accent_hex: str, brand_name: str) -> Dict[str, Any]:
        L, C, H = ColorSpace.hex_to_lch(accent_hex)
        name_lower = brand_name.lower()

        # Hue classification
        hue_type = 'neutral'
        if C > 15:  # Only classify hue if there's enough chroma
            if 15 <= H <= 75 or 330 <= H <= 360:
                hue_type = 'warm'
            elif 160 <= H <= 290:
                hue_type = 'cool'
            else:
                hue_type = 'neutral'

        # Semantic classification from brand name
        scores = {
            'luxury': sum(1 for t in cls.LUXURY_TERMS if t in name_lower),
            'tech':   sum(1 for t in cls.TECH_TERMS   if t in name_lower),
            'organic': sum(1 for t in cls.ORGANIC_TERMS if t in name_lower),
            'minimal': sum(1 for t in cls.MINIMAL_TERMS if t in name_lower),
        }
        semantic = max(scores, key=scores.get)
        if scores[semantic] == 0:
            semantic = 'generic'

        # Strategy matrix: hue_type x semantic -> strategy
        STRATEGY_MAP = {
            ('warm', 'luxury'):  'luxury-warm',
            ('warm', 'tech'):    'energetic-tech',
            ('warm', 'organic'): 'earth-organic',
            ('warm', 'minimal'): 'warm-minimal',
            ('warm', 'generic'): 'warm-premium',
            ('cool', 'luxury'):  'cool-luxury',
            ('cool', 'tech'):    'tech-cool',
            ('cool', 'organic'): 'fresh-organic',
            ('cool', 'minimal'): 'cool-minimal',
            ('cool', 'generic'): 'cool-premium',
            ('neutral', 'luxury'):  'mono-luxury',
            ('neutral', 'tech'):    'mono-tech',
            ('neutral', 'organic'): 'natural-neutral',
            ('neutral', 'minimal'): 'pure-minimal',
            ('neutral', 'generic'): 'neutral-premium',
        }
        strategy = STRATEGY_MAP.get((hue_type, semantic), 'generic')

        return {
            'strategy':    strategy,
            'hue_type':    hue_type,
            'semantic':    semantic,
            'lightness':   L,
            'chroma':      C,
            'hue':         H,
            'is_dark':     L < 50,
            'is_saturated': C > 60,
            'is_muted':    C < 30,
            'glass_viable': L > 40 and L < 80,
        }


# ===============================================================
# 3. PALETTE ENGINE (perceptually-uniform generation)
# ===============================================================

class PaletteEngine:
    """Generates complete color palette from accent + strategy."""

    @classmethod
    def generate(cls, accent: str, strategy: Dict[str, Any]) -> Dict[str, str]:
        L, C, H = ColorSpace.hex_to_lch(accent)
        strat = strategy['strategy']

        colors = {'accent': accent}

        # Accent variants
        colors['accent-hover'] = ColorSpace.adjust_lightness(accent, 0.85)
        colors['premium'] = cls._premium_from_accent(accent, strat)

        # Surface scale (perceptually uniform)
        colors['surface-deep']  = cls._surface_deep(accent, strat)
        colors['surface-mid']   = ColorSpace.adjust_lightness(colors['surface-deep'], 1.25)
        colors['surface-light'] = cls._surface_light(accent, strat)
        colors['surface-white'] = ColorSpace.adjust_lightness(colors['surface-light'], 1.02)

        # Text colors with guaranteed contrast
        colors['text-primary']   = cls._text_primary(colors['surface-light'], strat)
        colors['text-secondary'] = ColorSpace.adjust_lightness(colors['text-primary'], 1.35)
        colors['text-on-dark']   = cls._text_on_dark(colors['surface-deep'])
        colors['text-on-accent'] = cls._text_on_dark(accent) if ColorSpace.is_dark(accent) else cls._text_primary(accent, strat)

        # Glass system (derived from accent, not hardcoded)
        colors['glass-bg']           = cls._glass_bg(colors['surface-white'], accent)
        colors['glass-border']       = cls._glass_border(accent)
        colors['glass-border-light'] = cls._glass_border_light(accent)

        # Glow system
        colors['glow-accent']        = cls._glow_color(accent)
        colors['glow-accent-strong'] = cls._glow_color(accent, strong=True)

        # Aura / gradient overlays
        colors['aura-gradient'] = cls._aura_gradient(accent, strat)

        # Sepia/tertiary scale
        colors['sepia-100'] = ColorSpace.adjust_chroma(
            ColorSpace.adjust_lightness(accent, 1.4), 0.3)
        colors['sepia-300'] = ColorSpace.adjust_chroma(
            ColorSpace.adjust_lightness(accent, 1.2), 0.5)
        colors['sepia-500'] = accent
        colors['sepia-700'] = ColorSpace.adjust_lightness(accent, 0.7)
        colors['sepia-900'] = ColorSpace.adjust_lightness(accent, 0.5)

        # Functional
        colors['success'] = cls._functional_color('success', strat)
        colors['error']   = cls._functional_color('error', strat)

        return colors

    @classmethod
    def _premium_from_accent(cls, accent: str, strat: str) -> str:
        return ColorSpace.adjust_chroma(ColorSpace.adjust_lightness(accent, 1.25), 0.75)

    @classmethod
    def _surface_deep(cls, accent: str, strat: str) -> str:
        # Extraemos el Hue del color de acento para garantizar cohesión cromática
        L, C, H = ColorSpace.hex_to_lch(accent)
        # Bajamos drásticamente el lightness y chroma para crear un fondo oscuro del mismo tono
        # L=10 (muy oscuro), C=8 (muy poca saturación, elegante)
        base_dark = ColorSpace.lch_to_hex(10.0, 8.0, H)
        
        if 'luxury' in strat or 'warm' in strat:
            # Luxury/Warm: Hacemos el fondo ligeramente más cálido (restamos ~15 grados de hue si es posible) o subimos chroma
            return ColorSpace.lch_to_hex(12.0, 10.0, H)
        elif 'cool' in strat or 'tech' in strat:
            # Tech/Cool: Hacemos el fondo ligeramente más frío (más oscuro y azulado)
            return ColorSpace.lch_to_hex(8.0, 12.0, H)
        elif 'organic' in strat:
            # Organic: Menos chroma, ligeramente más luminoso
            return ColorSpace.lch_to_hex(14.0, 6.0, H)
        else:
            return base_dark

    @classmethod
    def _surface_light(cls, accent: str, strat: str) -> str:
        # Extraemos el Hue del color de acento
        L, C, H = ColorSpace.hex_to_lch(accent)
        # L=97 (muy claro, casi blanco), C=3 (apenas perceptible el tono)
        base_light = ColorSpace.lch_to_hex(97.0, 3.0, H)
        
        if 'luxury' in strat and 'warm' in strat:
            # Blanco huevo/crema
            return ColorSpace.lch_to_hex(96.0, 5.0, H)
        elif 'organic' in strat:
            return ColorSpace.lch_to_hex(95.0, 6.0, H)
        elif 'cool' in strat:
            # Blanco grisáceo azulado
            return ColorSpace.lch_to_hex(98.0, 2.0, H)
        else:
            return base_light

    @classmethod
    def _text_primary(cls, surface_light: str, strat: str) -> str:
        base = "#1D1D1F"
        cr = ColorSpace.contrast_ratio(base, surface_light)
        if cr >= 7.0:
            return base
        for factor in [0.95, 0.9, 0.85, 0.8, 0.75, 0.5, 0.3]:
            candidate = ColorSpace.adjust_lightness(base, factor)
            if ColorSpace.contrast_ratio(candidate, surface_light) >= 7.0:
                return candidate
        return "#111111"

    @classmethod
    def _text_on_dark(cls, surface_deep: str) -> str:
        base = "#F5F5F7"
        cr = ColorSpace.contrast_ratio(base, surface_deep)
        if cr >= 7.0:
            return base
        for factor in [1.05, 1.1, 1.15, 1.2, 1.5, 2.0]:
            candidate = ColorSpace.adjust_lightness(base, factor)
            if ColorSpace.contrast_ratio(candidate, surface_deep) >= 7.0:
                return candidate
        return "#EEEEEE"

    @classmethod
    def _glass_bg(cls, surface_white: str, accent: str) -> str:
        """Glass background: surface_white tinted with accent."""
        # Tomamos el surface white (que ya tiene el hue del acento gracias al fix anterior)
        # y le ponemos 88% de opacidad.
        return surface_white + "E0"  # ~88% opacity

    @classmethod
    def _glass_border(cls, accent: str) -> str:
        """Semi-transparent border from accent."""
        return accent + "1F"  # ~12% opacity

    @classmethod
    def _glass_border_light(cls, accent: str) -> str:
        """Very subtle border for inner elements."""
        return accent + "0D"  # ~5% opacity

    @classmethod
    def _glow_color(cls, accent: str, strong: bool = False) -> str:
        alpha = "4D" if strong else "26"  # 30% vs 15%
        return accent + alpha

    @classmethod
    def _aura_gradient(cls, accent: str, strat: str) -> str:
        """Radial gradient for section overlays."""
        r, g, b = ColorSpace.hex_to_rgb(accent)
        r, g, b = int(r*255), int(g*255), int(b*255)
        opacity = 0.15 if 'luxury' in strat else 0.18
        return f"radial-gradient(circle at 80% 20%, rgba({r},{g},{b},{opacity}) 0%, transparent 60%)"

    @classmethod
    def _functional_color(cls, type_: str, strat: str) -> str:
        if type_ == 'success':
            return "#34C759" if 'tech' in strat or 'cool' in strat else "#3D6B4F"
        return "#FF3B30" if 'tech' in strat or 'cool' in strat else "#8B3A3A"


# ===============================================================
# 4. TYPOGRAPHY ENGINE
# ===============================================================

class TypographyEngine:
    """Generates typography rules based on strategy."""

    STRATEGY_FONTS = {
        'luxury-warm': {
            'display': "'Bodoni Moda', Georgia, serif",
            'body':    "'Jost', system-ui, sans-serif",
            'ui':      "'Jost', system-ui, sans-serif",
        },
        'luxury-cool': {
            'display': "'Playfair Display', Georgia, serif",
            'body':    "'Inter', system-ui, sans-serif",
            'ui':      "'Inter', system-ui, sans-serif",
        },
        'tech-cool': {
            'display': "'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', sans-serif",
            'body':    "'Inter', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', sans-serif",
            'ui':      "'Inter', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', sans-serif",
        },
        'energetic-tech': {
            'display': "'Space Grotesk', -apple-system, sans-serif",
            'body':    "'Inter', -apple-system, sans-serif",
            'ui':      "'Inter', -apple-system, sans-serif",
        },
        'earth-organic': {
            'display': "'Cormorant Garamond', Georgia, serif",
            'body':    "'Crimson Pro', Georgia, serif",
            'ui':      "'DM Sans', system-ui, sans-serif",
        },
        'warm-minimal': {
            'display': "'Neue Montreal', -apple-system, sans-serif",
            'body':    "'Inter', -apple-system, sans-serif",
            'ui':      "'Inter', -apple-system, sans-serif",
        },
        'cool-minimal': {
            'display': "'Helvetica Neue', Helvetica, Arial, sans-serif",
            'body':    "'Inter', -apple-system, sans-serif",
            'ui':      "'Inter', -apple-system, sans-serif",
        },
        'generic': {
            'display': "'Inter', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', sans-serif",
            'body':    "'Inter', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', sans-serif",
            'ui':      "'Inter', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', sans-serif",
        },
    }

    STRATEGY_TYPE = {
        'luxury': {
            'display_weight':   800,
            'display_tracking': '-0.03em',
            'display_lh':       '0.95',
            'body_weight':      400,
            'body_lh':          '1.7',
        },
        'tech': {
            'display_weight':   700,
            'display_tracking': '-0.025em',
            'display_lh':       '1.0',
            'body_weight':      400,
            'body_lh':          '1.65',
        },
        'organic': {
            'display_weight':   600,
            'display_tracking': '-0.02em',
            'display_lh':       '1.1',
            'body_weight':      400,
            'body_lh':          '1.75',
        },
        'minimal': {
            'display_weight':   700,
            'display_tracking': '-0.02em',
            'display_lh':       '1.05',
            'body_weight':      400,
            'body_lh':          '1.6',
        },
        'generic': {
            'display_weight':   700,
            'display_tracking': '-0.02em',
            'display_lh':       '1.05',
            'body_weight':      400,
            'body_lh':          '1.7',
        },
    }

    @classmethod
    def generate(cls, strategy: Dict[str, Any], user_fonts: Dict[str, str]) -> Dict[str, Any]:
        strat_key = strategy['strategy']

        # Find base strategy key
        base = 'generic'
        for k in cls.STRATEGY_TYPE:
            if k in strat_key:
                base = k
                break

        # Fonts: user overrides > strategy defaults
        fonts = dict(cls.STRATEGY_FONTS.get(strat_key, cls.STRATEGY_FONTS['generic']))
        for k in ('display', 'body', 'ui'):
            if user_fonts.get(k):
                fonts[k] = user_fonts[k]

        rules = cls.STRATEGY_TYPE[base]

        return {
            'fonts': fonts,
            'rules': rules,
            'sizes': cls._generate_sizes(),
        }

    @classmethod
    def _generate_sizes(cls) -> Dict[str, str]:
        return {
            'display-xxl': "clamp(2.5rem, 6vw, 5rem)",
            'display-xl':  "clamp(2rem, 4.5vw, 3.75rem)",
            'display-lg':  "clamp(1.5rem, 3vw, 2.5rem)",
            'h1':          "clamp(1.75rem, 3.5vw, 2.75rem)",
            'h2':          "clamp(1.375rem, 2.5vw, 2rem)",
            'h3':          "clamp(1.125rem, 1.75vw, 1.5rem)",
            'body':        "clamp(1rem, 1.25vw, 1.125rem)",
            'body-lg':     "clamp(1.05rem, 1.5vw, 1.25rem)",
            'body-sm':     "clamp(0.8rem, 0.9vw, 0.875rem)",
            'eyebrow':     "clamp(0.7rem, 0.8vw, 0.75rem)",
        }


# ===============================================================
# 5. PRESET BUILDER
# ===============================================================

class PresetBuilder:
    """Constructs all presets from palette + strategy + typography."""

    @classmethod
    def build(cls, palette: Dict[str, str], strategy: Dict[str, Any],
              typography: Dict[str, Any], user_presets: Dict) -> Dict[str, Dict]:
        presets = {cat: {} for cat in PRESET_CATEGORIES}

        presets['section']   = cls._build_sections(palette, strategy)
        presets['text']      = cls._build_text(palette, typography)
        presets['module']    = cls._build_modules(palette, strategy)
        presets['divider']   = cls._build_dividers()
        presets['animation'] = cls._build_animations()
        presets['scroll']    = cls._build_scroll()
        presets['transform'] = cls._build_transforms(palette)

        # Merge user presets (override auto-generated)
        for cat, items in user_presets.items():
            if cat in presets:
                presets[cat] = {**presets[cat], **items}

        return presets

    @classmethod
    def _build_sections(cls, palette: Dict[str, str], strategy: Dict[str, Any]) -> Dict:
        glass = strategy.get('glass_viable', False)

        def spacing(top_desk: str, top_tab: str, top_phone: str) -> Dict:
            return {
                'desktop': {'value': {'padding': {'top': top_desk,  'bottom': top_desk,  'right': '96px', 'left': '96px'}}},
                'tablet':  {'value': {'padding': {'top': top_tab,   'bottom': top_tab,   'right': '48px', 'left': '48px'}}},
                'phone':   {'value': {'padding': {'top': top_phone, 'bottom': top_phone, 'right': '24px', 'left': '24px'}}},
            }

        sections = {
            'hero-dark': {
                'decoration': {
                    'background': {'desktop': {'value': {
                        'color': palette['surface-deep'],
                        'overlay': {'gradient': palette['aura-gradient']},
                    }}},
                    'spacing':   spacing('160px', '96px', '64px'),
                    'animation': {'desktop': {'value': {'style': 'fade', 'duration': '800ms', 'delay': '0ms'}}},
                }
            },
            'hero-image-dark': {
                'decoration': {
                    'spacing':   spacing('160px', '96px', '64px'),
                    'animation': {'desktop': {'value': {'style': 'fade', 'duration': '1000ms', 'delay': '0ms'}}},
                }
            },
            'hero-glass': {
                'decoration': {
                    'background': {'desktop': {'value': {
                        'color': palette['surface-deep'],
                        'overlay': {'gradient': palette['aura-gradient']},
                    }}},
                    'spacing':   spacing('160px', '96px', '64px'),
                    'animation': {'desktop': {'value': {'style': 'fade', 'duration': '1000ms', 'delay': '0ms'}}},
                }
            },
            'cta-epic': {
                'decoration': {
                    'background': {'desktop': {'value': {
                        'color': palette['surface-deep'],
                        'overlay': {'gradient': palette['aura-gradient']
                            .replace('80% 20%', '20% 80%')
                            .replace('0.06', '0.05')
                            .replace('0.08', '0.05')},
                    }}},
                    'spacing':   spacing('128px', '96px', '64px'),
                    'animation': {'desktop': {'value': {'style': 'fade', 'duration': '800ms', 'delay': '200ms'}}},
                }
            },
            'light': {
                'decoration': {
                    'background': {'desktop': {'value': {'color': palette['surface-light']}}},
                    'spacing':   spacing('96px', '64px', '40px'),
                    'animation': {'desktop': {'value': {'style': 'fade', 'duration': '600ms', 'delay': '50ms'}}},
                }
            },
            'dark': {
                'decoration': {
                    'background': {'desktop': {'value': {
                        'color': palette['surface-mid'],
                        'overlay': {'gradient': palette['aura-gradient']
                            .replace('80% 20%', '50% 50%')
                            .replace('0.06', '0.04')
                            .replace('0.08', '0.04')},
                    }}},
                    'spacing':   spacing('96px', '64px', '40px'),
                    'animation': {'desktop': {'value': {'style': 'fade', 'duration': '600ms', 'delay': '50ms'}}},
                }
            },
            'white': {
                'decoration': {
                    'background': {'desktop': {'value': {'color': palette['surface-white']}}},
                    'spacing':   spacing('96px', '64px', '40px'),
                    'animation': {'desktop': {'value': {'style': 'fade', 'duration': '600ms', 'delay': '50ms'}}},
                }
            },
            'trust-bar': {
                'decoration': {
                    'background': {'desktop': {'value': {'color': palette['surface-light']}}},
                    'border':    {'desktop': {'value': {'styles': {'top': {'style': 'solid', 'width': '1px', 'color': palette['glass-border-light']}}}}},
                    'spacing':   {'desktop': {'value': {'padding': {'top': '40px', 'bottom': '40px', 'right': '96px', 'left': '96px'}}}},
                    'animation': {'desktop': {'value': {'style': 'fade', 'duration': '600ms', 'delay': '100ms'}}},
                }
            },
        }

        return sections

    @classmethod
    def _build_text(cls, palette: Dict[str, str], typography: Dict[str, Any]) -> Dict:
        fonts = typography['fonts']
        rules = typography['rules']
        sizes = typography['sizes']

        def font_spec(size_key: str, color_key: str, is_heading: bool = True, level: str = 'h1') -> Dict:
            font_key = 'headingFont' if is_heading else 'bodyFont'
            return {
                font_key: {
                    level if is_heading else 'body': {
                        'font': {
                            'desktop': {'value': {
                                'fontFamily':    fonts['display'] if is_heading else fonts['body'],
                                'color':         palette.get(color_key, color_key),
                                'size':          sizes.get(size_key, size_key),
                                'weight':        str(rules['display_weight']) if is_heading else str(rules['body_weight']),
                                'lineHeight':    rules['display_lh'] if is_heading else rules['body_lh'],
                                'letterSpacing': rules['display_tracking'] if is_heading else '0em',
                            }}
                        }
                    }
                }
            }

        return {
            'eyebrow': {
                'headingFont': {'p': {'font': {'desktop': {'value': {
                    'fontFamily':    fonts['ui'],
                    'weight':        '500',
                    'textTransform': 'uppercase',
                    'letterSpacing': '0.12em',
                    'color':         palette['premium'],
                    'size':          '12px',
                }}}}}
            },
            'eyebrow-dark': {
                'headingFont': {'p': {'font': {'desktop': {'value': {
                    'fontFamily':    fonts['ui'],
                    'weight':        '500',
                    'textTransform': 'uppercase',
                    'letterSpacing': '0.2em',
                    'color':         palette['sepia-300'],
                    'size':          '12px',
                }}}}}
            },
            'hero-title':       font_spec('display-xxl', 'surface-white', True, 'h1'),
            'display-xl':       font_spec('display-xl',  'text-primary',  True, 'h1'),
            'display-md':       font_spec('display-lg',  'text-primary',  True, 'h2'),
            'display-md-light': font_spec('display-lg',  'surface-white', True, 'h2'),
            'headline':         font_spec('h2',          'text-primary',  True, 'h2'),
            'headline-light':   font_spec('h2',          'surface-white', True, 'h2'),
            'headline-3':       font_spec('h3',          'text-primary',  True, 'h3'),
            'lead': {
                'bodyFont': {'body': {'font': {'desktop': {'value': {
                    'fontFamily': fonts['body'],
                    'color':      palette['text-secondary'],
                    'size':       '20px',
                    'lineHeight': '1.7',
                }}}}}
            },
            'lead-dark': {
                'bodyFont': {'body': {'font': {'desktop': {'value': {
                    'fontFamily': fonts['body'],
                    'color':      palette['text-secondary'],
                    'size':       '18px',
                    'lineHeight': '1.65',
                }}}}}
            },
            'body-md': {
                'bodyFont': {'body': {'font': {'desktop': {'value': {
                    'fontFamily': fonts['body'],
                    'color':      palette['text-secondary'],
                    'size':       '16px',
                    'lineHeight': '1.6',
                }}}}}
            },
            'stat-num':   font_spec('display-lg', 'text-primary', True, 'h3'),
            'stat-label': {
                'bodyFont': {'body': {'font': {'desktop': {'value': {
                    'fontFamily':    fonts['ui'],
                    'color':         palette['text-secondary'],
                    'size':          '11px',
                    'weight':        '500',
                    'textTransform': 'uppercase',
                    'letterSpacing': '0.12em',
                    'lineHeight':    '1.3',
                }}}}}
            },
            'quote-serif': {
                'bodyFont': {'body': {'font': {'desktop': {'value': {
                    'fontFamily':    fonts['display'],
                    'color':         palette['text-primary'],
                    'size':          '28px',
                    'weight':        '400',
                    'style':         'italic',
                    'lineHeight':    '1.45',
                    'letterSpacing': '0.01em',
                }}}}}
            },
            'caption': {
                'bodyFont': {'body': {'font': {'desktop': {'value': {
                    'fontFamily': fonts['ui'],
                    'color':      palette['text-secondary'],
                    'size':       '12px',
                    'lineHeight': '1.4',
                }}}}}
            },
        }

    @classmethod
    def _build_modules(cls, palette: Dict[str, str], strategy: Dict[str, Any]) -> Dict:
        glass_card = cls._glass_card(palette)
        solid_card = cls._solid_card(palette)

        return {
            'card':         solid_card,
            'feature-card': cls._feature_card(palette),
            'glass-card':   glass_card,
            'stat-item': {
                'decoration': {
                    'spacing':   {'desktop': {'value': {'padding': {'top': '16px', 'bottom': '16px'}}}},
                    'transform': {'hover': {'value': {'translateY': '-2px'}}},
                    'animation': {'desktop': {'value': {'style': 'fade', 'duration': '800ms', 'delay': '0ms'}}},
                }
            },
            'testimonial-card': {
                'decoration': {
                    'background': {'desktop': {'value': {'color': palette['surface-white']}}},
                    'border':     {'desktop': {'value': {'radius': {
                        'topLeft': '10px', 'topRight': '10px',
                        'bottomRight': '10px', 'bottomLeft': '10px', 'sync': 'on',
                    }}}},
                    'boxShadow': {'desktop': {'value': {
                        'horizontal': '0px', 'vertical': '1px',
                        'blur': '3px', 'spread': '0px',
                        'color': palette['glass-border-light'],
                    }}},
                    'transform': {'hover': {'value': {'translateY': '-4px'}}},
                    'spacing':   {'desktop': {'value': {'padding': {
                        'top': '40px', 'right': '40px', 'bottom': '40px', 'left': '40px', 'sync': 'on',
                    }}}},
                    'animation': {'desktop': {'value': {'style': 'fade', 'duration': '800ms', 'delay': '100ms'}}},
                }
            },
            'image-shadow': {
                'decoration': {
                    'border':    {'desktop': {'value': {'radius': {
                        'topLeft': '10px', 'topRight': '10px',
                        'bottomRight': '10px', 'bottomLeft': '10px', 'sync': 'on',
                    }}}},
                    'boxShadow': {'desktop': {'value': {
                        'horizontal': '0px', 'vertical': '12px',
                        'blur': '40px', 'spread': '-4px',
                        'color': palette['glass-border'],
                    }}},
                    'transform': {'hover': {'value': {'scale': '1.02'}}},
                    'animation': {'desktop': {'value': {'style': 'fade', 'duration': '600ms', 'delay': '100ms'}}},
                }
            },
            'accent-line': {
                'decoration': {
                    'spacing': {'desktop': {'value': {'padding': {'top': '16px', 'bottom': '16px'}}}},
                    'border':  {'desktop': {'value': {'styles': {'bottom': {
                        'style': 'solid', 'width': '2px', 'color': palette['premium'],
                    }}}}},
                }
            },
            'btn-primary': {
                'decoration': {
                    'button': {'desktop': {'value': {
                        'backgroundColor': palette['accent'],
                        'color':  palette['surface-deep'],
                        'border': {'all': {'radius': {
                            'topLeft': '9999px', 'topRight': '9999px',
                            'bottomRight': '9999px', 'bottomLeft': '9999px', 'sync': 'on',
                        }}},
                    }}},
                    'spacing':   {'desktop': {'value': {'padding': {
                        'top': '14px', 'right': '32px', 'bottom': '14px', 'left': '32px', 'sync': 'on',
                    }}}},
                    'boxShadow': {'desktop': {'value': {
                        'horizontal': '0px', 'vertical': '8px',
                        'blur': '24px', 'spread': '-6px',
                        'color': palette['glow-accent'],
                    }}},
                    'transform': {'hover': {'value': {
                        'translateY': '-2px',
                        'boxShadow': {
                            'horizontal': '0px', 'vertical': '12px',
                            'blur': '32px', 'spread': '-8px',
                            'color': palette['glow-accent-strong'],
                        },
                    }}},
                }
            },
            'btn-outline': {
                'decoration': {
                    'button': {'desktop': {'value': {
                        'color':  palette['surface-white'],
                        'border': {'all': {
                            'style': 'solid', 'width': '1.5px', 'color': 'rgba(255,255,255,0.25)',
                        }},
                    }}},
                    'spacing':   {'desktop': {'value': {'padding': {
                        'top': '14px', 'right': '32px', 'bottom': '14px', 'left': '32px', 'sync': 'on',
                    }}}},
                    'transform': {'hover': {'value': {
                        'translateY': '-2px',
                        'borderColor': palette['accent'],
                    }}},
                }
            },
            'btn-ghost': {
                'decoration': {
                    'button': {'desktop': {'value': {
                        'color':  palette['text-primary'],
                    }}},
                    'transform': {'hover': {'value': {
                        'translateY': '0px',
                        'color': palette['accent'],
                    }}},
                }
            },
            'btn-primary-gradient': {
                'decoration': {
                    'button': {'desktop': {'value': {
                        'background': {'style': 'gradient', 'color': palette['accent'],
                                       'gradient': {'type': 'linear', 'direction': '135deg',
                                                    'stops': [{'color': palette['accent-hover'], 'position': '0'},
                                                              {'color': palette['accent'], 'position': '100'}]}},
                        'color':  palette['surface-deep'],
                        'border': {'radius': {
                            'topLeft': '9999px', 'topRight': '9999px',
                            'bottomRight': '9999px', 'bottomLeft': '9999px', 'sync': 'on',
                        }},
                    }}},
                    'spacing':   {'desktop': {'value': {'padding': {
                        'top': '18px', 'right': '44px', 'bottom': '18px', 'left': '44px', 'sync': 'on',
                    }}}},
                    'boxShadow': {'desktop': {'value': {
                        'horizontal': '0px', 'vertical': '6px',
                        'blur': '20px', 'spread': '-4px',
                        'color': palette['glow-accent'],
                    }}},
                    'hover': {'desktop': {'value': {
                        'translateY': '-4px',
                        'boxShadow': {
                            'horizontal': '0px', 'vertical': '16px',
                            'blur': '40px', 'spread': '-8px',
                            'color': palette['glow-accent-strong'],
                        },
                    }}},
                }
            },
            'heading-shadow': {
                'decoration': {
                    'font': {'desktop': {'value': {
                        'textShadow': f'0 2px 12px {palette["glow-accent"]}',
                    }}},
                }
            },
        }

    @classmethod
    def _glass_card(cls, palette: Dict[str, str]) -> Dict:
        return {
            'decoration': {
                'background': {'desktop': {'value': {
                    'color':                    palette['surface-white'] + 'D9',
                    'backdropFilter':           'blur(20px) saturate(1.4)',
                    'backdropFilterSupported':  'on',
                }}},
                'border': {'desktop': {'value': {
                    'radius': {
                        'topLeft': '16px', 'topRight': '16px',
                        'bottomRight': '16px', 'bottomLeft': '16px', 'sync': 'on',
                    },
                    'styles': {'all': {'style': 'solid', 'width': '1px', 'color': palette['glass-border']}},
                }}},
                'boxShadow': {'desktop': {'value': {
                    'horizontal': '0px', 'vertical': '8px',
                    'blur': '32px', 'spread': '0px',
                    'color': palette['glow-accent'],
                }}},
                'spacing':   {'desktop': {'value': {'padding': {
                    'top': '32px', 'right': '32px', 'bottom': '32px', 'left': '32px', 'sync': 'on',
                }}}},
                'transform': {'hover': {'value': {
                    'translateY': '-6px',
                    'boxShadow': {
                        'horizontal': '0px', 'vertical': '16px',
                        'blur': '48px', 'spread': '0px',
                        'color': palette['glow-accent-strong'],
                    },
                }}},
                'animation': {'desktop': {'value': {'style': 'fade', 'duration': '600ms', 'delay': '60ms'}}},
            }
        }

    @classmethod
    def _solid_card(cls, palette: Dict[str, str]) -> Dict:
        return {
            'decoration': {
                'background': {'desktop': {'value': {'color': palette['surface-white']}}},
                'border':     {'desktop': {'value': {'radius': {
                    'topLeft': '16px', 'topRight': '16px',
                    'bottomRight': '16px', 'bottomLeft': '16px', 'sync': 'on',
                }}}},
                'boxShadow':  {'desktop': {'value': {
                    'horizontal': '0px', 'vertical': '4px',
                    'blur': '16px', 'spread': '0px',
                    'color': palette['glass-border-light'],
                }}},
                'spacing':    {'desktop': {'value': {'padding': {
                    'top': '24px', 'right': '24px', 'bottom': '24px', 'left': '24px', 'sync': 'on',
                }}}},
                'transform':  {'hover': {'value': {'translateY': '-4px'}}},
                'animation':  {'desktop': {'value': {'style': 'fade', 'duration': '480ms', 'delay': '60ms'}}},
            }
        }

    @classmethod
    def _feature_card(cls, palette: Dict[str, str]) -> Dict:
        return {
            'decoration': {
                'background': {'desktop': {'value': {'color': palette['surface-white']}}},
                'border':     {'desktop': {'value': {'radius': {
                    'topLeft': '16px', 'topRight': '16px',
                    'bottomRight': '16px', 'bottomLeft': '16px', 'sync': 'on',
                }}}},
                'boxShadow':  {'desktop': {'value': {
                    'horizontal': '0px', 'vertical': '4px',
                    'blur': '16px', 'spread': '0px',
                    'color': palette['glass-border-light'],
                }}},
                'spacing':    {'desktop': {'value': {'padding': {
                    'top': '32px', 'right': '32px', 'bottom': '32px', 'left': '32px', 'sync': 'on',
                }}}},
                'transform':  {'hover': {'value': {'translateY': '-8px'}}},
                'animation':  {'desktop': {'value': {
                    'style': 'slide', 'direction': 'bottom',
                    'duration': '480ms', 'delay': '60ms', 'intensity': '10%',
                }}},
            }
        }

    @classmethod
    def _build_dividers(cls) -> Dict:
        return {
            'curve-top': {'decoration': {'shapeDivider': {'top': {
                'desktop': {'value': {'style': 'curve', 'height': '100px', 'flip': 'off', 'invert': 'on'}},
                'tablet':  {'value': {'height': '60px'}},
                'phone':   {'value': {'height': '40px'}},
            }}}},
            'curve-bottom': {'decoration': {'shapeDivider': {'bottom': {
                'desktop': {'value': {'style': 'curve', 'height': '100px', 'flip': 'off', 'invert': 'off'}},
                'tablet':  {'value': {'height': '60px'}},
                'phone':   {'value': {'height': '40px'}},
            }}}},
            'wave-top': {'decoration': {'shapeDivider': {'top': {
                'desktop': {'value': {'style': 'wave', 'height': '80px', 'flip': 'off', 'invert': 'off'}},
                'tablet':  {'value': {'height': '50px'}},
                'phone':   {'value': {'height': '30px'}},
            }}}},
            'tilt-top': {'decoration': {'shapeDivider': {'top': {
                'desktop': {'value': {'style': 'tilt', 'height': '80px', 'flip': 'off', 'invert': 'off'}},
                'phone':   {'value': {'height': '40px'}},
            }}}},
        }

    @classmethod
    def _build_animations(cls) -> Dict:
        return {
            'fade-in':      {'decoration': {'animation': {'desktop': {'value': {'style': 'fade',   'duration': '800ms', 'delay': '0ms', 'speedCurve': 'ease-out'}}}}},
            'fade-in-fast': {'decoration': {'animation': {'desktop': {'value': {'style': 'fade',   'duration': '400ms', 'delay': '0ms', 'speedCurve': 'ease-out'}}}}},
            'slide-up':     {'decoration': {'animation': {'desktop': {'value': {'style': 'slide',  'direction': 'bottom', 'duration': '600ms', 'intensity': {'slide': '15%'}, 'startingOpacity': '0%', 'speedCurve': 'ease-out'}}}}},
            'reveal-up':    {'decoration': {'animation': {'desktop': {'value': {'style': 'slide',  'direction': 'bottom', 'duration': '700ms', 'intensity': {'slide': '25%'}, 'startingOpacity': '0%', 'speedCurve': 'ease-out'}}}}},
            'zoom-in':      {'decoration': {'animation': {'desktop': {'value': {'style': 'zoom',   'direction': 'in',     'duration': '600ms', 'startingOpacity': '0%', 'speedCurve': 'ease-out'}}}}},
            'bounce-up':    {'decoration': {'animation': {'desktop': {'value': {'style': 'bounce', 'direction': 'bottom', 'duration': '800ms', 'speedCurve': 'ease-out'}}}}},
            'flip':         {'decoration': {'animation': {'desktop': {'value': {'style': 'flip',   'direction': 'bottom', 'duration': '600ms', 'speedCurve': 'ease-out'}}}}},
            'stagger-reveal': {'decoration': {'animation': {'desktop': {'value': {'style': 'fade', 'duration': '900ms', 'delay': '100ms', 'speedCurve': 'cubic-bezier(0.22, 1, 0.36, 1)'}}}, 'css': {'desktop': {'value': {'freeForm': '.selector { animation: revealUp 900ms cubic-bezier(0.16,1,0.3,1) 100ms both; }'}}}}},
            'blur-reveal': {'decoration': {'animation': {'desktop': {'value': {'style': 'fade', 'duration': '800ms', 'delay': '0ms', 'speedCurve': 'ease-out'}}}, 'css': {'desktop': {'value': {'freeForm': '.selector { filter: blur(4px); animation: revealUp 900ms cubic-bezier(0.16,1,0.3,1) 0ms both; }'}}}}},
        }

    @classmethod
    def _build_scroll(cls) -> Dict:
        return {
            'fade-in':     {'decoration': {'scroll': {'desktop': {'value': {'style': 'fade',  'duration': '1000ms'}}}}},
            'parallax-up': {'decoration': {'scroll': {'desktop': {'value': {'style': 'slide', 'direction': 'bottom', 'speed': 'medium'}}}}},
            'scale-in':    {'decoration': {'scroll': {'desktop': {'value': {'style': 'scale', 'duration': '800ms'}}}}},
            'reveal':      {'decoration': {'scroll': {'desktop': {'value': {'style': 'slide', 'direction': 'bottom', 'duration': '600ms', 'startingOpacity': '0%'}}}}},
            'blur-in':     {'decoration': {'scroll': {'desktop': {'value': {'style': 'blur',  'duration': '800ms'}}}}},
        }

    @classmethod
    def _build_transforms(cls, palette: Dict[str, str]) -> Dict:
        return {
            'hover-lift':   {'decoration': {'transform': {'hover': {'value': {'translateY': '-8px'}}}}},
            'hover-scale':  {'decoration': {'transform': {'hover': {'value': {'scale': {'x': '1.03', 'y': '1.03'}, 'origin': {'x': '50%', 'y': '50%'}}}}}},
            'hover-glow':   {'decoration': {'transform': {'hover': {'value': {
                'translateY': '-4px',
                'boxShadow':  {
                    'horizontal': '0px', 'vertical': '12px',
                    'blur': '32px', 'spread': '-8px',
                    'color': palette['glow-accent'],
                },
            }}}}},
            'hover-expand': {'decoration': {'transform': {'hover': {'value': {'scale': {'x': '1.03', 'y': '1.03'}, 'origin': {'x': '50%', 'y': '50%'}}}}}},
        }


# ===============================================================
# 6. VISUAL VALIDATOR
# ===============================================================

class VisualValidator:
    """Validates generated design system for WCAG + perceptual harmony."""

    @classmethod
    def validate(cls, tokens: Dict[str, str], strategy: Dict[str, Any]) -> List[str]:
        issues = []
        colors = {
            k: v for k, v in tokens.items()
            if not k.startswith('font')
            and not k.startswith('space')
            and not k.startswith('radius')
        }

        # WCAG checks
        pairs = [
            ('text-primary',   'surface-light'),
            ('text-secondary', 'surface-light'),
            ('text-on-dark',   'surface-deep'),
            ('text-on-dark',   'surface-mid'),
            ('accent',         'surface-white'),
        ]
        for fg, bg in pairs:
            if fg in colors and bg in colors:
                cr = ColorSpace.contrast_ratio(colors[fg], colors[bg])
                level = 'AAA' if cr >= 7 else ('AA' if cr >= 4.5 else 'FAIL')
                if level == 'FAIL':
                    issues.append(f'[FAIL] {fg} on {bg}: {cr:.1f}:1 (need >=4.5)')
                elif cr < 7:
                    issues.append(f'[WARN] {fg} on {bg}: {cr:.1f}:1 (AA ok, AAA >=7.0)')

        # Delta E harmony checks
        if HAS_COLOUR:
            de_pairs = [
                ('accent',  'premium'),
                ('accent',  'surface-light'),
                ('accent',  'surface-deep'),
            ]
            for c1, c2 in de_pairs:
                if c1 in colors and c2 in colors:
                    de = ColorSpace.delta_e(colors[c1], colors[c2])
                    if de < 10:
                        issues.append(f'[HARMONY] {c1} vs {c2}: ΔE={de:.1f} (too close, may blend)')

        return issues


# ===============================================================
# 7. BUILD COMPLETE SCHEMA
# ===============================================================

def build_tokens(palette: Dict[str, str], fonts: Dict[str, str],
                 radii: Dict[str, str], spaces: Dict[str, str]) -> Dict:
    return {
        'color':  palette,
        'font':   fonts,
        'radius': radii,
        'space':  spaces,
    }

def build_customizer(vars_dict: Dict[str, str]) -> Dict:
    mapping = {}
    for key, val in vars_dict.items():
        if key.startswith('customizer_'):
            mapping[key[11:]] = val
    return mapping

def build_complete_schema(user_vars: Dict[str, str], presets_path: str = None) -> Dict:
    # 1. Extract core variables
    accent     = user_vars.get('color_accent', '#8B6F47')
    brand_name = user_vars.get('brand_name', 'Brand')
    brand_desc = user_vars.get('brand_description', '')

    # 2. Strategy detection
    strategy = BrandStrategy.analyze(accent, brand_name)
    print(f'[STRATEGY] Detected: {strategy["strategy"]} '
          f'(hue={strategy["hue_type"]}, semantic={strategy["semantic"]}, '
          f'glass_viable={strategy["glass_viable"]})')

    # 3. Generate palette
    palette = PaletteEngine.generate(accent, strategy)
    print(f'[PALETTE] Generated {len(palette)} color tokens from accent')

    # 4. Typography
    user_fonts = {
        'display': user_vars.get('font_display'),
        'body':    user_vars.get('font_body'),
        'ui':      user_vars.get('font_ui'),
    }
    typography = TypographyEngine.generate(strategy, user_fonts)
    print(f'[TYPE] Fonts: display={typography["fonts"]["display"]}, '
          f'body={typography["fonts"]["body"]}')

    # 5. Radii & spaces from user vars (or defaults)
    radii  = {}
    spaces = {}
    for key, val in user_vars.items():
        if key.startswith('radius_'):
            radii[key[7:]] = val
        elif key.startswith('space_'):
            spaces[key[6:]] = val
    if not radii:
        radii = {
            'sm': '6px', 'md': '10px', 'lg': '14px', 'xl': '20px', 'full': '9999px',
        }
    if not spaces:
        spaces = {
            'xs': '4px',  'sm': '8px',  'md': '16px', 'lg': '24px',
            'xl': '32px', '2xl': '48px', '3xl': '64px', '4xl': '96px', '5xl': '128px',
        }

    # 6. Build presets
    user_presets = {}
    if presets_path and os.path.exists(presets_path):
        with open(presets_path, encoding='utf-8') as f:
            raw_user = json.load(f)
        # Filter out empty presets (brand generator creates {} placeholders)
        for cat, items in raw_user.items():
            filtered = {k: v for k, v in items.items() if v}
            if filtered:
                user_presets[cat] = filtered
        if user_presets:
            print(f'[PRESETS] Loaded {sum(len(v) for v in user_presets.values())} non-empty user presets from: {presets_path}')

    presets = PresetBuilder.build(palette, strategy, typography, user_presets)
    total_presets = sum(len(v) for v in presets.values())
    print(f'[PRESETS] Built {total_presets} presets')

    # 7. Assemble tokens
    tokens = build_tokens(palette, typography['fonts'], radii, spaces)

    # 8. Validate
    issues = VisualValidator.validate(palette, strategy)
    if issues:
        print('[VALIDATE] Issues found:')
        for iss in issues:
            print(f'  {iss}')
    else:
        print('[VALIDATE] All checks passed')

    return {
        'name':        brand_name,
        'description': brand_desc,
        'strategy':    strategy['strategy'],
        'tokens':      tokens,
        'customizer':  build_customizer(user_vars),
        'presets':     presets,
    }


# ===============================================================
# 8. FILE HELPERS
# ===============================================================

def _find_brand_file(filename: str) -> Optional[str]:
    if not os.path.isdir(BRAND_DIR):
        return None
    direct = os.path.join(BRAND_DIR, filename)
    if os.path.isfile(direct):
        return direct
    for entry in sorted(os.listdir(BRAND_DIR)):
        candidate = os.path.join(BRAND_DIR, entry, filename)
        if os.path.isfile(candidate):
            return candidate
    return None

def substitute_tokens(obj, palette: Dict[str, str]):
    """Replace {{design:color:*}} with actual hex values (for preview/debug)."""
    if isinstance(obj, str):
        if '{{design:color:' in obj:
            for k, v in palette.items():
                obj = obj.replace(f'{{{{design:color:{k}}}}}', v)
        return obj
    elif isinstance(obj, dict):
        return {k: substitute_tokens(v, palette) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [substitute_tokens(i, palette) for i in obj]
    return obj


# ===============================================================
# 9. CLI
# ===============================================================

def main():
    parser = argparse.ArgumentParser(
        description='Design System Builder v4.0 — Visual Intelligence Engine',
        epilog='CIELCH perceptual color, brand strategy detection, glass/glow presets, WCAG validation')
    parser.add_argument('--vars',  '-v', type=str, default=None, help='Path to JSON variables file')
    parser.add_argument('--presets', '-p', type=str, default=None, help='Path to JSON presets file')
    parser.add_argument('--out',   '-o', type=str, default=None, help='Output path')
    parser.add_argument('--no-enrich', action='store_true', help='Skip intelligence (raw vars only)')
    parser.add_argument('--validate-only', action='store_true', help='Validate only, no write')
    parser.add_argument('--quiet', '-q', action='store_true', help='Minimal output')
    parser.add_argument('--substitute-colors', action='store_true',
                        help='Replace tokens with hex values in output')
    args = parser.parse_args()

    init_site_paths()

    # Load variables
    user_vars = {}
    if args.vars:
        with open(args.vars, encoding='utf-8') as f:
            user_vars = json.load(f)
        if not args.quiet:
            print(f'[OK] Loaded variables from: {args.vars}')
    else:
        default_vars_path = _find_brand_file('_design_vars.json')
        if default_vars_path and os.path.exists(default_vars_path):
            with open(default_vars_path, encoding='utf-8') as f:
                user_vars = json.load(f)
            if not args.quiet:
                print(f'[OK] Loaded variables from: {default_vars_path}')
        else:
            if not args.quiet:
                print('[WARN] No _design_vars.json found — using minimal defaults')

    # Build schema
    schema = build_complete_schema(user_vars, presets_path=args.presets)

    if args.validate_only:
        return

    # Optional: substitute tokens for preview
    if args.substitute_colors:
        schema = substitute_tokens(schema, schema['tokens']['color'])

    # Write output
    out_path = args.out or OUT_PATH
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)

    # Generate brand.css for premium utilities (brand-specific path)
    brand_css_dir = os.path.join(BRAND_DIR, 'assets', 'css')
    os.makedirs(brand_css_dir, exist_ok=True)
    brand_css_path = os.path.join(brand_css_dir, 'brand.css')
    with open(brand_css_path, 'w', encoding='utf-8') as f:
        f.write("/* Auto-generated Brand CSS for Premium Visuals */\n")
        f.write(":root {\n")
        for k, v in schema.get('tokens', {}).get('color', {}).items():
            f.write(f"  --daw-color-{k}: {v};\n")
        f.write("}\n\n")
        f.write(".daw-glass-card {\n")
        f.write("  background-color: var(--daw-color-glass-bg) !important;\n")
        f.write("  backdrop-filter: blur(16px) !important;\n")
        f.write("  -webkit-backdrop-filter: blur(16px) !important;\n")
        f.write("  border: 1px solid var(--daw-color-glass-border) !important;\n")
        f.write("  box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.1) !important;\n")
        f.write("}\n\n")
        f.write(".daw-hover-glow {\n")
        f.write("  transition: all 0.3s ease !important;\n")
        f.write("}\n")
        f.write(".daw-hover-glow:hover {\n")
        f.write("  box-shadow: 0 0 24px var(--daw-color-glow-accent) !important;\n")
        f.write("  transform: translateY(-4px) !important;\n")
        f.write("}\n\n")
        f.write(".daw-hero-aura {\n")
        f.write("  background: var(--daw-color-surface-deep);\n")
        f.write("  background-image: var(--daw-color-aura-gradient);\n")
        f.write("}\n\n")

        # Append brand effects CSS if _effects.css exists in brand dir
        effects_path = os.path.join(BRAND_DIR, '_effects.css')
        if os.path.isfile(effects_path):
            with open(effects_path, 'r', encoding='utf-8') as ef:
                f.write(ef.read())
            if not args.quiet:
                print(f'[OK] Appended effects CSS from {effects_path}')

    if not args.quiet:
        tokens = schema.get('tokens', {})
        presets = schema.get('presets', {})
        total_presets = sum(len(v) for v in presets.values())
        print('')
        print(f'[OK] Design system generated: {out_path}')
        print(f'    Name:     {schema.get("name")}')
        print(f'    Strategy: {schema.get("strategy")}')
        print(f'    Tokens:   color={len(tokens.get("color", {}))}, '
              f'font={len(tokens.get("font", {}))}, '
              f'radius={len(tokens.get("radius", {}))}, '
              f'space={len(tokens.get("space", {}))}')
        print(f'    Presets:  {total_presets} total')
        for cat, pset in sorted(presets.items()):
            print(f'      - {cat}: {len(pset)}')
        print('')
        print(f'    Usage: wp agentic global_colors sync --design-system="{out_path}"')


if __name__ == '__main__':
    main()