"""
ux_pro_bridge.py — Puente real entre DesignSystemGenerator y VIE.

El DesignSystemGenerator (BM25 sobre 5 CSVs) produce estilo, colores,
tipografía, efectos, anti-patrones. Este adaptador traduce ESO a
design_direction que VIE entiende: mood + overrides directos del
DesignProfile (card_style, motion, texturas, stagger).

NO sobreescribe colores de marca — esos vienen de _design_vars.json.
El bridge solo mapea INTENCIÓN DE DISEÑO a parámetros VIE.

Uso:
    from ux_pro_bridge import UXProBridge
    bridge = UXProBridge()
    dd = bridge.to_design_direction("aerolinea de lujo", "AeroLuxe")
    brief["design_direction"] = dd
"""

import sys, re
from pathlib import Path

# Buscar scripts de ui-ux-pro-max: primero en skills, luego en DAW_bundle local
UX_PRO_SCRIPTS = Path.home() / ".agents" / "skills" / "ui-ux-pro-max" / "scripts"
if not UX_PRO_SCRIPTS.exists():
    UX_PRO_SCRIPTS = Path(__file__).resolve().parent.parent.parent / "ui-ux-pro-max" / "scripts"
if UX_PRO_SCRIPTS.exists():
    sys.path.insert(0, str(UX_PRO_SCRIPTS))
else:
    UX_PRO_SCRIPTS = None

# ── Mapeo: pattern de texto del Generator → mood VIE ─────────────────────

_STYLE_TO_MOOD = [
    (r"glass|aurora|neon|cyber|tech|futur|digital|sleek|interface", "tech_glass"),
    (r"luxury|elegant|premium|gold|sophisticated|high.end|refined|exclusive|opulent|lujo|lujoso|elegante|dorado", "academic_night"),
    (r"cool|corporate|professional|clean|modern|apple|enterprise|business|sass", "cool_luxury"),
    (r"warm|cozy|organic|natural|earthy|rustic|comfort|wellness|boho|serene", "organic_modern"),
    (r"minimal|simple|serene|soft|gentle|calm|muted|editorial|magazine|quiet", "warm_minimal"),
]

_LUXURY_BOOST_WORDS = [
    "luxury", "premium", "elegant", "gold", "sophisticated",
    "opulent", "exclusive", "high-end", "refined", "concierge",
    # Español
    "lujo", "lujoso", "elegante", "dorado", "exclusivo", "premium",
]


def _detect_mood(style_name: str, keywords: str, effects_text: str, query: str = "") -> str:
    combined = f"{query} {style_name} {keywords} {effects_text}".lower()
    scores = {}
    for pattern, mood in _STYLE_TO_MOOD:
        score = len(re.findall(pattern, combined))
        if score > 0:
            scores[mood] = score

    # Luxury semantic boost: si el texto contiene keywords de lujo,
    # academic_night gana aunque BM25 haya devuelto "Liquid Glass"
    has_luxury = any(w in combined for w in _LUXURY_BOOST_WORDS)
    if has_luxury and "academic_night" in scores:
        scores["academic_night"] += 3

    return max(scores, key=scores.get) if scores else "cool_luxury"


# ── Efectos: texto libre → tags estructurados ────────────────────────────

_EFFECTS_RULES = [
    (r"blur|glass|frost|transparent|backdrop", "glass"),
    (r"gradient|vibrant|colorful|mesh", "gradient"),
    (r"shadow|depth|z.depth|layer|dimensional", "depth"),
    (r"animate|transition|motion|reveal|fade|slide", "animated"),
    (r"parallax|scroll|sticky", "scroll"),
    (r"reflection|shiny|gloss|pearl|lustre", "elegant"),
    (r"grain|texture|noise|grunge|rough", "grain"),
    (r"glow|neon|radiant|luminous", "glow"),
]


def _parse_effects_to_tags(effects_text: str) -> list:
    if not effects_text:
        return []
    text = effects_text.lower()
    tags = []
    seen = set()
    for pattern, tag in _EFFECTS_RULES:
        if re.search(pattern, text) and tag not in seen:
            tags.append(tag)
            seen.add(tag)
    return tags


# ── Mapeos por mood (copy exacta de design_director.py) ──────────────────

