"""Pattern Dictionary — Premium visual compositions for Divi 5.

Transforms UX-Pro style classifications into Divi-native decoration JSON.
Every pattern produces multi-layer compositions with depth, atmosphere, and
visual rhythm. No flat single-color backgrounds. No invisible cards.

Architecture:
  zone_system(section_type, index) → {zone, text_context, container_width}
  compose_background(zone_type) → decoration with composite bg (gradient overlays, radial accents)
  card_system(card_style, is_dark_zone) → {base, hover} with lift, shadow escalation, backdrop blur
  eyebrow_pill(is_dark_zone) → pill background with accent tint, border, letter-spacing
  heading_decoration(level, zone) → fluid type scale with zone-aware colors
  stagger_delay(index, total) → progressive reveal animation timing
  get_zone_divider(current, prev) → shape divider between contrast zones
"""

from typing import Any, Dict, List, Optional, Tuple


# ═══════════════════════════════════════════════════════════════════════════
# ZONE SYSTEM — Visual alternation with rhythm and contrast
# ═══════════════════════════════════════════════════════════════════════════

_ZONE_MAPS = {
    "academic_night": {
        "hero": "dark_gradient",
        "trust-bar": "transparent",
        "features": "light_composite",
        "content": "light",
        "stats": "strip_float",
        "team": "dark",
        "process": "light_alt",
        "testimonials": "dark_accent",
        "gallery": "light",
        "pricing": "dark",
        "faq": "light_alt",
        "contact": "dark_gradient",
        "cta": "dark_gradient",
    },
    "cool_luxury": {
        "hero": "dark_gradient",
        "trust-bar": "transparent",
        "features": "light_composite",
        "content": "light",
        "stats": "strip_float",
        "team": "dark",
        "process": "light_alt",
        "testimonials": "dark_accent",
        "gallery": "light",
        "pricing": "light_composite",
        "faq": "light_alt",
        "contact": "dark",
        "cta": "dark_gradient",
    },
    "warm_minimal": {
        "hero": "dark_gradient",
        "trust-bar": "transparent",
        "features": "light_composite",
        "content": "light_alt",
        "stats": "strip_float",
        "team": "light",
        "process": "light_alt",
        "testimonials": "dark",
        "gallery": "light_composite",
        "pricing": "light",
        "faq": "light_alt",
        "contact": "dark_accent",
        "cta": "dark_gradient",
    },
    "tech_glass": {
        "hero": "dark_orbs",
        "trust-bar": "transparent",
        "features": "dark_glass",
        "content": "dark",
        "stats": "strip_float_dark",
        "team": "dark_glass",
        "process": "dark_accent",
        "testimonials": "dark",
        "gallery": "dark",
        "pricing": "dark_glass",
        "faq": "dark",
        "contact": "dark_orbs",
        "cta": "dark_gradient",
    },
    "organic_modern": {
        "hero": "dark_gradient",
        "trust-bar": "transparent",
        "features": "light_composite",
        "content": "light_alt",
        "stats": "strip_float",
        "team": "light",
        "process": "light",
        "testimonials": "dark_accent",
        "gallery": "light",
        "pricing": "light",
        "faq": "light_alt",
        "contact": "dark",
        "cta": "dark_gradient",
    },
}

_CONTAINER_WIDTHS = {
    "dark_gradient": "1100px",
    "dark_orbs": "1100px",
    "dark": "1100px",
    "dark_accent": "1100px",
    "dark_glass": "1100px",
    "light_composite": "1100px",
    "light": "1200px",
    "light_alt": "1100px",
    "transparent": "1200px",
    "strip_float": "960px",
    "strip_float_dark": "960px",
}

