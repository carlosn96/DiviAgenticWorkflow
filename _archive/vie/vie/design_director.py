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

from daw.constants import FRONTEND_PRINCIPLES

# ── Mapeo: resolver.get_token_value(category, name) → DesignProfile field ──
# Los tokens provienen de _design_vars.json → build_design_system.py → divitheme.json
# Si un token no existe en la marca, se usa el default del dataclass.

_TOKEN_TO_PROFILE = [
    ("accent", "color", "accent"),
    ("bg_dark", "color", "bg_dark"),
    ("bg_light", "color", "bg_light"),
    ("bg_mid", "color", "bg_mid"),
    ("text_on_dark", "color", "text_on_dark"),
    ("text_on_light", "color", "text_on_light"),
    ("text_secondary", "color", "text_muted_light"),
    ("text_muted", "color", "text_muted_dark"),
    ("divider", "color", "divider"),
    ("font_display", "font", "display"),
    ("font_body", "font", "body"),
    ("font_ui", "font", "ui"),
    ("card_border_radius", "radius", "card"),
    ("button_radius", "radius", "button"),
    ("hero_padding_top", "space", "hero"),
    ("hero_padding_bottom", "space", "hero"),
    ("section_padding_top", "space", "section"),
    ("section_padding_bottom", "space", "section"),
]


def _load_brand_values(resolver) -> dict:
    """Carga valores de colores/fonts/espaciado desde el brand resolver.
    Solo sobreescribe si el token existe en el design system de la marca.
    """
    out = {}
    for field_name, category, token_name in _TOKEN_TO_PROFILE:
        val = resolver.get_token_value(category, token_name) if hasattr(resolver, 'get_token_value') else None
        if val:
            out[field_name] = val
    return out


@dataclass
class DesignProfile:
    """Perfil completo de decisiones de diseño para una página."""

    # Mood (set by get_profile, used by patterns.py:_get_mood)
    mood: str = "cool_luxury"

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

    # Premium upgrades (Phase 5)
    accent_light: str = ""
    accent_muted: str = ""
    hero_padding_top_tablet: str = "140px"
    hero_padding_top_phone: str = "120px"
    hero_padding_bottom_tablet: str = "140px"
    hero_padding_bottom_phone: str = "120px"
    section_padding_top_tablet: str = "100px"
    section_padding_top_phone: str = "80px"
    section_padding_bottom_tablet: str = "100px"
    section_padding_bottom_phone: str = "80px"
    cta_padding_top: str = "120px"
    cta_padding_bottom: str = "120px"
    cta_padding_top_tablet: str = "120px"
    cta_padding_top_phone: str = "100px"
    cta_padding_bottom_tablet: str = "120px"
    cta_padding_bottom_phone: str = "100px"
    button_gradient: bool = False
    button_shadow_layers: int = 1
    card_glass_blur: str = "20px"
    card_glass_saturate: str = "1.4"
    card_bg_glass_opacity: str = "0.6"
    heading_text_shadow: bool = False
    grain_texture: bool = False
    stagger_hero: bool = False
    stagger_cta: bool = False
    stagger_stats: bool = False

    @property
    def section_bg_dark(self) -> str:
        return self.bg_dark

    @property
    def section_bg_light(self) -> str:
        return self.bg_light


# ── Perfiles predefinidos por mood ──────────────────────────────────────────