_MOOD_METADATA = {
    "academic_night": {
        "color_temperature": "warm_on_dark",
        "typography_style": "serif_display_plus_sans_ui",
        "layout_rhythm": "dramatic_asymmetric",
        "spacing_density": "generous",
        "accent_material": "gold_antique",
        "motion_intensity": "subtle_parallax",
    },
    "cool_luxury": {
        "color_temperature": "neutral_cool",
        "typography_style": "sans_premium",
        "layout_rhythm": "centered",
        "spacing_density": "comfortable",
        "accent_material": "blue_chrome",
        "motion_intensity": "subtle",
    },
    "warm_minimal": {
        "color_temperature": "warm_light",
        "typography_style": "serif_humanist",
        "layout_rhythm": "symmetrical_grid",
        "spacing_density": "expansive",
        "accent_material": "terracotta",
        "motion_intensity": "gentle",
    },
    "tech_glass": {
        "color_temperature": "cool_on_dark",
        "typography_style": "mono_plus_sans",
        "layout_rhythm": "full_bleed_dynamic",
        "spacing_density": "dramatic",
        "accent_material": "cyan_neon",
        "motion_intensity": "dramatic",
    },
    "organic_modern": {
        "color_temperature": "warm_natural",
        "typography_style": "serif_natural_plus_sans",
        "layout_rhythm": "grid_masonry",
        "spacing_density": "generous",
        "accent_material": "sage_green",
        "motion_intensity": "subtle_parallax",
    },
}


def _overrides_from_effects(effects_tags: list) -> dict:
    """Convierte effects_tags en overrides directos de DesignProfile."""
    o = {}
    tag_set = set(effects_tags)

    if "glass" in tag_set:
        o["card_style"] = "glass"

    if "glow" in tag_set:
        o["card_style"] = "glass"
        o["heading_text_shadow"] = True

    if "depth" in tag_set:
        o["heading_text_shadow"] = True
        o["button_shadow_layers"] = 3

    if "gradient" in tag_set:
        o["button_gradient"] = True

    if "grain" in tag_set:
        o["grain_texture"] = True

    if "animated" in tag_set or "scroll" in tag_set:
        o["stagger_hero"] = True
        o["stagger_cta"] = True
        o["stagger_stats"] = True

    if "elegant" in tag_set:
        o["card_style"] = "glass"
        o["card_border_width"] = "1px"
        o["title_divider"] = True

    return o


# =========================================================================
#  Bridge
# =========================================================================

class UXProBridge:
    """Ejecuta DesignSystemGenerator y traduce su output a design_direction.

    Tres capas de output:
    1. mood + metadata (color_temperature, layout_rhythm, etc.)
    2. effects_tags (decoración contextual)
    3. overrides directos de DesignProfile (card_style, texturas, stagger)
    """

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
        except Exception as e:
            self._init_error = str(e)

    @property
    def is_ready(self) -> bool:
        return self._ready

    def to_design_direction(self, query: str, project_name: str = "") -> dict:
        """Ejecuta el Generator y traduce a design_direction."""
        if not self._ready or not self._gen:
            return self._fallback()

        try:
            raw = self._gen.generate(query, project_name or query)
        except Exception:
            return self._fallback()

        if not isinstance(raw, dict):
            return self._fallback()

        style = raw.get("style", {})
        typography = raw.get("typography", {})
        pattern = raw.get("pattern", {})

        style_name = style.get("name", "")
        keywords = style.get("keywords", "")
        effects_text = style.get("effects", "") or raw.get("key_effects", "")

        mood = _detect_mood(style_name, keywords, effects_text, query)
        effects_tags = _parse_effects_to_tags(effects_text)
        meta = dict(_MOOD_METADATA.get(mood, _MOOD_METADATA["cool_luxury"]))

        if effects_tags:
            meta["motion_intensity"] = "dramatic" if "scroll" in effects_tags else meta["motion_intensity"]

        overrides = _overrides_from_effects(effects_tags)

        dd = {
            "mood": mood,
            "effects_tags": effects_tags,
        }

        if overrides:
            dd.update(overrides)

        dd["_meta"] = {
            "color_temperature": meta.get("color_temperature", "neutral_cool"),
            "typography_style": meta.get("typography_style", "sans_premium"),
            "layout_rhythm": meta.get("layout_rhythm", "centered"),
            "spacing_density": meta.get("spacing_density", "comfortable"),
            "accent_material": meta.get("accent_material", "blue_chrome"),
            "motion_intensity": meta.get("motion_intensity", "subtle"),
            "source_style": style_name,
            "source_category": raw.get("category", ""),
        }

        if pattern and pattern.get("name"):
            dd["_meta"]["pattern_name"] = pattern.get("name", "")
            dd["_meta"]["pattern_sections"] = pattern.get("sections", "")

        dd["_anti_patterns"] = raw.get("anti_patterns", "")
        dd["_decision_rules"] = raw.get("decision_rules", {})

        return dd

    def _fallback(self) -> dict:
        return {
            "mood": "cool_luxury",
            "effects_tags": [],
            "_meta": {
                "color_temperature": "neutral_cool",
                "typography_style": "sans_premium",
                "layout_rhythm": "centered",
                "spacing_density": "comfortable",
                "accent_material": "blue_chrome",
                "motion_intensity": "subtle",
                "source_style": "",
                "source_category": "",
            },
        }

    def last_error(self) -> str:
        return self._init_error or ""