_TEXT_COLORS = {
    "dark_gradient": {"heading": "text_on_dark", "body": "text_on_dark_muted", "eyebrow": "accent"},
    "dark_orbs": {"heading": "text_on_dark", "body": "text_on_dark_muted", "eyebrow": "accent"},
    "dark": {"heading": "text_on_dark", "body": "text_on_dark_muted", "eyebrow": "accent"},
    "dark_accent": {"heading": "text_on_dark", "body": "text_on_dark_muted", "eyebrow": "accent"},
    "dark_glass": {"heading": "text_on_dark", "body": "text_on_dark_muted", "eyebrow": "accent"},
    "light_composite": {"heading": "text_on_light", "body": "text_secondary", "eyebrow": "accent"},
    "light": {"heading": "text_on_light", "body": "text_secondary", "eyebrow": "accent"},
    "light_alt": {"heading": "text_on_light", "body": "text_secondary", "eyebrow": "accent"},
    "transparent": {"heading": "text_on_dark", "body": "text_on_dark_muted", "eyebrow": "accent"},
    "strip_float": {"heading": "text_on_light", "body": "text_secondary", "eyebrow": "accent"},
    "strip_float_dark": {"heading": "text_on_dark", "body": "text_on_dark_muted", "eyebrow": "accent"},
}


def get_zone(profile, section_type: str, index: int = 0) -> Dict[str, Any]:
    mood = _get_mood(profile)
    zone_map = _ZONE_MAPS.get(mood, _ZONE_MAPS["cool_luxury"])
    zone = zone_map.get(section_type, "light")

    if zone == "transparent" and index == 0:
        zone = zone_map.get("hero", "dark_gradient")

    text_ctx = _TEXT_COLORS.get(zone, _TEXT_COLORS["light"])
    width = _CONTAINER_WIDTHS.get(zone, "1100px")

    return {
        "zone": zone,
        "text_context": text_ctx,
        "container_width": width,
        "index": index,
    }


def _get_mood(profile) -> str:
    # 1. Mood explícito del profile (seteado por get_profile desde design_direction)
    mood = getattr(profile, 'mood', '')
    if mood and mood in ("academic_night", "cool_luxury", "warm_minimal", "tech_glass", "organic_modern"):
        return mood

    # 2. Fallback: inferir desde layout hints
    if hasattr(profile, 'hero_layout'):
        layouts = {
            "asymmetric": "tech_glass",
            "2_5_3_5": "academic_night",
        }
        layout = getattr(profile, 'about_layout', 'centered')
        if layout in layouts:
            return layouts[layout]

    # 3. Fallback: inferir desde hex colors
    dark = getattr(profile, 'bg_dark', '')
    if '#0A0A' in dark or '#0505' in dark:
        return "tech_glass"
    if '#0A0E' in dark:
        return "academic_night"
    if '#2D2A' in dark:
        return "warm_minimal"
    if '#1B2A' in dark or '#1A2E' in dark:
        return "organic_modern"
    if '#1C19' in dark or '#211D' in dark:
        return "cool_luxury"

    return "cool_luxury"


# ═══════════════════════════════════════════════════════════════════════════
# COMPOSITE BACKGROUND SYSTEM — Rich multi-layer compositions
# Reference: UX-Pro Liquid Glass, Aurora, Dimensional Layering, Bento Grids
# ═══════════════════════════════════════════════════════════════════════════

def compose_background(profile, zone: str) -> Dict[str, Any]:
    bg_dark = getattr(profile, 'bg_dark', '#1C1917')
    bg_light = getattr(profile, 'bg_light', '#F5F7FA')
    bg_mid = getattr(profile, 'bg_mid', '#211D1B')
    accent = getattr(profile, 'accent', '#0071E3')
    accent_hover = getattr(profile, 'accent_hover', '#005FCE')
    section_pad_top = getattr(profile, 'section_padding_top', '120px')
    section_pad_bottom = getattr(profile, 'section_padding_bottom', '120px')
    hero_pad_top = getattr(profile, 'hero_padding_top', '180px')
    hero_pad_bottom = getattr(profile, 'hero_padding_bottom', '160px')
    content_pad_top = getattr(profile, 'section_padding_top', '100px')
    content_pad_bottom = getattr(profile, 'section_padding_bottom', '100px')

    ctx = {
        "bg_dark": bg_dark, "bg_light": bg_light, "bg_mid": bg_mid,
        "accent": accent, "accent_hover": accent_hover,
        "section_pad_top": section_pad_top, "section_pad_bottom": section_pad_bottom,
        "hero_pad_top": hero_pad_top, "hero_pad_bottom": hero_pad_bottom,
        "content_pad_top": content_pad_top, "content_pad_bottom": content_pad_bottom,
    }

    builders = {
        "dark_gradient": _bg_dark_gradient,
        "dark_orbs": _bg_dark_orbs,
        "dark": _bg_dark_solid,
        "dark_accent": _bg_dark_accent,
        "dark_glass": _bg_dark_glass,
        "light_composite": _bg_light_composite,
        "light": _bg_light_solid,
        "light_alt": _bg_light_alt,
        "transparent": _bg_transparent,
        "strip_float": _bg_strip_float,
        "strip_float_dark": _bg_strip_float_dark,
    }

    builder = builders.get(zone, _bg_light_solid)
    return builder(ctx)


