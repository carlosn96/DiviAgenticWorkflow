"""DesignDirector — traduce intención de diseño en decisiones concretas.

El Director lee `design_direction` del brief y produce un `DesignProfile` con
valores específicos de color, tipografía, spacing, layout y motion.

Sin `design_direction`, el VIE usa presets genéricos (comportamiento actual).
Con `design_direction`, el VIE genera decoration blocks calculados.

Perfiles predefinidos (moods):
  academic_night    → Azul marino + dorado envejecido + serif elegante
  cool_luxury       → Gris oscuro + azul brillante + sans premium (Apple)
  warm_minimal      → Crema + terracota + serif humanista
  tech_glass        → Negro + cian neón + sans monoespaciado
  organic_modern    → Verde bosque + crema + serif natural
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class DesignProfile:
    """Perfil completo de decisiones de diseño para una página."""

    # Color
    bg_dark: str = "#1C1917"
    bg_light: str = "#F5F7FA"
    bg_mid: str = "#211D1B"
    text_on_dark: str = "#F5F5F7"
    text_on_light: str = "#1D1D1F"
    text_secondary: str = "#252527"
    text_muted: str = "#6E6E73"
    accent: str = "#0071E3"
    accent_hover: str = "#005FCE"
    divider: str = "#0071E3"

    # Typography
    font_display: str = "'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif"
    font_body: str = "'SF Pro Text', -apple-system, BlinkMacSystemFont, sans-serif"
    font_ui: str = "'SF Pro Text', -apple-system, BlinkMacSystemFont, sans-serif"

    # Spacing
    hero_padding_top: str = "140px"
    hero_padding_bottom: str = "140px"
    section_padding_top: str = "96px"
    section_padding_bottom: str = "96px"
    content_padding_top: str = "80px"
    content_padding_bottom: str = "80px"
    container_max_width: str = "1200px"

    # Layout rhythm
    hero_layout: str = "centered"  # centered | asymmetric
    about_layout: str = "centered"   # centered | 2_5_3_5 | image_left
    features_layout: str = "grid_3"  # grid_3 | grid_2 | masonry
    cta_layout: str = "centered"     # centered | 1_3_2_3 | full_width

    # Motion
    motion_intensity: str = "subtle"  # none | subtle | dramatic
    parallax_sections: List[str] = field(default_factory=lambda: ["hero"])
    fade_sections: List[str] = field(default_factory=lambda: ["features", "cta"])

    # Shape dividers
    hero_divider_bottom: Optional[str] = "curve"
    cta_divider_top: Optional[str] = None

    # Button style
    button_radius: str = "3px"
    button_style: str = "filled"  # filled | outline | ghost
    button_letter_spacing: str = "0px"
    button_text_transform: str = "none"

    # Cards / features
    card_style: str = "glass"  # glass | solid | outline | minimal
    card_border_radius: str = "14px"
    card_border_width: str = "0px"
    card_border_color: str = "transparent"
    card_bg: str = "rgba(255,255,255,0.05)"

    # Dividers between title and text
    title_divider: bool = False
    title_divider_width: str = "60px"
    title_divider_color: str = "#0071E3"
    title_divider_weight: str = "2px"

    # Eyebrow style
    eyebrow_letter_spacing: str = "2px"
    eyebrow_size: str = "14px"
    eyebrow_bg: Optional[str] = None  # None = transparent
    eyebrow_radius: str = "0px"

    # Card hover
    card_hover_translate: str = "-4px"
    card_hover_shadow_blur: str = "48px"
    card_hover_border_accent: bool = True

    # Section dividers between zones
    zone_dividers: bool = True

    # Container width by zone
    container_wide: str = "1200px"
    container_standard: str = "1100px"
    container_narrow: str = "960px"

    @property
    def section_bg_dark(self) -> str:
        return self.bg_dark

    @property
    def section_bg_light(self) -> str:
        return self.bg_light


# ── Perfiles predefinidos por mood ──────────────────────────────────────────

_PROFILES: Dict[str, DesignProfile] = {
    "academic_night": DesignProfile(
        bg_dark="#0A0E1A",
        bg_light="#F4F1EA",
        bg_mid="#1A1A2E",
        text_on_dark="#F4F1EA",
        text_on_light="#1A1A2E",
        text_secondary="#4A4A5E",
        text_muted="#8B7355",
        accent="#C9A962",
        accent_hover="#B89A52",
        divider="#C9A962",
        font_display="'Crimson Pro', 'Playfair Display', serif",
        font_body="'Space Grotesk', 'Inter', sans-serif",
        font_ui="'Space Grotesk', 'Inter', sans-serif",
        hero_padding_top="180px",
        hero_padding_bottom="160px",
        section_padding_top="140px",
        section_padding_bottom="140px",
        content_padding_top="120px",
        content_padding_bottom="120px",
        hero_layout="centered",
        about_layout="2_5_3_5",
        features_layout="grid_3",
        cta_layout="1_3_2_3",
        motion_intensity="subtle",
        parallax_sections=["hero"],
        fade_sections=["about", "features", "cta"],
        hero_divider_bottom="wave",
        button_radius="0px",
        button_style="filled",
        button_letter_spacing="2px",
        button_text_transform="uppercase",
        card_style="outline",
        card_border_radius="2px",
        card_border_width="1px",
        card_border_color="rgba(201,169,98,0.15)",
        card_bg="rgba(255,255,255,0.03)",
        title_divider=True,
        title_divider_width="80px",
        title_divider_color="#C9A962",
        title_divider_weight="2px",
        eyebrow_letter_spacing="4px",
        eyebrow_size="12px",
        eyebrow_bg=None,
        eyebrow_radius="0px",
        card_hover_translate="-4px",
        card_hover_shadow_blur="54px",
        card_hover_border_accent=False,
        zone_dividers=True,
    ),
    "cool_luxury": DesignProfile(
        bg_dark="#1C1917",
        bg_light="#F5F7FA",
        bg_mid="#211D1B",
        text_on_dark="#F5F5F7",
        text_on_light="#1D1D1F",
        text_secondary="#252527",
        text_muted="#6E6E73",
        accent="#0071E3",
        accent_hover="#005FCE",
        divider="#0071E3",
        font_display="'SF Pro Display', -apple-system, sans-serif",
        font_body="'SF Pro Text', -apple-system, sans-serif",
        font_ui="'SF Pro Text', -apple-system, sans-serif",
        hero_padding_top="140px",
        hero_padding_bottom="140px",
        section_padding_top="96px",
        section_padding_bottom="96px",
        content_padding_top="80px",
        content_padding_bottom="80px",
        hero_layout="centered",
        about_layout="centered",
        features_layout="grid_3",
        cta_layout="centered",
        motion_intensity="subtle",
        parallax_sections=["hero"],
        fade_sections=["features", "cta"],
        hero_divider_bottom="curve",
        button_radius="3px",
        button_style="filled",
        button_letter_spacing="0px",
        button_text_transform="none",
        card_style="glass",
        card_border_radius="14px",
        card_border_width="0px",
        card_border_color="transparent",
        card_bg="rgba(255,255,255,0.05)",
        title_divider=False,
        title_divider_width="60px",
        title_divider_color="#0071E3",
        title_divider_weight="2px",
        eyebrow_letter_spacing="2px",
        eyebrow_size="14px",
        eyebrow_bg=None,
        eyebrow_radius="0px",
        card_hover_translate="-4px",
        card_hover_shadow_blur="48px",
        card_hover_border_accent=True,
        zone_dividers=True,
    ),
    "warm_minimal": DesignProfile(
        bg_dark="#2D2A26",
        bg_light="#FAF8F5",
        bg_mid="#E8E4DA",
        text_on_dark="#FAF8F5",
        text_on_light="#2D2A26",
        text_secondary="#5C5752",
        text_muted="#8B8680",
        accent="#C17F59",
        accent_hover="#A66B48",
        divider="#C17F59",
        font_display="'Crimson Pro', 'Georgia', serif",
        font_body="'Inter', 'Helvetica Neue', sans-serif",
        font_ui="'Inter', 'Helvetica Neue', sans-serif",
        hero_padding_top="160px",
        hero_padding_bottom="140px",
        section_padding_top="120px",
        section_padding_bottom="120px",
        content_padding_top="100px",
        content_padding_bottom="100px",
        hero_layout="centered",
        about_layout="centered",
        features_layout="grid_2",
        cta_layout="full_width",
        motion_intensity="none",
        parallax_sections=[],
        fade_sections=[],
        hero_divider_bottom=None,
        button_radius="0px",
        button_style="outline",
        button_letter_spacing="1px",
        button_text_transform="uppercase",
        card_style="minimal",
        card_border_radius="12px",
        card_border_width="1px",
        card_border_color="rgba(193,127,89,0.2)",
        card_bg="transparent",
        title_divider=True,
        title_divider_width="40px",
        title_divider_color="#C17F59",
        title_divider_weight="1px",
        eyebrow_letter_spacing="3px",
        eyebrow_size="11px",
        eyebrow_bg=None,
        eyebrow_radius="0px",
        card_hover_translate="-2px",
        card_hover_shadow_blur="36px",
        card_hover_border_accent=True,
        zone_dividers=False,
    ),
    "tech_glass": DesignProfile(
        bg_dark="#050505",
        bg_light="#0A0A0A",
        bg_mid="#111111",
        text_on_dark="#E0E0E0",
        text_on_light="#E0E0E0",
        text_secondary="#A0A0A0",
        text_muted="#606060",
        accent="#00F0FF",
        accent_hover="#00D0DD",
        divider="#00F0FF",
        font_display="'Space Grotesk', 'JetBrains Mono', monospace",
        font_body="'Inter', 'Roboto', sans-serif",
        font_ui="'Space Grotesk', sans-serif",
        hero_padding_top="200px",
        hero_padding_bottom="180px",
        section_padding_top="120px",
        section_padding_bottom="120px",
        content_padding_top="100px",
        content_padding_bottom="100px",
        hero_layout="asymmetric",
        about_layout="image_left",
        features_layout="grid_3",
        cta_layout="full_width",
        motion_intensity="dramatic",
        parallax_sections=["hero", "features"],
        fade_sections=["hero", "about", "features", "cta"],
        hero_divider_bottom="angle",
        button_radius="9999px",
        button_style="ghost",
        button_letter_spacing="2px",
        button_text_transform="uppercase",
        card_style="glass",
        card_border_radius="20px",
        card_border_width="1px",
        card_border_color="rgba(0,240,255,0.1)",
        card_bg="rgba(0,240,255,0.02)",
        title_divider=False,
        eyebrow_letter_spacing="4px",
        eyebrow_size="12px",
        eyebrow_bg="rgba(0,240,255,0.08)",
        eyebrow_radius="9999px",
        card_hover_translate="-4px",
        card_hover_shadow_blur="40px",
        card_hover_border_accent=True,
        zone_dividers=True,
    ),
    "organic_modern": DesignProfile(
        bg_dark="#1B2A1B",
        bg_light="#F5F0E8",
        bg_mid="#E8E0D4",
        text_on_dark="#F5F0E8",
        text_on_light="#1B2A1B",
        text_secondary="#3A4A3A",
        text_muted="#6B7B6B",
        accent="#7B9E6B",
        accent_hover="#6A8D5A",
        divider="#7B9E6B",
        font_display="'Crimson Pro', 'Georgia', serif",
        font_body="'Inter', sans-serif",
        font_ui="'Inter', sans-serif",
        hero_padding_top="160px",
        hero_padding_bottom="140px",
        section_padding_top="120px",
        section_padding_bottom="120px",
        content_padding_top="100px",
        content_padding_bottom="100px",
        hero_layout="centered",
        about_layout="centered",
        features_layout="grid_3",
        cta_layout="centered",
        motion_intensity="subtle",
        parallax_sections=["hero"],
        fade_sections=["features"],
        hero_divider_bottom="rounded",
        button_radius="9999px",
        button_style="filled",
        button_letter_spacing="1px",
        button_text_transform="uppercase",
        card_style="solid",
        card_border_radius="16px",
        card_border_width="0px",
        card_border_color="transparent",
        card_bg="#FFFFFF",
        title_divider=True,
        title_divider_width="50px",
        title_divider_color="#7B9E6B",
        title_divider_weight="2px",
        eyebrow_letter_spacing="3px",
        eyebrow_size="12px",
        eyebrow_bg=None,
        eyebrow_radius="0px",
        card_hover_translate="-3px",
        card_hover_shadow_blur="32px",
        card_hover_border_accent=False,
        zone_dividers=True,
    ),
}


def get_profile(design_direction: Optional[Dict[str, str]]) -> DesignProfile:
    """Resuelve un DesignProfile desde design_direction.

    Si design_direction es None o no tiene 'mood', retorna el perfil genérico
    cool_luxury (comportamiento actual del VIE).
    """
    if not design_direction:
        return _PROFILES["cool_luxury"]

    mood = design_direction.get("mood", "cool_luxury")
    base = _PROFILES.get(mood, _PROFILES["cool_luxury"])

    # Overrides explícitos desde design_direction
    overrides = {
        k: v for k, v in design_direction.items()
        if k != "mood" and hasattr(base, k)
    }
    if overrides:
        # Crear copia con overrides aplicados
        fields = {f.name: getattr(base, f.name) for f in base.__dataclass_fields__.values()}
        fields.update(overrides)
        return DesignProfile(**fields)

    return base


def get_hero_decoration(profile: DesignProfile) -> Dict[str, Any]:
    """Genera decoration block para sección hero según perfil."""
    bg_overlay = None
    if profile.motion_intensity == "dramatic":
        bg_overlay = {
            "gradient": f"linear-gradient(165deg, {profile.bg_dark}ee 0%, {profile.bg_mid}99 40%, {profile.bg_dark}f0 100%)"
        }
    elif profile.motion_intensity == "subtle":
        bg_overlay = {
            "gradient": f"linear-gradient(165deg, {profile.bg_dark}e6 0%, {profile.bg_mid}66 50%, {profile.bg_dark}f2 100%)"
        }
    else:
        bg_overlay = {
            "gradient": f"linear-gradient(180deg, {profile.bg_dark}f5 0%, {profile.bg_dark} 100%)"
        }

    dec = {
        "background": {
            "desktop": {
                "value": {
                    "color": profile.bg_dark,
                    "overlay": bg_overlay,
                }
            }
        },
        "spacing": {
            "desktop": {
                "value": {
                    "padding": {
                        "top": profile.hero_padding_top,
                        "bottom": profile.hero_padding_bottom,
                        "right": "48px",
                        "left": "48px",
                    }
                }
            }
        },
    }

    if profile.hero_divider_bottom:
        dec["shapeDivider"] = {
            "bottom": {
                "desktop": {
                    "value": {
                        "style": profile.hero_divider_bottom,
                        "color": profile.bg_light,
                        "height": "80px",
                        "flip": "off",
                        "invert": "off",
                    }
                }
            }
        }

    if profile.motion_intensity in ("subtle", "dramatic"):
        dec["animation"] = {
            "desktop": {
                "value": {
                    "style": "fade",
                    "duration": "800ms",
                    "delay": "0ms",
                    "speedCurve": "ease-out",
                }
            }
        }
        if "hero" in profile.parallax_sections:
            dec["scroll"] = {
                "desktop": {
                    "value": {
                        "verticalMotion": {
                            "enable": "on",
                            "offset": {"start": "6", "mid": "0", "end": "-4"},
                        },
                        "motionTriggerStart": "middle",
                    }
                }
            }

    return dec


def get_features_decoration(profile: DesignProfile) -> Dict[str, Any]:
    """Genera decoration block para sección features según perfil."""
    dec = {
        "background": {
            "desktop": {
                "value": {
                    "color": profile.bg_mid,
                }
            }
        },
        "spacing": {
            "desktop": {
                "value": {
                    "padding": {
                        "top": profile.section_padding_top,
                        "bottom": profile.section_padding_bottom,
                        "right": "48px",
                        "left": "48px",
                    }
                }
            }
        },
    }

    if profile.motion_intensity in ("subtle", "dramatic"):
        dec["animation"] = {
            "desktop": {
                "value": {
                    "style": "fade",
                    "duration": "600ms",
                    "delay": "100ms",
                    "speedCurve": "ease-out",
                }
            }
        }

    return dec


def get_cta_decoration(profile: DesignProfile) -> Dict[str, Any]:
    """Genera decoration block para sección CTA según perfil."""
    dec = {
        "background": {
            "desktop": {
                "value": {
                    "color": profile.bg_dark,
                    "overlay": {
                        "gradient": f"linear-gradient(135deg, {profile.bg_dark}f5 0%, {profile.bg_mid}dd 100%)"
                    },
                }
            }
        },
        "spacing": {
            "desktop": {
                "value": {
                    "padding": {
                        "top": profile.section_padding_top,
                        "bottom": profile.section_padding_bottom,
                        "right": "48px",
                        "left": "48px",
                    }
                }
            }
        },
    }

    if profile.motion_intensity in ("subtle", "dramatic"):
        dec["animation"] = {
            "desktop": {
                "value": {
                    "style": "fade",
                    "duration": "600ms",
                    "delay": "200ms",
                    "speedCurve": "ease-out",
                }
            }
        }

    return dec


def get_content_decoration(profile: DesignProfile, is_light: bool = True) -> Dict[str, Any]:
    """Genera decoration block para sección content según perfil."""
    bg = profile.bg_light if is_light else profile.bg_mid
    return {
        "background": {
            "desktop": {
                "value": {
                    "color": bg,
                }
            }
        },
        "spacing": {
            "desktop": {
                "value": {
                    "padding": {
                        "top": profile.content_padding_top,
                        "bottom": profile.content_padding_bottom,
                        "right": "48px",
                        "left": "48px",
                    }
                }
            }
        },
    }


def get_card_decoration(profile: DesignProfile) -> Dict[str, Any]:
    """Genera decoration block para tarjetas de features según perfil."""
    card_dec = {
        "background": {
            "desktop": {
                "value": {
                    "color": profile.card_bg,
                }
            }
        },
        "border": {
            "desktop": {
                "value": {
                    "radius": {
                        "topLeft": profile.card_border_radius,
                        "topRight": profile.card_border_radius,
                        "bottomRight": profile.card_border_radius,
                        "bottomLeft": profile.card_border_radius,
                    },
                    "styles": {
                        "all": {
                            "color": profile.card_border_color,
                            "width": profile.card_border_width,
                        }
                    },
                }
            }
        },
        "spacing": {
            "desktop": {
                "value": {
                    "padding": {
                        "top": "48px",
                        "bottom": "48px",
                        "left": "36px",
                        "right": "36px",
                    }
                }
            }
        },
    }

    # Sombra sutil para cards sólidas
    if profile.card_style == "solid":
        card_dec["boxShadow"] = {
            "desktop": {
                "value": {
                    "boxShadowHorizontal": "0px",
                    "boxShadowVertical": "12px",
                    "boxShadowBlur": "24px",
                    "boxShadowSpread": "-6px",
                    "boxShadowColor": "rgba(0,0,0,0.08)",
                }
            }
        }

    return card_dec


def get_button_decoration(profile: DesignProfile) -> Dict[str, Any]:
    """Genera decoration block para botones según perfil."""
    if profile.button_style == "outline":
        return {
            "button": {
                "desktop": {
                    "value": {
                        "backgroundColor": "transparent",
                        "color": profile.accent,
                        "borderRadius": profile.button_radius,
                        "border": {
                            "all": {
                                "color": profile.accent,
                                "width": "2px",
                            }
                        },
                        "padding": {
                            "top": "18px",
                            "bottom": "18px",
                            "left": "48px",
                            "right": "48px",
                        },
                        "font": profile.font_ui,
                        "size": "14px",
                        "letterSpacing": profile.button_letter_spacing,
                        "textTransform": profile.button_text_transform,
                    }
                }
            }
        }
    elif profile.button_style == "ghost":
        return {
            "button": {
                "desktop": {
                    "value": {
                        "backgroundColor": "rgba(255,255,255,0.05)",
                        "color": profile.accent,
                        "borderRadius": profile.button_radius,
                        "border": {
                            "all": {
                                "color": f"{profile.accent}33",
                                "width": "1px",
                            }
                        },
                        "padding": {
                            "top": "18px",
                            "bottom": "18px",
                            "left": "40px",
                            "right": "40px",
                        },
                        "font": profile.font_ui,
                        "size": "14px",
                        "letterSpacing": profile.button_letter_spacing,
                        "textTransform": profile.button_text_transform,
                    }
                }
            }
        }
    else:  # filled
        return {
            "button": {
                "desktop": {
                    "value": {
                        "backgroundColor": profile.accent,
                        "color": profile.bg_dark,
                        "borderRadius": profile.button_radius,
                        "padding": {
                            "top": "18px",
                            "bottom": "18px",
                            "left": "40px",
                            "right": "40px",
                        },
                        "font": profile.font_ui,
                        "size": "14px",
                        "letterSpacing": profile.button_letter_spacing,
                        "textTransform": profile.button_text_transform,
                    }
                }
            }
        }


def get_eyebrow_font(profile: DesignProfile) -> Dict[str, Any]:
    """Genera font decoration para eyebrow según perfil."""
    return {
        "font": {
            "desktop": {
                "value": {
                    "color": profile.accent,
                    "textTransform": "uppercase",
                    "letterSpacing": profile.eyebrow_letter_spacing,
                    "size": profile.eyebrow_size,
                    "font": profile.font_ui,
                }
            }
        }
    }


def get_heading_font(profile: DesignProfile, level: str = "h2", color: str = None) -> Dict[str, Any]:
    """Genera font decoration para headings según perfil."""
    sizes = {
        "h1": "clamp(3rem, 7vw, 5.5rem)",
        "h2": "clamp(2rem, 4vw, 3rem)",
        "h3": "22px",
    }
    colors = {
        "dark": profile.text_on_dark,
        "light": profile.text_on_light,
    }
    chosen_color = color or colors.get("dark", profile.text_on_dark)
    return {
        "font": {
            "desktop": {
                "value": {
                    "color": chosen_color,
                    "size": sizes.get(level, "24px"),
                    "lineHeight": "1.15" if level in ("h1", "h2") else "1.3",
                    "font": profile.font_display,
                }
            }
        }
    }


def get_body_font(profile: DesignProfile, color_type: str = "muted") -> Dict[str, Any]:
    """Genera font decoration para body text según perfil."""
    colors = {
        "dark": profile.text_on_dark,
        "light": profile.text_on_light,
        "muted_dark": f"{profile.text_on_dark}b3",  # 70% opacity
        "muted_light": profile.text_secondary,
    }
    return {
        "font": {
            "desktop": {
                "value": {
                    "color": colors.get(color_type, profile.text_muted),
                    "size": "16px",
                    "lineHeight": "1.7",
                    "font": profile.font_body,
                }
            }
        }
    }


def get_stats_decoration(profile: DesignProfile) -> Dict[str, Any]:
    return {
        "background": {
            "desktop": {
                "value": {
                    "color": profile.bg_light,
                }
            }
        },
        "spacing": {
            "desktop": {
                "value": {
                    "padding": {
                        "top": profile.content_padding_top,
                        "bottom": profile.content_padding_bottom,
                        "right": "48px",
                        "left": "48px",
                    }
                }
            }
        },
    }


def get_team_card_decoration(profile: DesignProfile) -> Dict[str, Any]:
    card_dec = {
        "background": {
            "desktop": {
                "value": {
                    "color": profile.bg_mid if hasattr(profile, 'bg_mid') else profile.bg_dark,
                }
            }
        },
        "spacing": {
            "desktop": {
                "value": {
                    "padding": {
                        "top": "24px",
                        "bottom": "32px",
                        "left": "20px",
                        "right": "20px",
                    }
                }
            }
        },
    }
    if profile.card_border_radius:
        card_dec["border"] = {
            "desktop": {
                "value": {
                    "radius": {
                        "topLeft": "12px",
                        "topRight": "12px",
                        "bottomRight": "12px",
                        "bottomLeft": "12px",
                    },
                }
            }
        }
    return card_dec


def get_gallery_decoration(profile: DesignProfile) -> Dict[str, Any]:
    return {
        "background": {
            "desktop": {
                "value": {
                    "color": profile.bg_mid,
                }
            }
        },
        "spacing": {
            "desktop": {
                "value": {
                    "padding": {
                        "top": profile.section_padding_top,
                        "bottom": profile.section_padding_bottom,
                        "right": "48px",
                        "left": "48px",
                    }
                }
            }
        },
    }


def get_process_decoration(profile: DesignProfile) -> Dict[str, Any]:
    return {
        "background": {
            "desktop": {
                "value": {
                    "color": profile.bg_light,
                }
            }
        },
        "spacing": {
            "desktop": {
                "value": {
                    "padding": {
                        "top": profile.section_padding_top,
                        "bottom": profile.section_padding_bottom,
                        "right": "48px",
                        "left": "48px",
                    }
                }
            }
        },
    }


def get_title_divider(profile: DesignProfile) -> Optional[Dict[str, Any]]:
    """Genera divider decoration entre título y body si está habilitado."""
    if not profile.title_divider:
        return None
    return {
        "divider": {
            "desktop": {
                "value": {
                    "color": profile.title_divider_color,
                    "weight": profile.title_divider_weight,
                    "width": profile.title_divider_width,
                    "position": "left",
                }
            }
        },
        "spacing": {
            "desktop": {
                "value": {
                    "margin": {"top": "24px", "bottom": "24px"},
                }
            }
        },
    }
