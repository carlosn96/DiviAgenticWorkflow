"""StrategyProfile Protocol — encapsulates per-strategy behavior.

The Profile replaces stringly-typed checks like `"glass" in self.strategy`
throughout the codebase with a typed object that exposes:
  - contains_glass(), is_dark_background(), is_minimal()
  - preferred_blocks, avoid_blocks
  - preset_map: section_type → list of section preset names
  - glow_intensity: "none" | "low" | "medium" | "high"
  - glass_bg_alpha: 0.0..1.0

Profiles are pure data + tiny predicate methods; new strategies = 1 file.
"""
from typing import Any, Dict, List, Optional, Protocol

from daw.types import SectionType, Strategy


class StrategyProfile(Protocol):
    """Encapsulates all strategy-specific behavior."""
    name: str
    preferred_blocks: List[str]
    avoid_blocks: List[str]

    # Aesthetic knobs
    glass_enabled: bool
    glow_intensity: str
    glass_bg_alpha: float
    background_preference: str  # "dark" | "light"

    # Per-section preset resolution: section_type -> list of preset refs
    preset_map: Dict[str, List[str]]

    # ── Predicates (replace substring matching) ──
    def contains_glass(self) -> bool: ...
    def contains_luxury(self) -> bool: ...
    def is_dark_background(self) -> bool: ...
    def is_minimal(self) -> bool: ...
    def get_presets_for(self, section_type: str) -> List[str]: ...


# ─── Concrete profiles ─────────────────────────────────────────────────

COOL_LUXURY_PROFILE: Dict[str, Any] = {
    "name": "cool-luxury",
    "preferred_blocks": ["hero_glass", "features_glass_grid", "stats_dark_counters",
                         "testimonials_white_cards", "pricing_glass_tables", "cta_epic"],
    "avoid_blocks": ["features_light_grid"],
    "glass_enabled": True,
    "glow_intensity": "medium",
    "glass_bg_alpha": 0.88,
    "background_preference": "dark",
    "preset_map": {
        SectionType.HERO.value: ["section:hero-glass", "section:hero-dark"],
        SectionType.HERO_SPLIT.value: ["section:hero-glass"],
        SectionType.HERO_CENTERED.value: ["section:hero-dark"],
        SectionType.FEATURES.value: ["section:dark", "section:light"],
        SectionType.STATS.value: ["section:dark", "section:light"],
        SectionType.FAQ.value: ["section:dark", "section:light"],
        SectionType.PRICING.value: ["section:dark", "section:light"],
        SectionType.TESTIMONIALS.value: ["section:white"],
        SectionType.CTA.value: ["section:cta-epic"],
    },
}

WARM_LUXURY_PROFILE: Dict[str, Any] = {
    "name": "warm-luxury",
    "preferred_blocks": ["hero_glass", "features_glass_grid", "stats_dark_counters",
                         "testimonials_white_cards", "pricing_glass_tables", "cta_epic"],
    "avoid_blocks": ["features_light_grid"],
    "glass_enabled": True,
    "glow_intensity": "high",
    "glass_bg_alpha": 0.85,
    "background_preference": "dark",
    "preset_map": {
        SectionType.HERO.value: ["section:hero-glass", "section:hero-dark"],
        SectionType.HERO_SPLIT.value: ["section:hero-glass"],
        SectionType.HERO_CENTERED.value: ["section:hero-dark"],
        SectionType.FEATURES.value: ["section:dark", "section:light"],
        SectionType.STATS.value: ["section:dark", "section:light"],
        SectionType.FAQ.value: ["section:dark", "section:light"],
        SectionType.PRICING.value: ["section:dark", "section:light"],
        SectionType.TESTIMONIALS.value: ["section:white"],
        SectionType.CTA.value: ["section:cta-epic"],
    },
}

TECH_GLASS_PROFILE: Dict[str, Any] = {
    "name": "tech-glass",
    "preferred_blocks": ["hero_glass", "features_glass_grid", "testimonials_white_cards",
                         "cta_epic", "stats_dark_counters"],
    "avoid_blocks": ["features_light_grid", "pricing_glass_tables"],
    "glass_enabled": True,
    "glow_intensity": "high",
    "glass_bg_alpha": 0.80,
    "background_preference": "dark",
    "preset_map": {
        SectionType.HERO.value: ["section:hero-glass"],
        SectionType.HERO_SPLIT.value: ["section:hero-glass"],
        SectionType.HERO_CENTERED.value: ["section:hero-dark"],
        SectionType.FEATURES.value: ["section:dark", "section:light"],
        SectionType.STATS.value: ["section:dark", "section:light"],
        SectionType.FAQ.value: ["section:dark", "section:light"],
        SectionType.PRICING.value: ["section:light"],
        SectionType.TESTIMONIALS.value: ["section:white"],
        SectionType.CTA.value: ["section:cta-epic"],
    },
}