def _bg_dark_gradient(ctx: dict) -> Dict[str, Any]:
    d, m, a = ctx["bg_dark"], ctx["bg_mid"], ctx["accent"]
    return {
        "background": {
            "desktop": {
                "value": {
                    "color": d,
                    "overlay": {
                        "gradient": f"linear-gradient(165deg, {d} 0%, {a}18 25%, {m}44 50%, {d}cc 75%, {d} 100%)"
                    },
                }
            }
        },
        "spacing": {
            "desktop": {
                "value": {
                    "padding": {"top": ctx["hero_pad_top"], "bottom": ctx["hero_pad_bottom"], "right": "0", "left": "0"},
                }
            }
        },
        "animation": {
            "desktop": {
                "value": {
                    "style": "fade",
                    "duration": "800ms",
                    "delay": "0ms",
                    "speedCurve": "ease-out",
                }
            }
        },
    }


def _bg_dark_orbs(ctx: dict) -> Dict[str, Any]:
    d, m, a = ctx["bg_dark"], ctx["bg_mid"], ctx["accent"]
    return {
        "background": {
            "desktop": {
                "value": {
                    "color": d,
                    "overlay": {
                        "gradient": f"radial-gradient(ellipse at 20% 50%, {a}30 0%, transparent 50%), radial-gradient(ellipse at 80% 20%, {m}66 0%, transparent 40%), linear-gradient(180deg, {d} 0%, {m}33 100%)"
                    },
                }
            }
        },
        "spacing": {
            "desktop": {
                "value": {
                    "padding": {"top": ctx["hero_pad_top"], "bottom": ctx["hero_pad_bottom"], "right": "0", "left": "0"},
                }
            }
        },
        "animation": {
            "desktop": {
                "value": {
                    "style": "fade",
                    "duration": "800ms",
                    "delay": "0ms",
                    "speedCurve": "ease-out",
                }
            }
        },
    }


def _bg_dark_solid(ctx: dict) -> Dict[str, Any]:
    return {
        "background": {
            "desktop": {
                "value": {
                    "color": ctx["bg_dark"],
                    "overlay": {
                        "gradient": f"linear-gradient(180deg, {ctx['bg_dark']} 0%, {ctx['bg_mid']}66 100%)"
                    },
                }
            }
        },
        "spacing": {
            "desktop": {
                "value": {
                    "padding": {"top": ctx["section_pad_top"], "bottom": ctx["section_pad_bottom"], "right": "0", "left": "0"},
                }
            }
        },
    }


def _bg_dark_accent(ctx: dict) -> Dict[str, Any]:
    d, m, a = ctx["bg_dark"], ctx["bg_mid"], ctx["accent"]
    return {
        "background": {
            "desktop": {
                "value": {
                    "color": d,
                    "overlay": {
                        "gradient": f"linear-gradient(135deg, {a}22 0%, {d} 40%, {m}88 100%)"
                    },
                }
            }
        },
        "spacing": {
            "desktop": {
                "value": {
                    "padding": {"top": ctx["section_pad_top"], "bottom": ctx["section_pad_bottom"], "right": "0", "left": "0"},
                }
            }
        },
    }


