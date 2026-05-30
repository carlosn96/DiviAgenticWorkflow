"""
Design System Builder v3.0 — Divi 5 Design Intelligence
=========================================================
Data-driven + design-aware: auto-discovers tokens, derives missing colors,
validates WCAG contrast, enriches presets with premium defaults (hover states,
clamp() fluid typography, glassmorphism, SVG dividers, motion).

Usage:
    python build_design_system.py                          # uses brand/ files or defaults
    python build_design_system.py --vars my_vars.json       # load variables
    python build_design_system.py --presets my_presets.json # custom presets
    python build_design_system.py --out custom.json         # output path
    python build_design_system.py --no-enrich              # skip intelligence layer
    python build_design_system.py --validate-only           # validate only, no write
"""

import json, os, re, copy, math

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DAW_ROOT = os.path.dirname(SCRIPT_DIR)
DAW_SITE = os.environ.get('DAW_SITE', 'bibliotheca')
SITE_DIR = os.path.join(DAW_ROOT, 'site', DAW_SITE)
BRAND_DIR = os.path.join(SITE_DIR, 'brand')
OUT_DIR = os.path.join(SITE_DIR, 'design-system')
OUT_PATH = os.path.join(OUT_DIR, 'divitheme.json')

# ─── Valid preset category names ───
PRESET_CATEGORIES = {'section', 'text', 'module', 'divider', 'animation', 'scroll', 'transform'}


# ═══════════════════════════════════════════════════════════════════
# COLOR MATH (stdlib only)
# ═══════════════════════════════════════════════════════════════════

def hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(r, g, b):
    return f'#{int(round(r)):02X}{int(round(g)):02X}{int(round(b)):02X}'

def rgb_to_hsl(r, g, b):
    r, g, b = r/255.0, g/255.0, b/255.0
    mx, mn = max(r, g, b), min(r, g, b)
    L = (mx + mn) / 2
    if mx == mn:
        return (0.0, 0.0, L)
    D = mx - mn
    S = D / (1 - abs(2*L - 1))
    if mx == r:
        H = ((g - b) / D) % 6
    elif mx == g:
        H = (b - r) / D + 2
    else:
        H = (r - g) / D + 4
    H /= 6
    return (H % 1.0, S, L)

def hsl_to_rgb(H, S, L):
    if S == 0:
        v = int(round(L * 255))
        return (v, v, v)
    def hue2rgb(p, q, t):
        if t < 0: t += 1
        if t > 1: t -= 1
        if t < 1/6: return p + (q - p) * 6 * t
        if t < 1/2: return q
        if t < 2/3: return p + (q - p) * (2/3 - t) * 6
        return p
    q = L * (1 + S) if L < 0.5 else L + S - L * S
    p = 2 * L - q
    r = hue2rgb(p, q, H + 1/3)
    g = hue2rgb(p, q, H)
    b = hue2rgb(p, q, H - 1/3)
    return (int(round(r * 255)), int(round(g * 255)), int(round(b * 255)))

def adjust_lightness(hex_color, factor):
    r, g, b = hex_to_rgb(hex_color)
    h, s, l = rgb_to_hsl(r, g, b)
    l = max(0.0, min(1.0, l * factor))
    r, g, b = hsl_to_rgb(h, s, l)
    return rgb_to_hex(r, g, b)

def adjust_saturation(hex_color, factor):
    r, g, b = hex_to_rgb(hex_color)
    h, s, l = rgb_to_hsl(r, g, b)
    s = max(0.0, min(1.0, s * factor))
    r, g, b = hsl_to_rgb(h, s, l)
    return rgb_to_hex(r, g, b)

