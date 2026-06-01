"""
ux_pro_bridge.py — Clasificador de estilo desde ui-ux-pro-max.

NO inyecta datos crudos (hex, font names, CSS) al pipeline. Solo clasifica
el estilo de una combinación tone+product_type para que el DIE tome mejores
decisiones Divi-nativas (variantes, atmósfera, animación, contraste).

Uso:
    from ux_pro_bridge import UXProBridge
    bridge = UXProBridge()
    style = bridge.classify("editorial", "aletheia")
    print(style["style_name"])       # "Liquid Glass"
    print(style["effects_tags"])     # ["morphing", "fluid", ...]
    print(style["variant_hint"])     # "liquid-glass"
"""

import sys, re
from pathlib import Path

UX_PRO_SCRIPTS = Path.home() / ".agents" / "skills" / "ui-ux-pro-max" / "scripts"
if UX_PRO_SCRIPTS.exists():
    sys.path.insert(0, str(UX_PRO_SCRIPTS))
else:
    UX_PRO_SCRIPTS = None


_TONE_QUERY_MAP = {
    "editorial": {
        "default": "editorial magazine premium typography",
        "aletheia": "editorial health wellness premium typography",
    },
    "luxury": {
        "default": "luxury premium high-end elegant",
        "aletheia": "luxury health premium wellness elegant",
    },
    "professional": {
        "default": "professional corporate clean minimal",
        "aletheia": "professional health medical clean",
    },
    "playful": {
        "default": "playful creative bold vibrant",
        "aletheia": "playful health wellness creative",
    },
    "minimal": {
        "default": "minimal clean modern simple",
        "aletheia": "minimal health clean modern",
    },
}

_DEFAULT_QUERY = "premium modern clean design"


def _build_query(tone: str, product_type: str = "") -> str:
    tone_map = _TONE_QUERY_MAP.get(tone, {})
    if not product_type:
        return tone_map.get("default", _DEFAULT_QUERY)
    key = product_type.lower().strip().split()[0] if product_type else ""
    if key in tone_map:
        return tone_map[key]
    return tone_map.get("default", _DEFAULT_QUERY)


# ── Mapa: style_name → decisiones Divi-nativas ─────────────────────────
# Cada estilo de ui-ux-pro-max se mapea a preferencias que el DIE puede
# usar sin contaminar decoration blocks con datos no-Divi.

_STYLE_VARIANT_MAP = {
    "liquid glass": "liquid-glass",
    "glassmorphism": "liquid-glass",
    "vibrant": "minimal-card",
    "bold": "minimal-card",
    "editorial": "editorial-grid",
    "magazine": "editorial-grid",
    "brutalist": "monochrome-brutalist",
    "monochrome": "monochrome-brutalist",
    "minimal": "glass-metric",
    "clean": "glass-metric",
    "professional": "glass-metric",
    "elegant": "liquid-glass",
    "luxury": "liquid-glass",
    "playful": "glass-cta",
    "creative": "glass-cta",
}

_STYLE_ATMOSPHERE_MAP = {
    "liquid glass": "gold-accent",
    "glassmorphism": "gold-accent",
    "vibrant": "vibrant",
    "bold": "vibrant",
    "editorial": "clean",
    "magazine": "clean",
    "minimal": "minimal",
    "clean": "minimal",
    "professional": "minimal",
    "elegant": "gold-accent",
    "luxury": "gold-accent",
    "playful": "vibrant",
    "creative": "vibrant",
}

_STYLE_ANIMATION_PROFILES = {
    "heavy": {"duration": "800ms", "delay_step": 150, "stagger": True},
    "medium": {"duration": "600ms", "delay_step": 100, "stagger": True},
    "light": {"duration": "400ms", "delay_step": 0, "stagger": False},
}

_STYLE_CONTRAST_MAP = {
    "high": {"bg": "surface-deep", "text": "text-on-dark", "accent": "premium"},
    "medium": {"bg": "surface-mid", "text": "text-on-dark", "accent": "accent"},
    "low": {"bg": "surface-light", "text": "ink", "accent": "accent"},
}


def _extract_effects_tags(effects_text: str) -> list:
    """Parse effects text into keyword tags for decision mapping."""
    if not effects_text:
        return []
    text = effects_text.lower()
    tags = []
    if "morph" in text: tags.append("morphing")
    if "fluid" in text: tags.append("fluid")
    if "blur" in text: tags.append("blur")
    if "glass" in text: tags.append("glass")
    if "shadow" in text or "depth" in text: tags.append("depth")
    if "gradient" in text: tags.append("gradient")
    if "minimal" in text: tags.append("minimal")
    if "animate" in text or "motion" in text: tags.append("animated")
    if "scroll" in text or "parallax" in text: tags.append("scroll")
    if "hover" in text or "transition" in text: tags.append("hover")
    if "bold" in text or "vibrant" in text: tags.append("bold")
    if "elegant" in text or "luxury" in text: tags.append("elegant")
    return tags