def _bg_dark_glass(ctx: dict) -> Dict[str, Any]:
    d, m = ctx["bg_dark"], ctx["bg_mid"]
    return {
        "background": {
            "desktop": {
                "value": {
                    "color": d,
                    "overlay": {
                        "gradient": f"linear-gradient(180deg, {d}cc 0%, {m}44 50%, {d}cc 100%)"
                    },
                }
            }
        },
        "spacing": {
            "desktop": {
                "value": {
                    "padding": {"top": ctx["section_pad_top"], "bottom": ctx["section_pad_bottom"], "right": "0", "left": "0"},
                }
            }
        },
    }


def _bg_light_composite(ctx: dict) -> Dict[str, Any]:
    l, m = ctx["bg_light"], ctx["bg_mid"]
    return {
        "background": {
            "desktop": {
                "value": {
                    "color": l,
                    "overlay": {
                        "gradient": f"linear-gradient(180deg, {l} 0%, {m}18 35%, {l}aa 70%, {m}0d 100%)"
                    },
                }
            }
        },
        "spacing": {
            "desktop": {
                "value": {
                    "padding": {"top": ctx["section_pad_top"], "bottom": ctx["section_pad_bottom"], "right": "0", "left": "0"},
                }
            }
        },
    }


def _bg_light_solid(ctx: dict) -> Dict[str, Any]:
    return {
        "background": {
            "desktop": {
                "value": {
                    "color": ctx["bg_light"],
                }
            }
        },
        "spacing": {
            "desktop": {
                "value": {
                    "padding": {"top": ctx["section_pad_top"], "bottom": ctx["section_pad_bottom"], "right": "0", "left": "0"},
                }
            }
        },
    }


def _bg_light_alt(ctx: dict) -> Dict[str, Any]:
    alt = ctx["bg_mid"] if ctx["bg_mid"] != ctx["bg_light"] else "#EAEAEA"
    return {
        "background": {
            "desktop": {
                "value": {
                    "color": alt,
                    "overlay": {
                        "gradient": f"linear-gradient(180deg, {alt} 0%, {ctx['bg_light']}44 100%)"
                    },
                }
            }
        },
        "spacing": {
            "desktop": {
                "value": {
                    "padding": {"top": ctx["content_pad_top"], "bottom": ctx["content_pad_bottom"], "right": "0", "left": "0"},
                }
            }
        },
    }


def _bg_transparent(ctx: dict) -> Dict[str, Any]:
    return {
        "spacing": {
            "desktop": {
                "value": {
                    "padding": {"top": "0px", "bottom": "0px", "right": "0px", "left": "0px"},
                }
            }
        },
    }


def _bg_strip_float(ctx: dict) -> Dict[str, Any]:
    l, m = ctx["bg_light"], ctx["bg_mid"]
    return {
        "background": {
            "desktop": {
                "value": {
                    "color": "#FFFFFF",
                    "overlay": {
                        "gradient": f"linear-gradient(180deg, #FFFFFF 0%, {m}11 100%)"
                    },
                }
            }
        },
        "borderRadius": {
            "desktop": {
                "value": {
                    "topLeft": "24px",
                    "topRight": "24px",
                    "bottomRight": "24px",
                    "bottomLeft": "24px",
                }
            }
        },
        "boxShadow": {
            "desktop": {
                "value": {
                    "boxShadowHorizontal": "0px",
                    "boxShadowVertical": "20px",
                    "boxShadowBlur": "60px",
                    "boxShadowSpread": "0px",
                    "boxShadowColor": "rgba(0,0,0,0.08)",
                    "position": "outer",
                }
            }
        },
        "spacing": {
            "desktop": {
                "value": {
                    "padding": {"top": "56px", "bottom": "56px", "right": "32px", "left": "32px"},
                    "margin": {"top": "-80px"},
                }
            }
        },
    }