MINIMAL_PROFILE: Dict[str, Any] = {
    "name": "minimal",
    "preferred_blocks": ["hero_dark_centered", "features_light_grid", "testimonials",
                         "faq", "cta_epic"],
    "avoid_blocks": ["hero_glass", "features_glass_grid", "pricing_glass_tables"],
    "glass_enabled": False,
    "glow_intensity": "none",
    "glass_bg_alpha": 1.0,
    "background_preference": "light",
    "preset_map": {
        SectionType.HERO.value: ["section:hero-dark"],
        SectionType.HERO_SPLIT.value: ["section:hero-dark"],
        SectionType.HERO_CENTERED.value: ["section:hero-dark"],
        SectionType.FEATURES.value: ["section:light"],
        SectionType.STATS.value: ["section:light"],
        SectionType.FAQ.value: ["section:light"],
        SectionType.PRICING.value: ["section:light"],
        SectionType.TESTIMONIALS.value: ["section:white"],
        SectionType.CTA.value: ["section:cta-epic"],
    },
}

ORGANIC_PROFILE: Dict[str, Any] = {
    "name": "organic",
    "preferred_blocks": ["hero_dark_centered", "features_light_grid", "testimonials",
                         "timeline", "cta_epic"],
    "avoid_blocks": ["hero_glass", "pricing_glass_tables"],
    "glass_enabled": False,
    "glow_intensity": "low",
    "glass_bg_alpha": 1.0,
    "background_preference": "light",
    "preset_map": {
        SectionType.HERO.value: ["section:hero-dark"],
        SectionType.HERO_SPLIT.value: ["section:hero-dark"],
        SectionType.HERO_CENTERED.value: ["section:hero-dark"],
        SectionType.FEATURES.value: ["section:light"],
        SectionType.STATS.value: ["section:light"],
        SectionType.FAQ.value: ["section:light"],
        SectionType.PRICING.value: ["section:light"],
        SectionType.TESTIMONIALS.value: ["section:white"],
        SectionType.CTA.value: ["section:cta-epic"],
    },
}

# Map Strategy enum → profile dict
_PROFILE_BY_STRATEGY: Dict[str, Dict[str, Any]] = {
    Strategy.COOL_LUXURY.value: COOL_LUXURY_PROFILE,
    Strategy.WARM_LUXURY.value: WARM_LUXURY_PROFILE,
    Strategy.TECH_GLASS.value: TECH_GLASS_PROFILE,
    Strategy.MINIMAL.value: MINIMAL_PROFILE,
    Strategy.ORGANIC.value: ORGANIC_PROFILE,
}


def get_profile(strategy: str) -> Dict[str, Any]:
    """Look up a strategy profile. Falls back to MINIMAL for unknown values."""
    return _PROFILE_BY_STRATEGY.get(strategy, MINIMAL_PROFILE)


# ─── Predicate helpers (Strategy-method-compatible) ────────────────────

def _contains_glass(profile: Dict[str, Any]) -> bool:
    return bool(profile.get("glass_enabled"))


def _is_dark_background(profile: Dict[str, Any]) -> bool:
    return profile.get("background_preference") == "dark"


def _is_minimal(profile: Dict[str, Any]) -> bool:
    return profile.get("name") == "minimal"


def _contains_luxury(profile: Dict[str, Any]) -> bool:
    name = profile.get("name", "")
    return "luxury" in name


def _get_presets_for(profile: Dict[str, Any], section_type: str) -> List[str]:
    return list(profile.get("preset_map", {}).get(section_type, []))


# Wrap the dict as a StrategyProfile-compatible object.
class StrategyProfileImpl:
    """Lightweight object exposing the StrategyProfile Protocol surface."""

    def __init__(self, data: Dict[str, Any]):
        self._data = data

    @property
    def name(self) -> str:
        return self._data["name"]

    @property
    def preferred_blocks(self) -> List[str]:
        return self._data.get("preferred_blocks", [])

    @property
    def avoid_blocks(self) -> List[str]:
        return self._data.get("avoid_blocks", [])

    @property
    def glass_enabled(self) -> bool:
        return self._data.get("glass_enabled", False)

    @property
    def glow_intensity(self) -> str:
        return self._data.get("glow_intensity", "none")

    @property
    def glass_bg_alpha(self) -> float:
        return self._data.get("glass_bg_alpha", 1.0)

    @property
    def background_preference(self) -> str:
        return self._data.get("background_preference", "light")

    @property
    def preset_map(self) -> Dict[str, List[str]]:
        return self._data.get("preset_map", {})

    def contains_glass(self) -> bool:
        return _contains_glass(self._data)

    def contains_luxury(self) -> bool:
        return _contains_luxury(self._data)

    def is_dark_background(self) -> bool:
        return _is_dark_background(self._data)

    def is_minimal(self) -> bool:
        return _is_minimal(self._data)

    def get_presets_for(self, section_type: str) -> List[str]:
        return _get_presets_for(self._data, section_type)


def get_profile_obj(strategy: str) -> StrategyProfileImpl:
    """Return a typed StrategyProfile object for the given strategy name."""
    return StrategyProfileImpl(get_profile(strategy))