_PROFILES: Dict[str, DesignProfile] = {
    "academic_night": DesignProfile(
        mood="academic_night",
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
        hero_padding_top_tablet="140px",
        hero_padding_top_phone="120px",
        hero_padding_bottom_tablet="120px",
        hero_padding_bottom_phone="100px",
        section_padding_top="140px",
        section_padding_bottom="140px",
        section_padding_top_tablet="100px",
        section_padding_top_phone="80px",
        section_padding_bottom_tablet="100px",
        section_padding_bottom_phone="80px",
        cta_padding_top="160px",
        cta_padding_bottom="160px",
        cta_padding_top_tablet="120px",
        cta_padding_top_phone="100px",
        cta_padding_bottom_tablet="120px",
        cta_padding_bottom_phone="100px",
        accent_light="#D4BA7A",
        accent_muted="#A8893E",
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
        heading_text_shadow=True,
        stagger_hero=True,
        stagger_cta=True,
        stagger_stats=False,
        zone_dividers=True,
    ),
    "cool_luxury": DesignProfile(
        mood="cool_luxury",
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
        hero_padding_top_tablet="120px",
        hero_padding_top_phone="100px",
        hero_padding_bottom_tablet="120px",
        hero_padding_bottom_phone="100px",
        section_padding_top="96px",
        section_padding_bottom="96px",
        section_padding_top_tablet="80px",
        section_padding_top_phone="64px",
        section_padding_bottom_tablet="80px",
        section_padding_bottom_phone="64px",
        cta_padding_top="120px",
        cta_padding_bottom="120px",
        cta_padding_top_tablet="100px",
        cta_padding_top_phone="80px",
        cta_padding_bottom_tablet="100px",
        cta_padding_bottom_phone="80px",
        accent_light="#4DA6FF",
        accent_muted="#005FCE",
        card_glass_blur="16px",
        card_glass_saturate="1.3",
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
        heading_text_shadow=True,
        stagger_hero=True,
        stagger_cta=True,
        stagger_stats=True,
        zone_dividers=True,
    ),
    "warm_minimal": DesignProfile(
        mood="warm_minimal",
        bg_dark="#1A110A",
        bg_light="#F5F0E8",
        bg_mid="#E8E0D4",
        text_on_dark="#F5F0E8",
        text_on_light="#1A110A",
        text_secondary="#5C5752",
        text_muted="#8B8680",
        accent="#C17F59",
        accent_hover="#A66B48",
        accent_light="#E1AA8C",
        accent_muted="#DDC8BB",
        divider="#C17F59",
        font_display="'Bodoni Moda', 'Georgia', serif",
        font_body="'Jost', 'Inter', sans-serif",
        font_ui="'Jost', 'Inter', sans-serif",
        hero_padding_top="200px",
        hero_padding_bottom="200px",
        hero_padding_top_tablet="140px",
        hero_padding_top_phone="120px",
        hero_padding_bottom_tablet="140px",
        hero_padding_bottom_phone="120px",
        section_padding_top="160px",
        section_padding_bottom="120px",
        section_padding_top_tablet="100px",
        section_padding_top_phone="80px",
        section_padding_bottom_tablet="80px",
        section_padding_bottom_phone="64px",
        cta_padding_top="180px",
        cta_padding_bottom="180px",
        cta_padding_top_tablet="120px",
        cta_padding_top_phone="100px",
        cta_padding_bottom_tablet="120px",
        cta_padding_bottom_phone="100px",
        hero_layout="centered",
        about_layout="centered",
        features_layout="grid_2",
        cta_layout="full_width",
        motion_intensity="subtle",
        parallax_sections=[],
        fade_sections=["features"],
        hero_divider_bottom=None,
        button_radius="9999px",
        button_style="filled",
        button_letter_spacing="14px",
        button_text_transform="uppercase",
        button_gradient=True,
        button_shadow_layers=3,
        card_style="glass",
        card_border_radius="24px",
        card_border_width="0px",
        card_border_color="rgba(193,127,89,0.1)",
        card_bg="rgba(255,255,255,0.6)",
        card_glass_blur="20px",
        card_glass_saturate="1.4",
        card_bg_glass_opacity="0.6",
        title_divider=True,
        title_divider_width="40px",
        title_divider_color="#C17F59",
        title_divider_weight="1px",
        heading_text_shadow=True,
        grain_texture=True,
        stagger_hero=True,
        stagger_cta=True,
        stagger_stats=True,
        eyebrow_letter_spacing="25px",
        eyebrow_size="10px",
        eyebrow_bg=None,
        eyebrow_radius="0px",
        card_hover_translate="-8px",
        card_hover_shadow_blur="64px",
        card_hover_border_accent=False,
        zone_dividers=False,
    ),
    "tech_glass": DesignProfile(
        mood="tech_glass",
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
        hero_padding_top_tablet="140px",
        hero_padding_top_phone="120px",
        hero_padding_bottom_tablet="140px",
        hero_padding_bottom_phone="120px",
        section_padding_top="120px",
        section_padding_bottom="120px",
        section_padding_top_tablet="80px",
        section_padding_top_phone="64px",
        section_padding_bottom_tablet="80px",
        section_padding_bottom_phone="64px",
        cta_padding_top="160px",
        cta_padding_bottom="160px",
        cta_padding_top_tablet="120px",
        cta_padding_top_phone="100px",
        cta_padding_bottom_tablet="120px",
        cta_padding_bottom_phone="100px",
        accent_light="#66F5FF",
        accent_muted="#00B8CC",
        card_glass_blur="24px",
        card_glass_saturate="1.5",
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
        stagger_hero=True,
        stagger_cta=True,
        stagger_stats=True,
        zone_dividers=True,
    ),
    "organic_modern": DesignProfile(
        mood="organic_modern",
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
        font_display="'Cormorant Garamond', 'Georgia', serif",
        font_body="'Inter', sans-serif",
        font_ui="'Inter', sans-serif",
        hero_padding_top="160px",
        hero_padding_bottom="140px",
        hero_padding_top_tablet="120px",
        hero_padding_top_phone="100px",
        hero_padding_bottom_tablet="120px",
        hero_padding_bottom_phone="100px",
        section_padding_top="120px",
        section_padding_bottom="120px",
        section_padding_top_tablet="80px",
        section_padding_top_phone="64px",
        section_padding_bottom_tablet="80px",
        section_padding_bottom_phone="64px",
        cta_padding_top="140px",
        cta_padding_bottom="140px",
        cta_padding_top_tablet="100px",
        cta_padding_top_phone="80px",
        cta_padding_bottom_tablet="100px",
        cta_padding_bottom_phone="80px",
        accent_light="#9EBC8E",
        accent_muted="#5A7D4A",
        grain_texture=True,
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


def _hex_to_rgb(hex_color: str) -> str:
    """Convert hex color to 'R,G,B' string for use in rgba()."""
    h = hex_color.lstrip("#")
    if len(h) == 6:
        return f"{int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)}"
    return "0,0,0"


def get_profile(design_direction: Optional[Dict[str, str]],
                resolver=None) -> DesignProfile:
    """Resuelve un DesignProfile desde design_direction + brand resolver.

    El orden de precedencia (menor a mayor):
    1. Defaults del dataclass
    2. Valores del mood seleccionado
    3. Overrides explícitos desde design_direction (bridge → efectos, stagger)
    4. Valores del brand (desde resolver / divitheme.json → colores, fonts, espacio)

    El brand SIEMPRE gana en valores (colores, fuentes, espaciado).
    El mood + bridge controlan lo estructural (card_style, stagger, motion).
    """
    if not design_direction:
        base = _PROFILES["cool_luxury"]
    else:
        mood = design_direction.get("mood", "cool_luxury")
        base = _PROFILES.get(mood, _PROFILES["cool_luxury"])

    fields = {f.name: getattr(base, f.name) for f in base.__dataclass_fields__.values()}

    # 1. Overrides desde design_direction (bridge, UX-Pro, _ART_DIRECTION_PRESETS)
    if design_direction:
        dd_keys = {k for k in design_direction if k != "mood" and k in fields}
        structural = dd_keys - {f[0] for f in _TOKEN_TO_PROFILE}
        for k in structural:
            fields[k] = design_direction[k]

    # 2. Brand values SIEMPRE ganan sobre mood y bridge
    if resolver:
        brand_vals = _load_brand_values(resolver)
        fields.update(brand_vals)

    return DesignProfile(**fields)


def apply_effects_tags(profile: DesignProfile, effects_tags: List[str]) -> DesignProfile:
    """Apply UXProBridge effects_tags as profile field overrides.

    Maps: glass→blur/saturate, grain→texture, depth→multi-shadow/heading-shadow,
    gradient→button_gradient+radial overlay, animated/morphing/fluid→stagger,
    minimal→light profile, scroll→parallax.
    """
    if not effects_tags:
        return profile
    fields = {f.name: getattr(profile, f.name) for f in profile.__dataclass_fields__.values()}
    tag_set = set(t.lower() for t in effects_tags)

    if "glass" in tag_set or "blur" in tag_set:
        if fields.get("card_style") != "glass":
            fields["card_style"] = "glass"
            fields["card_bg"] = "rgba(255,255,255,0.6)"
            if not fields.get("card_glass_blur") or fields["card_glass_blur"] == "0px":
                fields["card_glass_blur"] = "20px"
                fields["card_glass_saturate"] = "1.4"

    if "depth" in tag_set:
        fields["heading_text_shadow"] = True
        fields["button_shadow_layers"] = max(fields.get("button_shadow_layers", 0), 3)

    if "gradient" in tag_set:
        fields["button_gradient"] = True

    if any(t in tag_set for t in ("animated", "morphing", "fluid")):
        fields["stagger_hero"] = True
        fields["stagger_cta"] = True
        fields["stagger_stats"] = True

    if "grain" in tag_set:
        fields["grain_texture"] = True

    if "minimal" in tag_set:
        fields["grain_texture"] = False
        fields["stagger_hero"] = False
        fields["stagger_cta"] = False
        fields["stagger_stats"] = False

    return DesignProfile(**fields)


def get_hero_decoration(profile: DesignProfile) -> Dict[str, Any]:
    """Genera decoration block para sección hero según perfil."""
    accent_rgb = _hex_to_rgb(profile.accent)
    bg_dark_rgb = _hex_to_rgb(profile.bg_dark)

    if profile.motion_intensity == "dramatic":
        gradient_stops = [
            {"color": f"rgba({accent_rgb},0.25)", "position": "0"},
            {"color": f"rgba({accent_rgb},0.08)", "position": "25"},
            {"color": f"rgba({bg_dark_rgb},0.5)", "position": "50"},
            {"color": f"rgba({bg_dark_rgb},0.95)", "position": "80"},
            {"color": profile.bg_dark, "position": "100"},
        ]
        gradient = {"type": "radial", "direction": "180deg", "stops": gradient_stops, "overlaysImage": "on"}
    elif profile.motion_intensity == "subtle":
        gradient_stops = [
            {"color": f"rgba({accent_rgb},0.22)", "position": "0"},
            {"color": f"rgba({accent_rgb},0.06)", "position": "25"},
            {"color": f"rgba({bg_dark_rgb},0.5)", "position": "50"},
            {"color": f"rgba({bg_dark_rgb},0.95)", "position": "80"},
            {"color": profile.bg_dark, "position": "100"},
        ]
        gradient = {"type": "radial", "direction": "180deg", "stops": gradient_stops, "overlaysImage": "on"}
    else:
        gradient_stops = [
            {"color": f"rgba({accent_rgb},0.15)", "position": "0"},
            {"color": f"rgba({bg_dark_rgb},0.8)", "position": "50"},
            {"color": profile.bg_dark, "position": "100"},
        ]
        gradient = {"type": "radial", "direction": "180deg", "stops": gradient_stops, "overlaysImage": "on"}

    dec = {
        "background": {
            "desktop": {
                "value": {
                    "color": profile.bg_dark,
                    "gradient": gradient,
                }
            }
        },
        "spacing": {
            "desktop": {"value": {"padding": {"top": profile.hero_padding_top, "bottom": profile.hero_padding_bottom, "right": "80px", "left": "80px"}}},
            "tablet": {"value": {"padding": {"top": profile.hero_padding_top_tablet, "bottom": profile.hero_padding_bottom_tablet, "right": "48px", "left": "48px"}}},
            "phone": {"value": {"padding": {"top": profile.hero_padding_top_phone, "bottom": profile.hero_padding_bottom_phone, "right": "24px", "left": "24px"}}},
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
    spt_t = getattr(profile, 'section_padding_top_tablet', '80px')
    spt_p = getattr(profile, 'section_padding_top_phone', '64px')
    spb_t = getattr(profile, 'section_padding_bottom_tablet', '80px')
    spb_p = getattr(profile, 'section_padding_bottom_phone', '64px')
    dec = {
        "background": {
            "desktop": {
                "value": {
                    "color": profile.bg_mid,
                }
            }
        },
        "spacing": {
            "desktop": {"value": {"padding": {"top": profile.section_padding_top, "bottom": profile.section_padding_bottom, "right": "80px", "left": "80px"}}},
            "tablet": {"value": {"padding": {"top": spt_t, "bottom": spb_t, "right": "48px", "left": "48px"}}},
            "phone": {"value": {"padding": {"top": spt_p, "bottom": spb_p, "right": "24px", "left": "24px"}}},
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
    accent_rgb = _hex_to_rgb(profile.accent)
    bg_dark_rgb = _hex_to_rgb(profile.bg_dark)
    cpt = getattr(profile, 'cta_padding_top', profile.section_padding_top)
    cpb = getattr(profile, 'cta_padding_bottom', profile.section_padding_bottom)
    cpt_t = getattr(profile, 'cta_padding_top_tablet', '80px')
    cpt_p = getattr(profile, 'cta_padding_top_phone', '64px')
    cpb_t = getattr(profile, 'cta_padding_bottom_tablet', '80px')
    cpb_p = getattr(profile, 'cta_padding_bottom_phone', '64px')

    gradient_stops = [
        {"color": f"rgba({accent_rgb},0.18)", "position": "0"},
        {"color": f"rgba({accent_rgb},0.04)", "position": "30"},
        {"color": f"rgba({bg_dark_rgb},0.6)", "position": "55"},
        {"color": f"rgba({bg_dark_rgb},0.95)", "position": "80"},
        {"color": profile.bg_dark, "position": "100"},
    ]
    gradient = {"type": "radial", "direction": "180deg", "stops": gradient_stops, "overlaysImage": "on"}

    dec = {
        "background": {
            "desktop": {
                "value": {
                    "color": profile.bg_dark,
                    "gradient": gradient,
                }
            }
        },
        "spacing": {
            "desktop": {"value": {"padding": {"top": cpt, "bottom": cpb, "right": "80px", "left": "80px"}}},
            "tablet": {"value": {"padding": {"top": cpt_t, "bottom": cpb_t, "right": "48px", "left": "48px"}}},
            "phone": {"value": {"padding": {"top": cpt_p, "bottom": cpb_p, "right": "24px", "left": "24px"}}},
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
    spt = getattr(profile, 'section_padding_top', '96px')
    spb = getattr(profile, 'section_padding_bottom', '96px')
    spt_t = getattr(profile, 'section_padding_top_tablet', '80px')
    spt_p = getattr(profile, 'section_padding_top_phone', '64px')
    spb_t = getattr(profile, 'section_padding_bottom_tablet', '80px')
    spb_p = getattr(profile, 'section_padding_bottom_phone', '64px')
    return {
        "background": {
            "desktop": {
                "value": {
                    "color": bg,
                }
            }
        },
        "spacing": {
            "desktop": {"value": {"padding": {"top": spt, "bottom": spb, "right": "80px", "left": "80px"}}},
            "tablet": {"value": {"padding": {"top": spt_t, "bottom": spb_t, "right": "48px", "left": "48px"}}},
            "phone": {"value": {"padding": {"top": spt_p, "bottom": spb_p, "right": "24px", "left": "24px"}}},
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

    if profile.card_style == "glass":
        accent_rgb = _hex_to_rgb(profile.accent)
        blur = getattr(profile, 'card_glass_blur', '20px')
        saturate = getattr(profile, 'card_glass_saturate', '1.4')
        card_dec["background"]["desktop"]["value"]["color"] = f"rgba({accent_rgb},0.05)"
        P = FRONTEND_PRINCIPLES["aesthetic"]["multi_shadow"]
        card_dec["boxShadow"] = {
            "desktop": {
                "value": {
                    "boxShadowHorizontal": P["card_ambient"]["x"],
                    "boxShadowVertical": P["card_ambient"]["y"],
                    "boxShadowBlur": P["card_ambient"]["blur"],
                    "boxShadowSpread": P["card_ambient"]["spread"],
                    "boxShadowColor": f"rgba({accent_rgb},0.06)",
                }
            }
        }
    elif profile.card_style == "solid":
        P = FRONTEND_PRINCIPLES["aesthetic"]["multi_shadow"]
        card_dec["boxShadow"] = {
            "desktop": {
                "value": {
                    "boxShadowHorizontal": "0px",
                    "boxShadowVertical": P["card_ambient"]["y"],
                    "boxShadowBlur": P["card_ambient"]["blur"],
                    "boxShadowSpread": P["card_ambient"]["spread"],
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
        accent_rgb = _hex_to_rgb(profile.accent)
        dec = {
            "button": {
                "desktop": {
                    "value": {
                        "backgroundColor": profile.accent,
                        "color": profile.bg_dark,
                        "borderRadius": profile.button_radius,
                        "padding": {
                            "top": "20px",
                            "bottom": "20px",
                            "left": "48px",
                            "right": "48px",
                        },
                        "font": profile.font_ui,
                        "size": "11px",
                        "letterSpacing": profile.button_letter_spacing,
                        "textTransform": profile.button_text_transform,
                    }
                }
            }
        }
        if profile.button_shadow_layers >= 3:
            P = FRONTEND_PRINCIPLES["aesthetic"]["multi_shadow"]
            ba = P["button_ambient"]
            bd = P["button_directional"]
            bi = P["button_inset"]
            dec["button"]["desktop"]["value"]["boxShadow"] = {
                "horizontal": "0px",
                "vertical": ba["y"],
                "blur": ba["blur"],
                "spread": ba["spread"],
                "color": f"rgba({accent_rgb},{ba['color'].split('{accent}')[-1]})",
            }
        return dec


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
    dec = {
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
    if getattr(profile, 'heading_text_shadow', False):
        accent_rgb = _hex_to_rgb(profile.accent)
        dec["font"]["desktop"]["value"]["textShadow"] = f"0 2px 12px rgba({accent_rgb},0.15)"
    return dec


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
    spt = getattr(profile, 'section_padding_top', '96px')
    spb = getattr(profile, 'section_padding_bottom', '96px')
    spt_t = getattr(profile, 'section_padding_top_tablet', '80px')
    spt_p = getattr(profile, 'section_padding_top_phone', '64px')
    spb_t = getattr(profile, 'section_padding_bottom_tablet', '80px')
    spb_p = getattr(profile, 'section_padding_bottom_phone', '64px')
    return {
        "background": {
            "desktop": {
                "value": {
                    "color": profile.bg_dark,
                }
            }
        },
        "spacing": {
            "desktop": {"value": {"padding": {"top": spt, "bottom": spb, "right": "80px", "left": "80px"}}},
            "tablet": {"value": {"padding": {"top": spt_t, "bottom": spb_t, "right": "48px", "left": "48px"}}},
            "phone": {"value": {"padding": {"top": spt_p, "bottom": spb_p, "right": "24px", "left": "24px"}}},
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
    spt_t = getattr(profile, 'section_padding_top_tablet', '80px')
    spt_p = getattr(profile, 'section_padding_top_phone', '64px')
    spb_t = getattr(profile, 'section_padding_bottom_tablet', '80px')
    spb_p = getattr(profile, 'section_padding_bottom_phone', '64px')
    return {
        "background": {
            "desktop": {
                "value": {
                    "color": profile.bg_mid,
                }
            }
        },
        "spacing": {
            "desktop": {"value": {"padding": {"top": profile.section_padding_top, "bottom": profile.section_padding_bottom, "right": "80px", "left": "80px"}}},
            "tablet": {"value": {"padding": {"top": spt_t, "bottom": spb_t, "right": "48px", "left": "48px"}}},
            "phone": {"value": {"padding": {"top": spt_p, "bottom": spb_p, "right": "24px", "left": "24px"}}},
        },
    }


def get_process_decoration(profile: DesignProfile) -> Dict[str, Any]:
    spt_t = getattr(profile, 'section_padding_top_tablet', '80px')
    spt_p = getattr(profile, 'section_padding_top_phone', '64px')
    spb_t = getattr(profile, 'section_padding_bottom_tablet', '80px')
    spb_p = getattr(profile, 'section_padding_bottom_phone', '64px')
    return {
        "background": {
            "desktop": {
                "value": {
                    "color": profile.bg_light,
                }
            }
        },
        "spacing": {
            "desktop": {"value": {"padding": {"top": profile.section_padding_top, "bottom": profile.section_padding_bottom, "right": "80px", "left": "80px"}}},
            "tablet": {"value": {"padding": {"top": spt_t, "bottom": spb_t, "right": "48px", "left": "48px"}}},
            "phone": {"value": {"padding": {"top": spt_p, "bottom": spb_p, "right": "24px", "left": "24px"}}},
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