def _bg_strip_float_dark(ctx: dict) -> Dict[str, Any]:
    d, m = ctx["bg_dark"], ctx["bg_mid"]
    return {
        "background": {
            "desktop": {
                "value": {
                    "color": f"{m}",
                    "overlay": {
                        "gradient": f"linear-gradient(180deg, {m}cc 0%, {d}55 100%)"
                    },
                }
            }
        },
        "borderRadius": {
            "desktop": {
                "value": {
                    "topLeft": "24px",
                    "topRight": "24px",
                    "bottomRight": "24px",
                    "bottomLeft": "24px",
                }
            }
        },
        "boxShadow": {
            "desktop": {
                "value": {
                    "boxShadowHorizontal": "0px",
                    "boxShadowVertical": "20px",
                    "boxShadowBlur": "60px",
                    "boxShadowSpread": "0px",
                    "boxShadowColor": "rgba(0,0,0,0.25)",
                    "position": "outer",
                }
            }
        },
        "spacing": {
            "desktop": {
                "value": {
                    "padding": {"top": "56px", "bottom": "56px", "right": "32px", "left": "32px"},
                    "margin": {"top": "-80px"},
                }
            }
        },
    }


# ═══════════════════════════════════════════════════════════════════════════
# CARD SYSTEM — Bento-style with glass morphism, dimensional elevation
# Reference: UX-Pro Glassmorphism, Bento Grids, Dimensional Layering
# ═══════════════════════════════════════════════════════════════════════════

_CARD_STYLES = {
    "glass": {
        "light": {
            "bg": "rgba(255,255,255,0.72)",
            "border": "rgba(0,0,0,0.06)",
            "shadow": "0 4px 24px rgba(0,0,0,0.06)",
            "hover_shadow": "0 24px 48px rgba(0,0,0,0.12)",
            "hover_border": "rgba(0,113,227,0.15)",
            "hover_translate": "-6px",
            "backdrop_filter": True,
            "backdrop_blur": "20px",
            "backdrop_saturate": "1.4",
        },
        "dark": {
            "bg": "rgba(255,255,255,0.05)",
            "border": "rgba(255,255,255,0.10)",
            "shadow": "0 4px 24px rgba(0,0,0,0.25)",
            "hover_shadow": "0 20px 48px rgba(0,0,0,0.40)",
            "hover_border": "rgba(255,255,255,0.20)",
            "hover_translate": "-6px",
            "backdrop_filter": True,
            "backdrop_blur": "20px",
            "backdrop_saturate": "1.4",
        },
    },
    "solid": {
        "light": {
            "bg": "#FFFFFF",
            "border": "rgba(0,0,0,0.04)",
            "shadow": "0 2px 8px rgba(0,0,0,0.04)",
            "hover_shadow": "0 16px 40px rgba(0,0,0,0.10)",
            "hover_border": "rgba(0,0,0,0.08)",
            "hover_translate": "-4px",
            "backdrop_filter": False,
        },
        "dark": {
            "bg": "rgba(255,255,255,0.06)",
            "border": "rgba(255,255,255,0.08)",
            "shadow": "0 2px 16px rgba(0,0,0,0.20)",
            "hover_shadow": "0 16px 40px rgba(0,0,0,0.35)",
            "hover_border": "rgba(255,255,255,0.18)",
            "hover_translate": "-4px",
            "backdrop_filter": False,
        },
    },
    "outline": {
        "light": {
            "bg": "transparent",
            "border": "rgba(0,0,0,0.08)",
            "shadow": "none",
            "hover_shadow": "0 8px 32px rgba(0,0,0,0.08)",
            "hover_border": "rgba(0,0,0,0.16)",
            "hover_translate": "-3px",
            "backdrop_filter": False,
        },
        "dark": {
            "bg": "transparent",
            "border": "rgba(255,255,255,0.12)",
            "shadow": "none",
            "hover_shadow": "0 8px 32px rgba(0,0,0,0.25)",
            "hover_border": "rgba(255,255,255,0.28)",
            "hover_translate": "-3px",
            "backdrop_filter": False,
        },
    },
    "minimal": {
        "light": {
            "bg": "rgba(255,255,255,0.60)",
            "border": "rgba(0,0,0,0.04)",
            "shadow": "0 1px 4px rgba(0,0,0,0.03)",
            "hover_shadow": "0 8px 24px rgba(0,0,0,0.08)",
            "hover_border": "rgba(0,0,0,0.10)",
            "hover_translate": "-3px",
            "backdrop_filter": True,
            "backdrop_blur": "16px",
            "backdrop_saturate": "1.3",
        },
        "dark": {
            "bg": "rgba(255,255,255,0.03)",
            "border": "rgba(255,255,255,0.06)",
            "shadow": "0 1px 4px rgba(0,0,0,0.12)",
            "hover_shadow": "0 8px 24px rgba(0,0,0,0.28)",
            "hover_border": "rgba(255,255,255,0.14)",
            "hover_translate": "-3px",
            "backdrop_filter": True,
            "backdrop_blur": "16px",
            "backdrop_saturate": "1.3",
        },
    },
}