def relative_luminance(hex_color):
    r, g, b = hex_to_rgb(hex_color)
    def linearize(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * linearize(r) + 0.7152 * linearize(g) + 0.0722 * linearize(b)

def contrast_ratio(hex1, hex2):
    l1 = relative_luminance(hex1)
    l2 = relative_luminance(hex2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)

def is_dark(hex_color):
    _, _, l = rgb_to_hsl(*hex_to_rgb(hex_color))
    return l < 0.45

def mix_colors(hex1, hex2, weight=0.5):
    r1, g1, b1 = hex_to_rgb(hex1)
    r2, g2, b2 = hex_to_rgb(hex2)
    w = max(0, min(1, weight))
    return rgb_to_hex(r1 * (1-w) + r2 * w, g1 * (1-w) + g2 * w, b1 * (1-w) + b2 * w)


# ═══════════════════════════════════════════════════════════════════
# DESIGN INTELLIGENCE — DERIVE COLORS
# ═══════════════════════════════════════════════════════════════════

def derive_color_variants(v):
    """Auto-compute derived colors from minimal input.
    
    Given just color_accent, can derive:
    - accent_hover, premium, sepia palette, surface contrast variants
    """
    derived = {}
    accent = v.get('color_accent', ULTRA_PRO_DEFAULTS['color_accent'])

    # accent_hover: 25% darker
    if 'color_accent_hover' not in v:
        derived['color_accent_hover'] = adjust_lightness(accent, 0.75)

    # premium: 20% lighter + desaturated
    if 'color_premium' not in v:
        lighter = adjust_lightness(accent, 1.35)
        derived['color_premium'] = adjust_saturation(lighter, 0.6)

    # sepia scale from accent
    if 'color_sepia_100' not in v:
        sepia_h, sepia_s, _ = rgb_to_hsl(*hex_to_rgb(accent))
        sepia_base = adjust_saturation(rgb_to_hex(*hsl_to_rgb(sepia_h, 0.35, 0.92)), 0.5)
        derived['color_sepia_100'] = sepia_base
    if 'color_sepia_300' not in v:
        derived['color_sepia_300'] = adjust_lightness(accent, 1.15)
    if 'color_sepia_500' not in v:
        derived['color_sepia_500'] = accent
    if 'color_sepia_700' not in v:
        derived['color_sepia_700'] = adjust_lightness(accent, 0.65)
    if 'color_sepia_900' not in v:
        derived['color_sepia_900'] = adjust_lightness(accent, 0.45)

    # Auto-ensure surface_light/surface_white if ink provided
    ink = v.get('color_ink', ULTRA_PRO_DEFAULTS['color_ink'])
    if 'color_surface_light' not in v:
        h, _, _ = rgb_to_hsl(*hex_to_rgb(ink))
        derived['color_surface_light'] = rgb_to_hex(*hsl_to_rgb(h, 0.06, 0.92))
    if 'color_surface_white' not in v:
        h, _, _ = rgb_to_hsl(*hex_to_rgb(ink))
        derived['color_surface_white'] = rgb_to_hex(*hsl_to_rgb(h, 0.04, 0.98))

    # Ensure text_on_dark contrasts sufficiently against surface_deep
    surface_deep = v.get('color_surface_deep', ULTRA_PRO_DEFAULTS['color_surface_deep'])
    text_on_dark = v.get('color_text_on_dark', ULTRA_PRO_DEFAULTS['color_text_on_dark'])
    cr = contrast_ratio(text_on_dark, surface_deep)
    if cr < 7.0:
        # auto-lighten text_on_dark until it passes AAA
        for factor in [1.05, 1.1, 1.15, 1.2]:
            candidate = adjust_lightness(text_on_dark, factor)
            if contrast_ratio(candidate, surface_deep) >= 7.0:
                derived['color_text_on_dark'] = candidate
                break

    return derived


# ═══════════════════════════════════════════════════════════════════
# DESIGN INTELLIGENCE — VALIDATE CONTRAST
# ═══════════════════════════════════════════════════════════════════

def validate_contrast(tokens, label='Design System'):
    """Check critical text/background combos for WCAG AA (4.5:1) compliance."""
    colors = tokens.get('color', {})
    warnings = []
    checks = [
        ('text-primary on light bg', colors.get('text-primary'), colors.get('surface-light')),
        ('text-secondary on light bg', colors.get('text-secondary'), colors.get('surface-light')),
        ('text-primary on white bg', colors.get('text-primary'), colors.get('surface-white')),
        ('text-on-dark on deep bg', colors.get('text-on-dark'), colors.get('surface-deep')),
        ('text-on-dark on mid bg', colors.get('text-on-dark'), colors.get('surface-mid')),
    ]
    for name, fg, bg in checks:
        if not fg or not bg:
            continue
        cr = contrast_ratio(fg, bg)
        level = 'AAA' if cr >= 7.0 else ('AA' if cr >= 4.5 else 'FAIL')
        if level == 'FAIL':
            warnings.append(f'  [FAIL] {name}: {cr:.1f}:1 (need >=4.5)')
        elif level == 'AA':
            warnings.append(f'  [WARN] {name}: {cr:.1f}:1 (AA ok, AAA >=7.0)')
    if warnings:
        print(f'[CONTRAST] {label}:')
        for w in warnings:
            print(w)
    return warnings


# ═══════════════════════════════════════════════════════════════════
# DESIGN INTELLIGENCE — ENRICH PRESETS
# ═══════════════════════════════════════════════════════════════════

def _has_hover(preset, key='transform'):
    if 'decoration' not in preset:
        return False
    return key in preset.get('decoration', {}).get('hover', {})

def _get_font_size(text_preset):
    for key in ('headingFont', 'bodyFont'):
        group = text_preset.get(key, {})
        for tag in group.values():
            font_data = tag.get('font', {})
            for bp in font_data.values():
                val = bp.get('value', {})
                if 'size' in val:
                    return val['size']
    return None

def _is_heading_preset(name):
    return name in ('hero-title', 'display-xl', 'display-md', 'display-md-light',
                     'headline', 'headline-light', 'headline-3', 'stat-num')

def _is_interactive_module(name):
    return name in ('card', 'feature-card', 'glass-card', 'stat-item',
                     'testimonial-card', 'image-shadow')

CLAMP_PRESETS = {
    'hero-title':      ('2.5rem', '5vw + 0.5rem', '5rem'),
    'display-xl':      ('2.25rem', '4.5vw + 0.45rem', '4.5rem'),
    'display-md':      ('2rem', '3vw + 0.8rem', '3.5rem'),
    'display-md-light':('2rem', '3vw + 0.8rem', '3.5rem'),
    'headline':        ('1.5rem', '2vw + 0.7rem', '2.5rem'),
    'headline-light':  ('1.5rem', '2vw + 0.7rem', '2.5rem'),
    'headline-3':      ('1.3125rem', '0.88vw + 0.96rem', '1.75rem'),
    'stat-num':        ('1.75rem', '2.5vw + 0.75rem', '3rem'),
}

HOVER_TRANSFORMS = {
    'card':             {'translateY': '-4px'},
    'feature-card':     {'translateY': '-8px'},
    'glass-card':       {'translateY': '-6px'},
    'stat-item':        {'translateY': '-2px'},
    'testimonial-card': {'translateY': '-4px'},
    'image-shadow':     {'scale': '1.02'},
}

DEFAULT_DIVIDER_PRESETS = {
    'curve-top': {
        'decoration': {
            'shapeDivider': {
                'top': {
                    'desktop': {'value': {'style': 'curve', 'height': '100px', 'flip': 'off', 'invert': 'on'}},
                    'tablet': {'value': {'height': '60px'}},
                    'phone': {'value': {'height': '40px'}}
                }
            }
        }
    },
    'curve-bottom': {
        'decoration': {
            'shapeDivider': {
                'bottom': {
                    'desktop': {'value': {'style': 'curve', 'height': '100px', 'flip': 'off', 'invert': 'off'}},
                    'tablet': {'value': {'height': '60px'}},
                    'phone': {'value': {'height': '40px'}}
                }
            }
        }
    },
    'wave-top': {
        'decoration': {
            'shapeDivider': {
                'top': {
                    'desktop': {'value': {'style': 'wave', 'height': '80px', 'flip': 'off', 'invert': 'off'}},
                    'tablet': {'value': {'height': '50px'}},
                    'phone': {'value': {'height': '30px'}}
                }
            }
        }
    },
    'wave-bottom': {
        'decoration': {
            'shapeDivider': {
                'bottom': {
                    'desktop': {'value': {'style': 'wave', 'height': '80px', 'flip': 'off', 'invert': 'off'}},
                    'tablet': {'value': {'height': '50px'}},
                    'phone': {'value': {'height': '30px'}}
                }
            }
        }
    },
    'tilt-top': {
        'decoration': {
            'shapeDivider': {
                'top': {
                    'desktop': {'value': {'style': 'tilt', 'height': '80px', 'flip': 'off', 'invert': 'off'}},
                    'phone': {'value': {'height': '40px'}}
                }
            }
        }
    }
}

DEFAULT_GLASS_CARD = {
    'decoration': {
        'background': {'desktop': {'value': {'color': '{{design:color:surface-white}}12', 'backdropFilter': 'blur(12px)', 'backdropFilterSupported': 'on'}}},
        'border': {'desktop': {'value': {'radius': {'sync': 'on'}, 'styles': {'all': {'style': 'solid', 'width': '1px'}}}}},
        'boxShadow': {'desktop': {'value': {'horizontal': '0px', 'vertical': '8px', 'blur': '32px', 'spread': '0px'}}},
        'transform': {'hover': {'value': {'translateY': '-6px'}}},
        'spacing': {'desktop': {'value': {'padding': {'sync': 'on'}}}},
        'animation': {'desktop': {'value': {'style': 'fade', 'duration': '600ms', 'delay': '60ms'}}}
    }
}

DEFAULT_ANIMATIONS = {
    'fade-in':      {'decoration': {'animation': {'desktop': {'value': {'style': 'fade', 'duration': '800ms', 'delay': '0ms', 'speedCurve': 'ease-out'}}}}},
    'fade-in-fast': {'decoration': {'animation': {'desktop': {'value': {'style': 'fade', 'duration': '400ms', 'delay': '0ms', 'speedCurve': 'ease-out'}}}}},
    'slide-up':     {'decoration': {'animation': {'desktop': {'value': {'style': 'slide', 'direction': 'bottom', 'duration': '600ms', 'intensity': {'slide': '15%'}, 'startingOpacity': '0%', 'speedCurve': 'ease-out'}}}}},
    'slide-down':   {'decoration': {'animation': {'desktop': {'value': {'style': 'slide', 'direction': 'top', 'duration': '600ms', 'intensity': {'slide': '15%'}, 'startingOpacity': '0%', 'speedCurve': 'ease-out'}}}}},
    'slide-left':   {'decoration': {'animation': {'desktop': {'value': {'style': 'slide', 'direction': 'right', 'duration': '600ms', 'intensity': {'slide': '15%'}, 'startingOpacity': '0%', 'speedCurve': 'ease-out'}}}}},
    'slide-right':  {'decoration': {'animation': {'desktop': {'value': {'style': 'slide', 'direction': 'left', 'duration': '600ms', 'intensity': {'slide': '15%'}, 'startingOpacity': '0%', 'speedCurve': 'ease-out'}}}}},
    'reveal-up':    {'decoration': {'animation': {'desktop': {'value': {'style': 'slide', 'direction': 'bottom', 'duration': '700ms', 'intensity': {'slide': '25%'}, 'startingOpacity': '0%', 'speedCurve': 'ease-out'}}}}},
    'zoom-in':      {'decoration': {'animation': {'desktop': {'value': {'style': 'zoom', 'direction': 'in', 'duration': '600ms', 'startingOpacity': '0%', 'speedCurve': 'ease-out'}}}}},
    'bounce-up':    {'decoration': {'animation': {'desktop': {'value': {'style': 'bounce', 'direction': 'bottom', 'duration': '800ms', 'speedCurve': 'ease-out'}}}}},
    'flip':         {'decoration': {'animation': {'desktop': {'value': {'style': 'flip', 'direction': 'bottom', 'duration': '600ms', 'speedCurve': 'ease-out'}}}}},
    'fold':         {'decoration': {'animation': {'desktop': {'value': {'style': 'fold', 'direction': 'bottom', 'duration': '500ms', 'speedCurve': 'ease-out'}}}}},
    'roll':         {'decoration': {'animation': {'desktop': {'value': {'style': 'roll', 'direction': 'bottom', 'duration': '600ms', 'speedCurve': 'ease-out'}}}}},
}

DEFAULT_SCROLL = {
    'fade-in':      {'decoration': {'scroll': {'desktop': {'value': {'style': 'fade', 'duration': '1000ms'}}}}},
    'parallax-up':  {'decoration': {'scroll': {'desktop': {'value': {'style': 'slide', 'direction': 'bottom', 'speed': 'medium'}}}}},
    'parallax-down':{'decoration': {'scroll': {'desktop': {'value': {'style': 'slide', 'direction': 'top', 'speed': 'medium'}}}}},
    'scale-in':     {'decoration': {'scroll': {'desktop': {'value': {'style': 'scale', 'duration': '800ms'}}}}},
    'reveal':       {'decoration': {'scroll': {'desktop': {'value': {'style': 'slide', 'direction': 'bottom', 'duration': '600ms', 'startingOpacity': '0%'}}}}},
    'rotate':       {'decoration': {'scroll': {'desktop': {'value': {'style': 'rotate', 'duration': '800ms'}}}}},
    'blur-in':      {'decoration': {'scroll': {'desktop': {'value': {'style': 'blur', 'duration': '800ms'}}}}},
}

DEFAULT_TRANSFORMS = {
    'hover-lift':     {'decoration': {'transform': {'hover': {'value': {'translateY': '-8px'}}}}},
    'hover-scale':    {'decoration': {'transform': {'hover': {'value': {'scale': {'x': '1.03', 'y': '1.03'}, 'origin': {'x': '50%', 'y': '50%'}}}}}},
    'hover-glow':     {'decoration': {'transform': {'hover': {'value': {'translateY': '-4px'}}}}},
    'hover-slide-up': {'decoration': {'transform': {'hover': {'value': {'translate': {'y': '-8px'}}}}}},
    'hover-expand':   {'decoration': {'transform': {'hover': {'value': {'scale': {'x': '1.03', 'y': '1.03'}, 'origin': {'x': '50%', 'y': '50%'}}}}}},
}


def enrich_presets(presets, tokens=None):
    """Intelligently enrich preset categories with premium defaults.
    
    - Add clamp() fluid typography to heading presets with fixed px
    - Add hover states to interactive module presets that lack them
    - Ensure divider presets exist
    - Ensure glass-card exists
    - Add radial glows/auras to dark sections (hero-dark, cta-epic, dark)
    - Add micro-typography (letter-spacing negative, line-height tight) to display headings
    """
    enriched = []
    
    # Ensure all categories exist
    for cat in PRESET_CATEGORIES:
        if cat not in presets:
            presets[cat] = {}
            enriched.append(f'  + Created empty category: {cat}')

    # ── SECTION: glows/auras to dark sections ──
    if 'section' in presets:
        dark_glows = {
            'hero-dark': 'radial-gradient(circle at 80% 20%, rgba(166,124,64,0.06) 0%, transparent 60%)',
            'cta-epic': 'radial-gradient(circle at 20% 80%, rgba(166,124,64,0.05) 0%, transparent 50%)',
            'dark': 'radial-gradient(circle at 50% 50%, rgba(166,124,64,0.04) 0%, transparent 70%)',
        }
        for name, glow in dark_glows.items():
            if name in presets['section']:
                preset = presets['section'][name]
                if 'decoration' not in preset:
                    preset['decoration'] = {}
                if 'background' not in preset['decoration']:
                    preset['decoration']['background'] = {'desktop': {'value': {}}}
                
                bg_val = preset['decoration']['background']['desktop'].get('value', {})
                if 'overlay' not in bg_val:
                    bg_val['overlay'] = {'gradient': glow}
                    preset['decoration']['background']['desktop']['value'] = bg_val
                    enriched.append(f'  + Added radial glow (aura) -> section:{name}')

    # ── TEXT: clamp() fluid typography & micro-typography (letter-spacing) ──
    if 'text' in presets:
        for name, preset in presets['text'].items():
            # Fluid clamp()
            if name in CLAMP_PRESETS:
                current_size = _get_font_size(preset)
                if current_size and 'clamp' not in current_size and current_size.endswith('px'):
                    size_val = int(current_size.replace('px', ''))
                    if size_val >= 28:
                        min_s, pref_s, max_s = CLAMP_PRESETS[name]
                        for key in ('headingFont', 'bodyFont'):
                            group = preset.get(key, {})
                            for tag in group.values():
                                font_data = tag.get('font', {})
                                for bp in font_data.values():
                                    val = bp.get('value', {})
                                    if 'size' in val and val['size'] == current_size:
                                        val['size'] = f'clamp({min_s}, {pref_s}, {max_s})'
                                        for bp_key in ('tablet', 'phone'):
                                            if bp_key in font_data:
                                                bp_val = font_data[bp_key].get('value', {})
                                                if 'size' in bp_val:
                                                    del bp_val['size']
                                        enriched.append(f'  + Fluid clamp() -> text:{name}')
                                        break
            
            # Micro-typography: Letter-spacing & line-height adjustments for headings
            if _is_heading_preset(name):
                # Apply letter-spacing and line-height tweaks for premium look
                for key in ('headingFont', 'bodyFont'):
                    group = preset.get(key, {})
                    for tag in group.values():
                        font_data = tag.get('font', {})
                        if 'desktop' in font_data:
                            val = font_data['desktop'].get('value', {})
                            
                            # Tighter line height for large headings
                            if 'lineHeight' not in val:
                                val['lineHeight'] = '1.05' if 'title' in name or 'xl' in name else '1.15'
                                enriched.append(f'  + Line-height compression ({val["lineHeight"]}) -> text:{name}')
                                
                            # Negative letter spacing to give Vercel/Apple premium look
                            if 'letterSpacing' not in val:
                                val['letterSpacing'] = '-0.02em' if 'title' in name or 'xl' in name else '-0.015em'
                                enriched.append(f'  + Negative letter-spacing ({val["letterSpacing"]}) -> text:{name}')

    # ── MODULE: hover states ──
    if 'module' in presets:
        for name, preset in presets['module'].items():
            if name in HOVER_TRANSFORMS and not _has_hover(preset):
                if 'decoration' not in preset:
                    preset['decoration'] = {}
                if 'transform' not in preset['decoration']:
                    preset['decoration']['transform'] = {}
                if 'hover' not in preset['decoration']['transform']:
                    preset['decoration']['transform']['hover'] = {'value': HOVER_TRANSFORMS[name]}
                    enriched.append(f'  + Hover state -> module:{name}')

    # ── DIVIDER: ensure defaults ──
    if 'divider' in presets and len(presets['divider']) == 0:
        presets['divider'] = copy.deepcopy(DEFAULT_DIVIDER_PRESETS)
        enriched.append(f'  + 5 SVG divider presets (defaults)')

    # ── MODULE: glass-card if missing ──
    if 'module' in presets and 'glass-card' not in presets['module']:
        radius = tokens.get('radius', {}).get('lg', '8px') if tokens else '8px'
        glass = copy.deepcopy(DEFAULT_GLASS_CARD)
        glass['decoration']['border']['desktop']['value']['radius']['topLeft'] = radius
        glass['decoration']['border']['desktop']['value']['radius']['topRight'] = radius
        glass['decoration']['border']['desktop']['value']['radius']['bottomRight'] = radius
        glass['decoration']['border']['desktop']['value']['radius']['bottomLeft'] = radius
        space = tokens.get('space', {}).get('lg', '40px') if tokens else '40px'
        glass['decoration']['spacing']['desktop']['value']['padding']['top'] = space
        glass['decoration']['spacing']['desktop']['value']['padding']['right'] = space
        glass['decoration']['spacing']['desktop']['value']['padding']['bottom'] = space
        glass['decoration']['spacing']['desktop']['value']['padding']['left'] = space
        presets['module']['glass-card'] = glass
        enriched.append(f'  + module:glass-card (auto-generated)')

    # ── ANIMATION: ensure defaults ──
    if 'animation' in presets and len(presets['animation']) < 4:
        for name, anim in DEFAULT_ANIMATIONS.items():
            if name not in presets['animation']:
                presets['animation'][name] = copy.deepcopy(anim)
        enriched.append(f'  + {len(DEFAULT_ANIMATIONS)} animation presets (defaults)')

    # ── SCROLL: ensure defaults ──
    if 'scroll' in presets and len(presets['scroll']) < 3:
        for name, sc in DEFAULT_SCROLL.items():
            if name not in presets['scroll']:
                presets['scroll'][name] = copy.deepcopy(sc)
        enriched.append(f'  + {len(DEFAULT_SCROLL)} scroll presets (defaults)')

    # ── TRANSFORM: ensure defaults ──
    if 'transform' in presets and len(presets['transform']) < 3:
        for name, tr in DEFAULT_TRANSFORMS.items():
            if name not in presets['transform']:
                presets['transform'][name] = copy.deepcopy(tr)
        enriched.append(f'  + {len(DEFAULT_TRANSFORMS)} transform presets (defaults)')

    if enriched:
        print(f'[ENRICH] Design intelligence applied:')
        for e in enriched:
            print(e)
    return presets


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
# MINIMAL VARIABLES (quick start for bibliotheca)
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
# HELPERS
# ═══════════════════════════════════════════════════════════════════

def _find_brand_file(filename):
    if not os.path.isdir(BRAND_DIR):
        return None
    # First check directly in BRAND_DIR root
    direct = os.path.join(BRAND_DIR, filename)
    if os.path.isfile(direct):
        return direct
    # Then check subdirectories
    for entry in sorted(os.listdir(BRAND_DIR)):
        candidate = os.path.join(BRAND_DIR, entry, filename)
        if os.path.isfile(candidate):
            return candidate
    return None

def substitute(obj, vars_dict):
    if isinstance(obj, str):
        if '{{' in obj:
            for k, v in vars_dict.items():
                obj = obj.replace('{{' + k + '}}', str(v))
        return obj
    elif isinstance(obj, dict):
        return {k: substitute(v, vars_dict) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [substitute(i, vars_dict) for i in obj]
    return obj


# ═══════════════════════════════════════════════════════════════════
# BUILD: TOKENS (auto-discovered by prefix)
# ═══════════════════════════════════════════════════════════════════

def build_tokens(v):
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
    return {'color': colors, 'font': fonts, 'radius': radii, 'space': spaces}


# ═══════════════════════════════════════════════════════════════════
# BUILD: CUSTOMIZER
# ═══════════════════════════════════════════════════════════════════

def build_customizer(v):
    mapping = {}
    for key, val in v.items():
        if key.startswith('customizer_'):
            mapping[key[11:]] = val
    return mapping


# ═══════════════════════════════════════════════════════════════════
# BUILD: PRESETS (load from file or auto-generate)
# ═══════════════════════════════════════════════════════════════════

def load_presets(path=None):
    if path is None:
        path = _find_brand_file('_design_presets.json')
    if not path or not os.path.exists(path):
        print(f'[OK] No presets file found — will auto-generate premium defaults.')
        return {}
    with open(path, encoding='utf-8') as f:
        presets = json.load(f)
    missing = PRESET_CATEGORIES - set(presets.keys())
    if missing:
        print(f'[OK] Presets file loaded from: {path}')
        print(f'[INFO] Missing categories (will be auto-generated): {", ".join(sorted(missing))}')
    else:
        print(f'[OK] Presets file loaded from: {path}')
    return presets


# ═══════════════════════════════════════════════════════════════════
# BUILD: COMPLETE SCHEMA
# ═══════════════════════════════════════════════════════════════════

def build_complete_schema(v, presets_path=None, enrich=True):
    tokens = build_tokens(v)
    presets = load_presets(presets_path)
    
    if enrich:
        presets = enrich_presets(presets, tokens)
    
    schema = {
        'name': v.get('brand_name', 'Design System'),
        'description': v.get('brand_description', ''),
        'tokens': tokens,
        'customizer': build_customizer(v),
        'presets': presets,
    }
    schema = substitute(schema, v)
    return schema


# ═══════════════════════════════════════════════════════════════════
# RESOLVE VARIABLES
# ═══════════════════════════════════════════════════════════════════

def auto_correct_colors(v):
    """Adjust colors to actively guarantee at least WCAG AA (4.5:1) contrast."""
    # 1. Contrast: text_primary vs surface_light
    surface_light = v.get('color_surface_light', ULTRA_PRO_DEFAULTS['color_surface_light'])
    text_primary = v.get('color_text_primary', ULTRA_PRO_DEFAULTS['color_text_primary'])
    cr1 = contrast_ratio(text_primary, surface_light)
    if cr1 < 4.5:
        for factor in [0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3]:
            candidate = adjust_lightness(text_primary, factor)
            if contrast_ratio(candidate, surface_light) >= 4.5:
                v['color_text_primary'] = candidate
                break

    # 2. Contrast: text_secondary vs surface_light
    text_secondary = v.get('color_text_secondary', ULTRA_PRO_DEFAULTS['color_text_secondary'])
    cr2 = contrast_ratio(text_secondary, surface_light)
    if cr2 < 4.5:
        for factor in [0.85, 0.75, 0.65, 0.55, 0.45, 0.35]:
            candidate = adjust_lightness(text_secondary, factor)
            if contrast_ratio(candidate, surface_light) >= 4.5:
                v['color_text_secondary'] = candidate
                break

    # 3. Contrast: text_on_dark vs surface_deep
    surface_deep = v.get('color_surface_deep', ULTRA_PRO_DEFAULTS['color_surface_deep'])
    text_on_dark = v.get('color_text_on_dark', ULTRA_PRO_DEFAULTS['color_text_on_dark'])
    cr3 = contrast_ratio(text_on_dark, surface_deep)
    if cr3 < 4.5:
        for factor in [1.15, 1.25, 1.35, 1.45, 1.55, 1.65, 1.75]:
            candidate = adjust_lightness(text_on_dark, factor)
            if contrast_ratio(candidate, surface_deep) >= 4.5:
                v['color_text_on_dark'] = candidate
                break

    # 4. Contrast: text_on_dark vs surface_mid
    surface_mid = v.get('color_surface_mid', ULTRA_PRO_DEFAULTS['color_surface_mid'])
    cr4 = contrast_ratio(text_on_dark, surface_mid)
    if cr4 < 4.5:
        for factor in [1.15, 1.25, 1.35, 1.45, 1.55, 1.65, 1.75]:
            candidate = adjust_lightness(text_on_dark, factor)
            if contrast_ratio(candidate, surface_mid) >= 4.5:
                v['color_text_on_dark'] = candidate
                break

    return v

def resolve_variables(user_vars=None):
    resolved = dict(ULTRA_PRO_DEFAULTS)
    if user_vars:
        for k, v in user_vars.items():
            if v is not None and v != '':
                resolved[k] = v
    # Apply design intelligence: derive missing colors
    derived = derive_color_variants(resolved)
    for k, v in derived.items():
        if k not in resolved or resolved[k] == ULTRA_PRO_DEFAULTS.get(k):
            resolved[k] = v
    # Actively fix contrast conflicts
    resolved = auto_correct_colors(resolved)
    return resolved


# ═══════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description='Divi 5 Design System Builder — v3.0 (design intelligence)',
        epilog='Design intelligence: color derivation, WCAG validation, clamp(), hover states, defaults')
    parser.add_argument('--vars', '-v', type=str, default=None,
                        help='Path to JSON variables file')
    parser.add_argument('--presets', '-p', type=str, default=None,
                        help='Path to JSON presets file')
    parser.add_argument('--out', '-o', type=str, default=None,
                        help='Output path')
    parser.add_argument('--minimal', '-m', action='store_true',
                        help='Use built-in minimal variables')
    parser.add_argument('--no-enrich', action='store_true',
                        help='Skip design intelligence layer')
    parser.add_argument('--validate-only', action='store_true',
                        help='Validate contrast only, do not write output')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Minimal output')
    args = parser.parse_args()
    quiet = args.quiet

    # ── Load variables ──
    user_vars = {}
    if args.vars:
        with open(args.vars, encoding='utf-8') as f:
            user_vars = json.load(f)
        if not quiet: print(f'[OK] Loaded variables from: {args.vars}')
    elif args.minimal:
        user_vars = dict(MINIMAL_VARS)
        if not quiet: print('[OK] Using minimal variables (quick start mode).')
    else:
        default_vars_path = _find_brand_file('_design_vars.json')
        if default_vars_path and os.path.exists(default_vars_path):
            with open(default_vars_path, encoding='utf-8') as f:
                user_vars = json.load(f)
            if not quiet: print(f'[OK] Loaded variables from: {default_vars_path}')
        else:
            if not quiet: print('[OK] Using ultra-pro defaults (no vars file found).')

    v = resolve_variables(user_vars)
    derived_count = sum(1 for k in v if k not in user_vars and k.startswith('color_'))
    if derived_count > 0 and not quiet:
        print(f'[COLORS] Derived {derived_count} missing color variants from accent')

    # ── Build schema ──
    schema = build_complete_schema(v, presets_path=args.presets, enrich=not args.no_enrich)

    # ── Validate ──
    contrast_warnings = validate_contrast(schema.get('tokens', {}), label=schema.get('name', 'Design System'))

    has_issues = len(contrast_warnings) > 0

    if args.validate_only:
        if has_issues:
            print('')
            print(f'[VALIDATE] Issues found — review contrast warnings above.')
        else:
            if not quiet: print(f'[VALIDATE] All AA contrast checks passed.')
        return

    # ── Write output ──
    out_path = args.out or OUT_PATH
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)

    # ── Stats ──
    tokens = schema.get('tokens', {})
    presets = schema.get('presets', {})
    total_tokens = sum(len(v) for v in tokens.values())
    total_presets = sum(len(v) for v in presets.values())
    vars_used = sum(1 for k in v if k in list(user_vars.keys()) + list(ULTRA_PRO_DEFAULTS.keys()))

    if not quiet:
        print(f'')
        print(f'[OK] Design system generated: {out_path}')
        print(f'    Name: {schema.get("name")}')
        print(f'    Tokens: {total_tokens} ({", ".join(f"{k}: {len(v)}" for k, v in tokens.items())})')
        print(f'    Presets: {total_presets} total')
        for cat, pset in sorted(presets.items()):
            print(f'      - {cat}: {len(pset)}')
        print(f'    Variables used: {vars_used}')
        if has_issues:
            print(f'    [!] Contrast issues: {len(contrast_warnings)}')
        print(f'')
        print(f'    Usage: wp agentic global_colors sync --design-system="{out_path}"')


if __name__ == '__main__':
    main()