def _extract_aesthetic_keywords(keywords_text: str, category: str = "") -> list:
    """Extract aesthetic keywords from style keywords + category."""
    combined = f"{keywords_text} {category}".lower()
    tokens = re.split(r"[,;\s/]+", combined)
    seen = set()
    result = []
    for t in tokens:
        t = t.strip()
        if t and len(t) > 2 and t not in seen:
            seen.add(t)
            result.append(t)
    return result[:12]


def _map_animation_intensity(effects_tags: list, style_name: str = "") -> str:
    """Map effects + style to animation intensity: heavy/medium/light."""
    style_lower = style_name.lower()
    if any(t in ("morphing", "fluid", "glass") for t in effects_tags):
        return "heavy"
    if "minimal" in style_lower or "clean" in style_lower:
        return "light"
    if any(t in ("animated", "bold", "vibrant") for t in effects_tags):
        return "medium"
    return "medium"


def _map_contrast_level(effects_tags: list, style_name: str = "") -> str:
    """Map effects + style to contrast level: high/medium/low."""
    style_lower = style_name.lower()
    if "minimal" in style_lower or "clean" in style_lower:
        return "medium"
    if "editorial" in style_lower or "magazine" in style_lower:
        return "high"
    if any(t in ("elegant", "luxury") for t in effects_tags):
        return "high"
    if any(t in ("bold", "vibrant") for t in effects_tags):
        return "high"
    return "medium"


def _match_style_variant(style_name: str) -> str:
    """Encuentra la mejor variante Divi para un style_name."""
    style_lower = style_name.lower()
    for key, variant in _STYLE_VARIANT_MAP.items():
        if key in style_lower or style_lower in key:
            return variant
    return ""


def _match_atmosphere(style_name: str) -> str:
    style_lower = style_name.lower()
    for key, atmosphere in _STYLE_ATMOSPHERE_MAP.items():
        if key in style_lower or style_lower in key:
            return atmosphere
    return "clean"


class UXProBridge:
    """Clasificador de estilo desde ui-ux-pro-max. No inyecta datos crudos."""

    def __init__(self):
        self._gen = None
        self._ready = False
        self._init_error = None
        self._init()

    def _init(self):
        if UX_PRO_SCRIPTS is None:
            self._init_error = "ui-ux-pro-max scripts dir not found"
            return
        try:
            from design_system import DesignSystemGenerator
            self._gen = DesignSystemGenerator()
            self._ready = True
        except ImportError as e:
            self._init_error = f"Import DesignSystemGenerator failed: {e}"
        except Exception as e:
            self._init_error = f"Init DesignSystemGenerator failed: {e}"

    @property
    def is_ready(self) -> bool:
        return self._ready

    def classify(self, tone: str = "editorial", product_type: str = "") -> dict:
        """Clasifica el estilo de tone+product_type para informar decisiones Divi.

        Returns:
            Dict con claves Divi-nativas:
            - style_name: nombre del estilo recomendado
            - category: categoría de producto detectada
            - effects_tags: lista de keywords de efectos
            - aesthetic_keywords: lista de keywords estéticas
            - variant_hint: variante de section-schema.json preferida
            - atmosphere_hint: clave de atmósfera preferida
            - animation_profile: {duration, delay_step, stagger}
            - contrast_level: "high", "medium", "low"
            - pattern_name: nombre del patrón de landing page
            Dict vacío si hay error.
        """
        if not self._ready or not self._gen:
            return {}

        query = _build_query(tone, product_type)
        name = f"{tone} {product_type}".strip()
        try:
            raw = self._gen.generate(query, name)
        except Exception:
            return {}
        if not isinstance(raw, dict):
            return {}

        style = raw.get("style", {})
        pattern = raw.get("pattern", {})
        effects = raw.get("key_effects", "") + " " + style.get("effects", "")
        keywords = style.get("keywords", "")
        category = raw.get("category", "")
        style_name = style.get("name", "")

        effects_tags = _extract_effects_tags(effects)
        aesthetic_keywords = _extract_aesthetic_keywords(keywords, category)
        variant_hint = _match_style_variant(style_name)
        atmosphere_hint = _match_atmosphere(style_name)
        intensity = _map_animation_intensity(effects_tags, style_name)
        contrast = _map_contrast_level(effects_tags, style_name)
        anim = _STYLE_ANIMATION_PROFILES.get(intensity, _STYLE_ANIMATION_PROFILES["medium"])

        return {
            "style_name": style_name,
            "category": category,
            "effects_tags": effects_tags,
            "aesthetic_keywords": aesthetic_keywords,
            "variant_hint": variant_hint,
            "atmosphere_hint": atmosphere_hint,
            "animation_profile": {
                "duration": anim["duration"],
                "delay_step_ms": anim["delay_step"],
                "stagger": anim["stagger"],
            },
            "contrast_level": contrast,
            "pattern_name": pattern.get("name", ""),
            "pattern_sections": pattern.get("sections", ""),
        }

    def last_error(self) -> str:
        return self._init_error or ""