def card_system(profile, card_style: str = None, is_dark_zone: bool = False) -> Dict[str, Any]:
    if card_style is None:
        card_style = getattr(profile, 'card_style', 'glass')

    context = "dark" if is_dark_zone else "light"
    style_def = _CARD_STYLES.get(card_style, _CARD_STYLES["glass"]).get(context, _CARD_STYLES["glass"]["light"])
    accent = getattr(profile, 'accent', '#0071E3')
    radius = getattr(profile, 'card_border_radius', '16px')

    shadow_parts = style_def["shadow"].split(", ") if style_def.get("shadow") and style_def["shadow"] != "none" else None
    hover_shadow_parts = style_def["hover_shadow"].split(", ") if style_def.get("hover_shadow") and style_def["hover_shadow"] != "none" else None

    base = {
        "background": {"desktop": {"value": {"color": style_def["bg"]}}},
        "border": {
            "desktop": {
                "value": {
                    "radius": {"topLeft": radius, "topRight": radius, "bottomRight": radius, "bottomLeft": radius},
                    "styles": {"all": {"color": style_def["border"], "width": "1px"}},
                }
            }
        },
        "spacing": {"desktop": {"value": {"padding": {"top": "40px", "bottom": "40px", "left": "32px", "right": "32px"}}}},
    }

    if shadow_parts:
        base["boxShadow"] = {
            "desktop": {
                "value": {
                    "boxShadowHorizontal": "0px",
                    "boxShadowVertical": shadow_parts[1].strip() if len(shadow_parts) > 1 else "4px",
                    "boxShadowBlur": shadow_parts[2].strip() if len(shadow_parts) > 2 else "12px",
                    "boxShadowSpread": "0px",
                    "boxShadowColor": shadow_parts[4].strip() if len(shadow_parts) > 4 else "rgba(0,0,0,0.10)",
                    "position": "outer",
                }
            }
        }

    module_css = {}
    if style_def.get("backdrop_filter"):
        blur_val = style_def.get("backdrop_blur", "12px")
        saturate = style_def.get("backdrop_saturate", "1.3")
        module_css = {
            "desktop": {
                "value": {
                    "freeForm": f".selector {{\n  backdrop-filter: blur({blur_val}) saturate({saturate});\n  -webkit-backdrop-filter: blur({blur_val}) saturate({saturate});\n}}"
                }
            }
        }

    hover = {}
    hover_translate = style_def.get("hover_translate")
    if hover_translate:
        hover["transform"] = {
            "hover": {
                "value": {
                    "translate": {"y": hover_translate},
                    "scale": {"x": "1.01", "y": "1.01"},
                }
            }
        }

    hover_border_color = style_def.get("hover_border")
    if hover_border_color and hover_border_color != "transparent":
        hover["border"] = {
            "hover": {
                "value": {
                    "styles": {"all": {"color": hover_border_color}},
                }
            }
        }

    if hover_shadow_parts:
        hover["boxShadow"] = {
            "hover": {
                "value": {
                    "boxShadowHorizontal": "0px",
                    "boxShadowVertical": hover_shadow_parts[1].strip() if len(hover_shadow_parts) > 1 else "16px",
                    "boxShadowBlur": hover_shadow_parts[2].strip() if len(hover_shadow_parts) > 2 else "48px",
                    "boxShadowSpread": "0px",
                    "boxShadowColor": hover_shadow_parts[4].strip() if len(hover_shadow_parts) > 4 else "rgba(0,0,0,0.15)",
                    "position": "outer",
                }
            }
        }

    return {"base": base, "hover": hover, "css": module_css}


# ═══════════════════════════════════════════════════════════════════════════
# EYEBROW PILL — Premium pill with accent tint, generous spacing
# ═══════════════════════════════════════════════════════════════════════════

def eyebrow_pill(profile, is_dark_zone: bool = False) -> Dict[str, Any]:
    accent = getattr(profile, 'accent', '#0071E3')
    accent_hover = getattr(profile, 'accent_hover', '#005FCE')
    font_ui = getattr(profile, 'font_ui', "'Inter', sans-serif")

    if is_dark_zone:
        bg = f"{accent}1A"
        border_color = f"{accent}40"
        text_color = accent
    else:
        bg = f"{accent}0F"
        border_color = f"{accent}28"
        text_color = accent_hover if accent_hover else accent

    return {
        "font": {
            "desktop": {
                "value": {
                    "color": text_color,
                    "textTransform": "uppercase",
                    "letterSpacing": "2.5px",
                    "size": "11px",
                    "fontWeight": "600",
                    "font": font_ui,
                }
            }
        },
        "background": {
            "desktop": {
                "value": {
                    "color": bg,
                }
            }
        },
        "border": {
            "desktop": {
                "value": {
                    "radius": {"topLeft": "9999px", "topRight": "9999px", "bottomRight": "9999px", "bottomLeft": "9999px"},
                    "styles": {"all": {"color": border_color, "width": "1px"}},
                }
            }
        },
        "spacing": {
            "desktop": {
                "value": {
                    "padding": {"top": "8px", "bottom": "8px", "left": "18px", "right": "18px"},
                    "margin": {"bottom": "16px"},
                }
            }
        },
    }


# ═══════════════════════════════════════════════════════════════════════════
# STAGGER DELAY — Progressive reveal with ease-out timing
# ═══════════════════════════════════════════════════════════════════════════

def stagger_delay(index: int, total: int = 6, base_ms: int = 100, style: str = "subtle") -> str:
    if style == "none":
        return "0ms"
    cap = min(total, 6) if total else 6
    step = min(index, cap - 1)
    if style == "dramatic":
        return f"{step * base_ms + base_ms}ms"
    return f"{step * base_ms}ms"


# ═══════════════════════════════════════════════════════════════════════════
# HEADING DECORATION — Fluid type scale, tight tracking, zone-aware colors
# ═══════════════════════════════════════════════════════════════════════════

_SIZES = {
    "h1": "clamp(2.75rem, 6vw, 5rem)",
    "h2": "clamp(1.75rem, 3.5vw, 2.75rem)",
    "h3": "clamp(1.25rem, 2vw, 1.5rem)",
    "h4": "18px",
}

_LETTER_SPACING = {
    "h1": "-0.04em",
    "h2": "-0.035em",
    "h3": "-0.02em",
    "h4": "-0.01em",
}

_LINE_HEIGHT = {
    "h1": "1.02",
    "h2": "1.08",
    "h3": "1.25",
    "h4": "1.35",
}


def heading_decoration(profile, level: str = "h2", zone: str = "dark_gradient") -> Dict[str, Any]:
    text_ctx = _TEXT_COLORS.get(zone, _TEXT_COLORS["light"])
    color_key = text_ctx["heading"]

    colors = {
        "text_on_dark": getattr(profile, 'text_on_dark', '#F5F5F7'),
        "text_on_light": getattr(profile, 'text_on_light', '#1D1D1F'),
        "text_on_dark_muted": f"{getattr(profile, 'text_on_dark', '#F5F5F7')}b3",
        "text_secondary": getattr(profile, 'text_secondary', '#6E6E73'),
    }
    color = colors.get(color_key, colors["text_on_dark"])
    font_display = getattr(profile, 'font_display', "'SF Pro Display', sans-serif")

    return {
        "font": {
            "desktop": {
                "value": {
                    "color": color,
                    "size": _SIZES.get(level, "24px"),
                    "lineHeight": _LINE_HEIGHT.get(level, "1.3"),
                    "letterSpacing": _LETTER_SPACING.get(level, "-0.02em"),
                    "font": font_display,
                }
            }
        },
    }


def body_decoration(profile, color_type: str = "muted", zone: str = "dark_gradient") -> Dict[str, Any]:
    text_ctx = _TEXT_COLORS.get(zone, _TEXT_COLORS["light"])
    body_key = text_ctx["body"]

    colors = {
        "dark": getattr(profile, 'text_on_dark', '#F5F5F7'),
        "light": getattr(profile, 'text_on_light', '#1D1D1F'),
        "muted_dark": f"{getattr(profile, 'text_on_dark', '#F5F5F7')}b3",
        "muted_light": getattr(profile, 'text_secondary', '#6E6E73'),
        "text_on_dark_muted": f"{getattr(profile, 'text_on_dark', '#F5F5F7')}b3",
        "text_secondary": getattr(profile, 'text_secondary', '#6E6E73'),
    }
    color = colors.get(body_key, colors.get(color_type, colors["text_secondary"]))
    font_body = getattr(profile, 'font_body', "'SF Pro Text', sans-serif")

    return {
        "font": {
            "desktop": {
                "value": {
                    "color": color,
                    "size": "17px",
                    "lineHeight": "1.75",
                    "font": font_body,
                }
            }
        },
    }


# ═══════════════════════════════════════════════════════════════════════════
# SECTION DIVIDERS — Shape dividers between contrast zones
# ═══════════════════════════════════════════════════════════════════════════

_DIVIDER_MAP = {
    "dark_gradient→light": "curve",
    "dark_gradient→light_composite": "curve",
    "dark→light": "curve",
    "dark_accent→light": "wave",
    "dark_glass→light": "angle",
    "light→dark": "curve",
    "light→dark_gradient": "curve",
    "light_composite→dark": "wave",
    "light_alt→dark": "rounded",
    "light→dark_accent": "wave",
    "strip_float→light": None,
    "strip_float_dark→dark": None,
    "transparent→dark_gradient": None,
    "transparent→light": None,
}


def get_zone_divider(current_zone: str, prev_zone: str = None, profile=None) -> Optional[Dict[str, Any]]:
    if prev_zone is None:
        return None
    if not current_zone or not isinstance(current_zone, str):
        return None

    key = f"{prev_zone}→{current_zone}"
    divider_style = _DIVIDER_MAP.get(key)

    if divider_style is None:
        same_family_dark = prev_zone.startswith("dark") and current_zone.startswith("dark")
        same_family_light = prev_zone.startswith("light") and current_zone.startswith("light")
        if same_family_dark or same_family_light:
            return None
        if prev_zone == "strip_float" or current_zone == "strip_float":
            return None
        if prev_zone == "strip_float_dark" or current_zone == "strip_float_dark":
            return None
        divider_style = "curve"

    bg_light = getattr(profile, 'bg_light', '#F5F7FA') if profile else '#F5F7FA'
    bg_dark = getattr(profile, 'bg_dark', '#1C1917') if profile else '#1C1917'

    prev_is_dark = prev_zone.startswith("dark")
    divider_color = bg_light if prev_is_dark else bg_dark

    return {
        "bottom": {
            "desktop": {
                "value": {
                    "style": divider_style,
                    "color": divider_color,
                    "height": "80px",
                    "flip": "off",
                    "invert": "on" if prev_is_dark else "off",
                }
            }
        }
    }


# ═══════════════════════════════════════════════════════════════════════════
# UTILITY — zone-aware color resolution
# ═══════════════════════════════════════════════════════════════════════════

def resolve_zone_color(profile, role: str, zone: str) -> str:
    text_ctx = _TEXT_COLORS.get(zone, _TEXT_COLORS["light"])
    color_key = text_ctx.get(role, "text_on_dark")

    color_map = {
        "text_on_dark": getattr(profile, 'text_on_dark', '#F5F5F7'),
        "text_on_light": getattr(profile, 'text_on_light', '#1D1D1F'),
        "text_on_dark_muted": f"{getattr(profile, 'text_on_dark', '#F5F5F7')}b3",
        "text_secondary": getattr(profile, 'text_secondary', '#6E6E73'),
        "accent": getattr(profile, 'accent', '#0071E3'),
    }
    return color_map.get(color_key, color_map["text_on_dark"])


def is_dark_zone(zone: str) -> bool:
    return zone.startswith("dark") or zone == "strip_float_dark"