"""
Visual Impact Engine v3.0 — Schema-Driven Rich Page Generator
===============================================================
Deterministic translator: brief + design system + catalog + dataset → page-def.json RICO.

Uses:
  1. Divi Catalog (127 native props from divi_catalog.json)
  2. Divi+ Dataset (12 high-impact block patterns from diviplus_dataset.json)
  3. Brand vars (tokens from design-system/divitheme.json)
  4. Frontend-design principles (perceptual color, spacing rhythm, contrast)

No LLMs. No randomness. All decisions are deterministic lookups.
"""

import json
import os
import copy
import random
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

DAW_ROOT = Path(__file__).resolve().parent.parent.parent


def _load_daw_site() -> str:
    site = os.environ.get('DAW_SITE')
    if site:
        return site
    env_path = os.path.join(os.path.dirname(DAW_ROOT), '.env')
    if os.path.exists(env_path):
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('DAW_SITE='):
                        val = line[9:].strip().strip('"').strip("'")
                        if val:
                            return val
        except Exception:
            pass
    if '-h' in os.sys.argv or '--help' in os.sys.argv:
        return 'example'
    print("[ERROR] DAW_SITE no está definido.", file=os.sys.stderr)
    os.sys.exit(1)


# ===============================================================
# 1. CATALOG LOADER — knows every Divi native prop
# ===============================================================

class CatalogLoader:
    """Loads and provides structured access to the Divi prop catalog."""

    def __init__(self, catalog_path: Optional[Path] = None):
        self.catalog_path = catalog_path or (DAW_ROOT / "workspace" / "data" / "divi_catalog.json")
        self.catalog: Dict = {}
        self.prop_index: Dict[str, Dict] = {}
        self._load()

    def _load(self):
        with open(self.catalog_path, 'r', encoding='utf-8') as f:
            self.catalog = json.load(f)
        # Flatten prop index
        for category, props in self.catalog.items():
            if category.startswith('_'):
                continue
            for prop_name, prop_def in props.items():
                self.prop_index[prop_name] = {**prop_def, "category": category}

    def get_prop(self, name: str) -> Optional[Dict]:
        return self.prop_index.get(name)

    def get_path(self, name: str) -> Optional[str]:
        prop = self.get_prop(name)
        return prop.get("path") if prop else None

    def get_pattern(self, name: str, pattern_name: str) -> Optional[Any]:
        prop = self.get_prop(name)
        if not prop:
            return None
        patterns = prop.get("patterns", {})
        return patterns.get(pattern_name)

    def validate_value(self, name: str, value: Any) -> bool:
        """Validate if a value matches the prop's schema."""
        prop = self.get_prop(name)
        if not prop:
            return True  # Unknown props pass through
        prop_type = prop.get("type")
        if prop_type == "enum":
            valid_values = prop.get("values", [])
            return value in valid_values if valid_values else True
        if prop_type == "object":
            return isinstance(value, dict)
        if prop_type == "color":
            return isinstance(value, str) and (value.startswith('#') or value.startswith('{{') or value.startswith('rgba') or value.startswith('var('))
        return True

    def get_props_by_category(self, category: str) -> Dict[str, Dict]:
        return {k: v for k, v in self.prop_index.items() if v.get("category") == category}

    def list_high_impact(self) -> List[str]:
        """Props marked as high or very_high impact."""
        result = []
        for name, prop in self.prop_index.items():
            impact = prop.get("impact", "low")
            if impact in ("high", "very_high", "medium"):
                result.append(name)
        return result


# ===============================================================
# 2. DATASET LOADER — knows winning block combinations
# ===============================================================

class DatasetLoader:
    """Loads the Divi+ dataset and provides block resolution."""

    def __init__(self, dataset_path: Optional[Path] = None):
        self.dataset_path = dataset_path or (DAW_ROOT / "workspace" / "data" / "diviplus_dataset.json")
        self.dataset: Dict = {}
        self.blocks: Dict[str, Dict] = {}
        self.combination_rules: Dict = {}
        self.strategy_adaptation: Dict = {}
        self.impact_weights: Dict = {}
        self._load()

    def _load(self):
        with open(self.dataset_path, 'r', encoding='utf-8') as f:
            self.dataset = json.load(f)
        self.blocks = self.dataset.get("blocks", {})
        self.combination_rules = self.dataset.get("combination_rules", {})
        self.strategy_adaptation = self.dataset.get("strategy_adaptation", {})
        self.impact_weights = self.dataset.get("impact_scoring_weights", {})

    def get_block(self, block_id: str) -> Optional[Dict]:
        return self.blocks.get(block_id)

    def find_compatible_blocks(self, section_type: str, strategy: str) -> List[Dict]:
        """Find blocks that match section_type and strategy."""
        matches = []
        for block in self.blocks.values():
            if block.get("section_type") != section_type:
                continue
            compatible = block.get("compatible_strategies", [])
            contras = block.get("contraindications", [])

            # Check strategy match
            if compatible and strategy not in compatible:
                continue

            # Check contraindications
            if "bg_is_light" in contras and strategy in ("minimal", "clean"):
                continue

            matches.append(block)

        # Sort by impact_score descending
        matches.sort(key=lambda x: x.get("impact_score", 0), reverse=True)
        return matches

    def get_best_block(self, section_type: str, strategy: str) -> Optional[Dict]:
        matches = self.find_compatible_blocks(section_type, strategy)
        return matches[0] if matches else None

    def get_strategy_adaptation(self, strategy: str) -> Dict:
        return self.strategy_adaptation.get(strategy, {})

    def score_decoration_set(self, props_used: List[str]) -> int:
        """Score a set of props by impact weight."""
        score = 0
        for prop in props_used:
            score += self.impact_weights.get(prop, 1)
        return score

    def get_combination_rule(self, rule_name: str) -> Optional[Dict]:
        return self.combination_rules.get(rule_name)


# ===============================================================
# 3. BRAND RESOLVER — adapts tokens automatically
# ===============================================================

class BrandResolver:
    """Resolves {{design:*}} tokens using the design system."""

    def __init__(self, design_system: Dict[str, Any]):
        self.ds = design_system
        self.tokens = design_system.get("tokens", {})
        self.presets = design_system.get("presets", {})
        self.strategy = design_system.get("strategy", "generic")

    def has_token(self, token_name: str) -> bool:
        for cat in self.tokens.values():
            if isinstance(cat, dict) and token_name in cat:
                return True
        return False

    def has_preset(self, category: str, name: str) -> bool:
        return category in self.presets and name in self.presets[category]

    def resolve(self, token_expr: str) -> str:
        """Resolve {{design:type:name}} -> value, including within larger strings."""
        if not isinstance(token_expr, str):
            return token_expr

        import re
        def _replace(match):
            inner = match.group(0).strip("{}").replace("design:", "")
            parts = inner.split(":")
            if len(parts) >= 2:
                cat, name = parts[0], parts[1]
                cat_data = self.tokens.get(cat, {})
                if isinstance(cat_data, dict) and name in cat_data:
                    return cat_data[name]
            return match.group(0)

        return re.sub(r'\{\{design:([^}]+)\}\}', _replace, token_expr)

    def resolve_deep(self, obj: Any) -> Any:
        """Deep-resolve all tokens in a nested structure."""
        if isinstance(obj, str):
            return self.resolve(obj)
        if isinstance(obj, dict):
            return {k: self.resolve_deep(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self.resolve_deep(item) for item in obj]
        return obj

    def get_token_value(self, category: str, name: str) -> Optional[str]:
        cat_data = self.tokens.get(category, {})
        if isinstance(cat_data, dict):
            return cat_data.get(name)
        return None

    def get_strategy(self) -> str:
        return self.strategy


# ===============================================================
# 4a. PAGE PROFILE ANALYZER — content-aware analysis
# ===============================================================

class PageProfileAnalyzer:
    """Analyzes brief content to derive narrative profile, content density, and contrast requirements."""

    _NARRATIVE_SIGNALS = {
        "landing": {
            "triggers": lambda b, sts: (
                any("hero" in s for s in sts)
                and any(s == "cta" for s in sts)
                and (any(s == "pricing" for s in sts) or any(s == "testimonials" for s in sts))
            ),
            "tone_weight": {"professional": 0.3, "luxury": 0.3, "tech": 0.2},
        },
        "story": {
            "triggers": lambda b, sts: (
                b.get("tone") in ("editorial", "warm", "organic")
                and not any(s == "pricing" for s in sts)
            ) or any(s == "timeline" for s in sts),
            "tone_weight": {"editorial": 0.3, "warm": 0.3, "organic": 0.2},
        },
        "educational": {
            "triggers": lambda b, sts: (
                any("hero" in s for s in sts)
                and any(s == "faq" for s in sts)
                and b.get("tone") in ("educational", "professional")
            ),
            "tone_weight": {"educational": 0.3, "professional": 0.1},
        },
        "showcase": {
            "triggers": lambda b, sts: (
                any(s == "gallery" for s in sts)
                or b.get("product_type") in ("portfolio", "gallery", "agency")
            ),
            "tone_weight": {"vibrant": 0.3, "luxury": 0.2, "tech": 0.1},
        },
    }

    @staticmethod
    def detect_narrative_profile(brief: Dict) -> str:
        """Detect narrative profile from tone + product_type + section_types."""
        sections = brief.get("sections", [])
        section_types = [s.get("section_type", "") for s in sections]

        scores = {}
        for profile, signals in PageProfileAnalyzer._NARRATIVE_SIGNALS.items():
            s = 0.0
            if signals["triggers"](brief, section_types):
                s += 0.6
            tone_bonus = signals["tone_weight"].get(brief.get("tone", ""), 0)
            s += tone_bonus
            scores[profile] = s

        if not scores:
            return "landing"
        return max(scores, key=scores.get)

    @staticmethod
    def profile_section(sec_def: Dict) -> Dict:
        """Profile a section's actual content for block matching."""
        items = sec_def.get("items", [])
        stats = sec_def.get("stats", [])
        testimonials = sec_def.get("testimonials", [])
        faqs = sec_def.get("faqs", [])
        features = sec_def.get("features", [])

        all_items = items or stats or testimonials or faqs or features
        has_icons = bool(all_items and all_items[0].get("icon"))
        has_images = bool(all_items and all_items[0].get("image")) or bool(sec_def.get("image"))
        has_cta = bool(sec_def.get("btn_primary_text"))
        has_long_text = any(len(i.get("text", i.get("content", ""))) > 100 for i in all_items)

        return {
            "n_items": len(all_items) or 1,
            "has_icons": has_icons,
            "has_images": has_images,
            "has_cta": has_cta,
            "has_long_text": has_long_text,
            "section_type": sec_def.get("section_type", "generic"),
        }

    @staticmethod
    def build_contrast_plan(sections: List[Dict], strategy: str) -> List[Dict]:
        """Build a contrast arc plan for the entire page."""

        def _bg_type(st: str, strat: str) -> str:
            if st in ("hero", "hero-split", "hero-centered"):
                return "dark_deep"
            if st == "testimonials":
                return "light"
            if st == "cta":
                return "dark_deep"
            if st in ("features", "stats", "pricing"):
                return "dark" if "glass" in strat or "luxury" in strat else "light"
            if st == "faq":
                return "dark" if "glass" in strat or "luxury" in strat else "light"
            if st == "gallery":
                return "light"
            return "light"

        transitions = []
        section_types = [s.get("section_type", "generic") for s in sections]
        previous_bg = None

        for i, st in enumerate(section_types):
            current_bg = _bg_type(st, strategy)

            if previous_bg is None:
                ttype = "start"
            elif previous_bg.startswith("dark") and current_bg.startswith("light"):
                ttype = "break"
            elif previous_bg.startswith("light") and current_bg.startswith("dark"):
                ttype = "break"
            elif previous_bg == current_bg:
                ttype = "match"
            else:
                ttype = "subtle_shift"

            if st == "cta" and i == len(section_types) - 1:
                ttype = "climax"

            transitions.append({"index": i, "transition": ttype, "bg": current_bg})
            previous_bg = current_bg

        return transitions


# ===============================================================
# 4b. BLOCK SELECTION ENGINE — intelligent context-aware selection
# ===============================================================

class BlockSelectionEngine:
    """
    Intelligent block selection using weighted 4D scoring:
    1. Strategy Alignment — compatibility with brand strategy (20%)
    2. Content Density Fit — structure matches actual content (25%)
    3. Visual Harmony — continuity with previous section (25%)
    4. Narrative Bias — aligns with page narrative profile (15%)
    + Impact bonus — raw impact_score as tiebreaker (15%)

    Also builds harmony matrix between blocks for contrast arc planning.
    """

    _NARRATIVE_BIAS = {
        "landing": {
            "preferred": ["hero_glass", "features_glass", "cta_epic", "pricing_glass", "stats_dark"],
            "avoid": ["features_light", "timeline", "gallery_masonry"],
            "contrast": "high",
        },
        "story": {
            "preferred": ["testimonials", "timeline", "features_light", "hero_dark_centered"],
            "avoid": ["pricing_glass", "features_glass"],
            "contrast": "medium",
        },
        "educational": {
            "preferred": ["faq", "features_light", "hero_dark_centered", "cta_epic"],
            "avoid": ["gallery_masonry", "pricing_glass"],
            "contrast": "low",
        },
        "showcase": {
            "preferred": ["gallery_masonry", "features_glass", "hero_glass", "testimonials"],
            "avoid": ["faq", "pricing_glass"],
            "contrast": "medium",
        },
    }

    def __init__(self, dataset: DatasetLoader, strategy: str, strategy_adapt: Dict):
        self.dataset = dataset
        self.strategy = strategy
        self.strategy_adapt = strategy_adapt
        self.harmony_matrix = self._build_harmony_matrix()

    def _derive_columns(self, block: Dict) -> int:
        """Derive column count from block layout string."""
        layout = block.get("layout", "4_4")
        parts = layout.split(",")
        return len(parts)

    def _build_harmony_matrix(self) -> Dict[str, Dict[str, float]]:
        """Build harmony matrix from dataset blocks."""
        block_ids = list(self.dataset.blocks.keys())
        matrix = {bid: {bid: 1.0 for bid in block_ids} for bid in block_ids}

        for bid_a in block_ids:
            for bid_b in block_ids:
                if bid_a == bid_b:
                    continue
                ba = self.dataset.blocks[bid_a]
                bb = self.dataset.blocks[bid_b]
                score = 0.0

                if ba.get("section_type") == bb.get("section_type"):
                    score += 0.5

                sa = set(ba.get("compatible_strategies", []))
                sb = set(bb.get("compatible_strategies", []))
                if sa and sb:
                    score += (len(sa & sb) / max(len(sa | sb), 1)) * 0.3

                bg_a = str(ba.get("props", {}).get("section", {}).get("bg_color", ""))
                bg_b = str(bb.get("props", {}).get("section", {}).get("bg_color", ""))
                a_is_dark = "dark" in bg_a.lower() or "surface" in bg_a.lower()
                b_is_dark = "dark" in bg_b.lower() or "surface" in bg_b.lower()
                if a_is_dark == b_is_dark:
                    score += 0.2

                matrix[bid_a][bid_b] = min(score, 1.0)

        return matrix

    def _contrast_multiplier(self, transition: str, block_a_id: str, block_b_id: str) -> float:
        """Convert harmony into a contrast-appropriate score."""
        harmony = self.harmony_matrix.get(block_a_id, {}).get(block_b_id, 0.5)
        if transition == "match":
            return harmony
        elif transition == "break":
            return 1.0 - harmony
        elif transition == "climax":
            return min(1.0, harmony + 0.2)
        elif transition == "subtle_shift":
            return 0.5 + (harmony - 0.5) * 0.5
        return 0.5

    def _score_content_fit(self, block: Dict, profile: Dict, bias: Dict) -> float:
        """Score how well a block fits the actual content (0-1)."""
        score = 0.5
        bcols = self._derive_columns(block)
        n_items = profile["n_items"]
        expected_cols = min(n_items, bcols) if n_items > 0 else bcols

        if bcols == expected_cols:
            score += 0.25
        elif abs(bcols - expected_cols) <= 1:
            score += 0.12

        bid = block.get("id", "")

        if profile["has_icons"] and "blurb" in str(block.get("module_type", "")):
            score += 0.1
        if profile["has_long_text"] and "light" in bid:
            score += 0.08
        if profile["has_images"] and profile["has_images"]:
            if "gallery" in bid or "image" in str(block.get("module_type", "")):
                score += 0.1
        if profile["has_cta"] and "cta" in block.get("section_type", ""):
            score += 0.12

        return min(score, 1.0)

    def select_blocks(self, sections: List[Dict], page_profile: str,
                      contrast_plan: List[Dict], seed: Optional[int] = None) -> List[Optional[Dict]]:
        """Select optimal blocks for ALL sections using full-page context."""
        rng = random.Random(seed) if seed is not None else random
        narrative_bias = self._NARRATIVE_BIAS.get(page_profile, self._NARRATIVE_BIAS["landing"])
        strategy_preferred = self.strategy_adapt.get("preferred_blocks", [])
        strategy_avoid = self.strategy_adapt.get("avoid_blocks", [])
        narrative_preferred = narrative_bias["preferred"]
        narrative_avoid = narrative_bias["avoid"]
        selected = []

        for i, (sec_def, ct) in enumerate(zip(sections, contrast_plan)):
            st = sec_def.get("section_type", "generic")
            matches = self.dataset.find_compatible_blocks(st, self.strategy)

            if not matches:
                selected.append(None)
                continue

            content_profile = PageProfileAnalyzer.profile_section(sec_def)
            prev_block_id = selected[i - 1].get("id", "") if i > 0 and selected[-1] else ""
            scored = []

            for block in matches:
                bid = block.get("id", "")

                d1 = 1.0 if bid in strategy_preferred else (
                    0.8 if any(p in bid for p in strategy_preferred) else 0.5
                )
                if bid in strategy_avoid:
                    d1 = 0.0

                d2 = self._score_content_fit(block, content_profile, narrative_bias)

                if prev_block_id:
                    d3 = self._contrast_multiplier(ct["transition"], prev_block_id, bid)
                else:
                    d3 = 0.7

                d4 = 0.5
                if any(p in bid for p in narrative_preferred):
                    d4 = 1.0
                if any(a in bid for a in narrative_avoid):
                    d4 = max(0, d4 - 0.6)

                impact = block.get("impact_score", 50) / 100.0

                total = d1 * 0.20 + d2 * 0.25 + d3 * 0.25 + d4 * 0.15 + impact * 0.15
                scored.append((total, block))

            scored.sort(key=lambda x: x[0], reverse=True)

            if len(scored) >= 2 and (scored[0][0] - scored[1][0]) < 0.15:
                tier = [b for s, b in scored if (scored[0][0] - s) < 0.15]
                chosen = rng.choice(tier)
            else:
                chosen = scored[0][1]

            selected.append(chosen)

        return selected


# ===============================================================
# 5. IMPACT DIRECTOR — frontend-design principles as Divi params
# ===============================================================

class ImpactDirector:
    """Translates frontend-design principles into Divi-native decisions.
    Deterministic: same inputs → same outputs."""

    # Frontend-design principles translated to Divi parameters
    _FRONTEND_PRINCIPLES = {
        "typography": {
            "penalize_generic_fonts": True,
            "generic_fonts": ["Inter", "Arial", "Roboto", "Helvetica", "sans-serif"],
            "prefer_letter_spacing_negative": True,
            "headline_line_height": "1.1em",
            "body_line_height": "1.6em",
            "eyebrow_letter_spacing": "2px",
            "eyebrow_transform": "uppercase"
        },
        "motion": {
            "stagger_step_ms": 100,
            "hero_duration_ms": 800,
            "content_duration_ms": 600,
            "micro_duration_ms": 300,
            "preferred_easing": "cubic-bezier(0.16,1,0.3,1)",
            "fallback_easing": "ease-out"
        },
        "spacing": {
            "section_padding_min": "80px",
            "section_padding_hero": "140px",
            "section_padding_cta": "120px",
            "container_padding_x": "96px",
            "mobile_padding_x": "24px"
        },
        "color": {
            "prefers_high_contrast": True,
            "minimum_contrast_ratio": 4.5
        },
        "aesthetic": {
            "prefers_distinctive": True,
            "glass_alpha_min": 0.80,
            "glow_intensity_map": {"none": 0, "low": 0.1, "medium": 0.15, "high": 0.25}
        }
    }

    def __init__(self, resolver: BrandResolver, catalog: CatalogLoader, dataset: DatasetLoader,
                 block_engine: Optional['BlockSelectionEngine'] = None, seed: Optional[int] = None):
        self.resolver = resolver
        self.catalog = catalog
        self.dataset = dataset
        self.strategy = resolver.get_strategy()
        self.strategy_adapt = dataset.get_strategy_adaptation(self.strategy)
        self.block_engine = block_engine
        self.seed = seed
        self._block_cache: List[Optional[Dict]] = []

    def select_block(self, section_type: str, index: int = 0) -> Optional[Dict]:
        """Select block for section_type + strategy, using cache if available."""
        if self._block_cache and index < len(self._block_cache):
            return self._block_cache[index]

        # Fallback: dataset search
        return self.dataset.get_best_block(section_type, self.strategy)

    def adapt_block_props(self, block: Dict) -> Dict:
        """Adapt block props to brand strategy."""
        props = copy.deepcopy(block.get("props", {}))
        adjustments = self.strategy_adapt.get("color_adjustments", {})

        # Apply strategy-specific color adjustments
        if adjustments.get("glass_bg_alpha"):
            alpha = adjustments["glass_bg_alpha"]
            if "card_blurb" in props and "bg_color" in props["card_blurb"]:
                # Keep token reference, the design system already has alpha in glass-bg
                pass

        # Apply glow intensity adjustments
        glow_intensity = adjustments.get("glow_intensity", "medium")
        if glow_intensity == "none":
            # Remove glow effects
            for key in list(props.keys()):
                if "glow" in key.lower() or "shadow_hover" in key.lower():
                    if key != "section":  # Keep section shadows
                        props.pop(key, None)

        # Apply typography rules
        typography = self._FRONTEND_PRINCIPLES["typography"]
        for key, prop in props.items():
            if isinstance(prop, dict):
                if "text_font_size" in prop and "clamp(" not in str(prop.get("text_font_size", "")):
                    # Only override if not already using clamp()
                    pass

        return props

    def apply_combination_rules(self, props: Dict) -> Dict:
        """Ensure prop combinations follow the rules (glass, glow, etc)."""
        result = copy.deepcopy(props)

        # Glass morphism rule
        if "backdrop_filter" in str(json.dumps(result)):
            rule = self.dataset.get_combination_rule("glass_morphism")
            if rule:
                required = rule.get("required", [])
                # Ensure all required props are present when backdrop_filter is used
                for target_key in result:
                    target = result[target_key]
                    if isinstance(target, dict) and "backdrop_filter" in target:
                        if "bg_color" not in target:
                            target["bg_color"] = "{{design:color:glass-bg}}"
                        if "border_width" not in target:
                            target["border_width"] = {"top": "1px", "right": "1px", "bottom": "1px", "left": "1px"}
                        if "border_color" not in target:
                            target["border_color"] = "{{design:color:glass-border}}"

        return result

    def get_presets_for_module(self, module_type: str, block: Optional[Dict] = None) -> List[str]:
        """Get presets for a module based on strategy and block."""
        presets = []
        if block and "presets" in block:
            presets = list(block["presets"])

        # Strategy-specific preset adjustments
        if "minimal" in self.strategy:
            # Remove glow presets in minimal
            presets = [p for p in presets if "glow" not in p]

        return presets

    def evaluate_impact(self, section: Dict) -> int:
        """Score the visual impact of a section."""
        score = 0
        decoration = section.get("decoration", {})

        # Check for high-impact props
        if "background" in decoration:
            bg = decoration["background"]
            if isinstance(bg, dict):
                val = bg.get("desktop", {}).get("value", {})
                if "overlay" in val and "gradient" in str(val.get("overlay", {})):
                    score += self.dataset.impact_weights.get("overlay_gradient", 12)

        if "boxShadow" in decoration:
            score += self.dataset.impact_weights.get("box_shadow", 5)

        if "transform" in decoration:
            score += self.dataset.impact_weights.get("transform_hover", 10)

        if "scroll" in decoration:
            score += self.dataset.impact_weights.get("scroll_vertical_motion", 8)

        return score


# ===============================================================
# 5. DECORATION BUILDER — constructs Divi decoration objects
# ===============================================================

class DecorationBuilder:
    """Builds Divi-native decoration objects from prop definitions."""

    def __init__(self, catalog: CatalogLoader, resolver: BrandResolver):
        self.catalog = catalog
        self.resolver = resolver

    def _resolve_value(self, value: Any) -> Any:
        return self.resolver.resolve_deep(value)

    def build_background(self, color: str, overlay_gradient: Optional[str] = None) -> Dict:
        """Build a background decoration."""
        val = {"color": self._resolve_value(color)}
        if overlay_gradient:
            val["overlay"] = {"gradient": self._resolve_value(overlay_gradient)}
        return {"desktop": {"value": val}}

    def build_spacing(self, top: str, bottom: str, right: str = "96px", left: str = "96px") -> Dict:
        return {"desktop": {"value": {
            "padding": {
                "top": self._resolve_value(top),
                "bottom": self._resolve_value(bottom),
                "right": self._resolve_value(right),
                "left": self._resolve_value(left)
            }
        }}}

    def build_animation(self, style: str = "fade", duration: str = "600ms",
                       delay: str = "0ms", speed_curve: str = "ease-out") -> Dict:
        return {"desktop": {"value": {
            "style": style,
            "duration": self._resolve_value(duration),
            "delay": self._resolve_value(delay),
            "speedCurve": speed_curve
        }}}

    def build_scroll(self, effect_type: str, **kwargs) -> Dict:
        if effect_type == "verticalMotion":
            return {"desktop": {"value": {
                "verticalMotion": {
                    "enable": "on",
                    "offset": kwargs.get("offset", {"start": "6", "mid": "0", "end": "-4"})
                },
                "motionTriggerStart": kwargs.get("trigger", "middle")
            }}}
        if effect_type == "fade":
            return {"desktop": {"value": {
                "fade": {
                    "enable": "on",
                    "offset": kwargs.get("offset", {"start": "0", "mid": "100", "end": "100"})
                },
                "motionTriggerStart": kwargs.get("trigger", "middle")
            }}}
        if effect_type == "scaling":
            return {"desktop": {"value": {
                "scaling": {
                    "enable": "on",
                    "offset": kwargs.get("offset", {"start": "80", "mid": "100", "end": "100"})
                },
                "motionTriggerStart": kwargs.get("trigger", "middle")
            }}}
        return {}

    def build_shape_divider(self, position: str, style: str, color: str,
                           height: str = "100px", flip: str = "off", invert: str = "off") -> Dict:
        return {position: {"desktop": {"value": {
            "style": style,
            "color": self._resolve_value(color),
            "height": height,
            "flip": flip,
            "invert": invert
        }}}}

    def build_box_shadow(self, horizontal: str, vertical: str, blur: str,
                        spread: str, color: str, position: str = "outer") -> Dict:
        return {"desktop": {"value": {
            "horizontal": horizontal,
            "vertical": vertical,
            "blur": blur,
            "spread": spread,
            "color": self._resolve_value(color),
            "position": position
        }}}

    def build_transform_hover(self, scale_x: str = "1.02", scale_y: str = "1.02",
                               translate_y: str = "-2px") -> Dict:
        return {"hover": {"value": {
            "scale": {"x": scale_x, "y": scale_y},
            "translate": {"y": translate_y}
        }}}

    def build_border_radius(self, radius: str) -> Dict:
        return {"desktop": {"value": {
            "radius": {
                "topLeft": self._resolve_value(radius),
                "topRight": self._resolve_value(radius),
                "bottomRight": self._resolve_value(radius),
                "bottomLeft": self._resolve_value(radius)
            }
        }}}


# ===============================================================
# 6. ROW BUILDERS — layout construction
# ===============================================================

class RowBuilder:
    """Builds row structures for different layouts."""

    @staticmethod
    def grid_row(modules: List[Dict], max_cols: int = 3) -> Dict:
        n = len(modules)
        ncols = min(n, max_cols)
        col_type = {1: "4_4", 2: "1_2", 4: "1_4"}.get(ncols, "1_3")
        cols = [{"type": col_type, "modules": [m]} for m in modules]
        while len(cols) < ncols:
            cols.append({"type": col_type, "modules": []})
        return {
            "type": "divi/row",
            "module": "divi/row",
            "column_structure": ",".join([col_type] * ncols),
            "columns": cols,
        }

    @staticmethod
    def split_row(left_modules: List[Dict], right_modules: List[Dict]) -> Dict:
        return {
            "type": "divi/row",
            "module": "divi/row",
            "column_structure": "1_2,1_2",
            "columns": [
                {"type": "1_2", "modules": left_modules},
                {"type": "1_2", "modules": right_modules},
            ],
        }

    @staticmethod
    def full_row(modules: List[Dict]) -> Dict:
        return {
            "type": "divi/row",
            "module": "divi/row",
            "column_structure": "4_4",
            "columns": [{"type": "4_4", "modules": modules}],
        }


# ===============================================================
# 7. MODULE BUILDER — builds native Divi modules
# ===============================================================

class ModuleBuilder:
    """Builds Divi 5 module instances with rich decoration."""

    def __init__(self, director: ImpactDirector, decorator: DecorationBuilder):
        self.director = director
        self.decorator = decorator
        self.resolver = director.resolver

    def _base(self, module_type: str, **fields) -> Dict:
        base = {"type": module_type, "module": module_type}
        base.update(fields)
        return base

    def make_text(self, content: str, text_type: str = "body", is_dark: bool = False,
                  custom_props: Optional[Dict] = None) -> Dict:
        """Build a text module with contextual presets."""
        presets = []

        # Determine text preset
        if text_type == "eyebrow":
            if is_dark and self.resolver.has_preset("text", "eyebrow-dark"):
                presets = ["text:eyebrow-dark"]
            elif self.resolver.has_preset("text", "eyebrow"):
                presets = ["text:eyebrow"]
        elif text_type == "headline" and self.resolver.has_preset("text", "headline"):
            presets = ["text:headline-light" if is_dark else "text:headline"]

        fields = {"content": content, "presets": presets}
        if custom_props:
            fields["decoration"] = self._build_text_decoration(custom_props)
        return self._base("divi/text", **fields)

    def make_heading(self, content: str, level: str = "h2", is_dark: bool = False,
                     custom_props: Optional[Dict] = None) -> Dict:
        presets = []
        if level == "h1" and self.resolver.has_preset("text", "hero-title"):
            presets = ["text:hero-title"]
        elif level == "h2":
            if is_dark and self.resolver.has_preset("text", "headline-light"):
                presets = ["text:headline-light"]
            elif self.resolver.has_preset("text", "headline"):
                presets = ["text:headline"]

        fields = {"content": content, "level": level, "presets": presets}
        if custom_props:
            fields["decoration"] = self._build_text_decoration(custom_props)
        return self._base("divi/heading", **fields)

    def make_button(self, text: str, url: str, is_primary: bool = True,
                    custom_props: Optional[Dict] = None) -> Dict:
        presets = []
        if self.resolver.has_preset("module", "btn-primary"):
            presets.append("module:btn-primary")
        if self.resolver.has_preset("transform", "hover-glow"):
            presets.append("transform:hover-glow")

        fields = {
            "button_text": text,
            "button_url": url,
            "presets": presets,
        }
        return self._base("divi/button", **fields)

    def make_image(self, src: str, alt: str = "",
                   custom_props: Optional[Dict] = None) -> Dict:
        presets = []
        if self.resolver.has_preset("module", "image-shadow"):
            presets.append("module:image-shadow")
        if self.resolver.has_preset("transform", "hover-scale"):
            presets.append("transform:hover-scale")

        fields = {"src": src, "alt": alt, "presets": presets}
        return self._base("divi/image", **fields)

    def make_blurb(self, item: Dict, custom_props: Optional[Dict] = None) -> Dict:
        """Build a blurb with glass card support when strategy allows."""
        presets = []
        use_glass = "glass" in self.director.strategy or "luxury" in self.director.strategy

        if use_glass and self.resolver.has_preset("module", "glass-card"):
            presets.append("module:glass-card")
        elif self.resolver.has_preset("module", "feature-card"):
            presets.append("module:feature-card")

        if self.resolver.has_preset("transform", "hover-glow"):
            presets.append("transform:hover-glow")

        fields = {
            "title": item.get("title", ""),
            "content": item.get("text", item.get("content", "")),
            "presets": presets,
        }
        if item.get("icon"):
            fields["icon"] = item.get("icon")
        return self._base("divi/blurb", **fields)

    def make_stat(self, stat: Dict) -> Dict:
        number = stat.get("number", "")
        enable_percent = "off"
        if "%" in number:
            number = number.replace("%", "").strip()
            enable_percent = "on"
        number = number.replace("+", "").strip()

        presets = []
        if self.resolver.has_preset("module", "stat-item"):
            presets.append("module:stat-item")
        if self.resolver.has_preset("transform", "hover-scale"):
            presets.append("transform:hover-scale")

        return self._base("divi/number-counter",
            number=number,
            title=stat.get("label", ""),
            presets=presets,
        )

    def make_testimonial(self, testimonial: Dict) -> Dict:
        presets = []
        if self.resolver.has_preset("module", "testimonial-card"):
            presets.append("module:testimonial-card")
        if self.resolver.has_preset("transform", "hover-glow"):
            presets.append("transform:hover-glow")

        return self._base("divi/testimonial",
            content=testimonial.get("text", ""),
            author=testimonial.get("name", ""),
            jobTitle=testimonial.get("role", ""),
            presets=presets,
        )

    def make_accordion(self, items: List[Dict]) -> Dict:
        children = []
        for item in items[:8]:
            child = self._base("divi/accordion-item",
                title=item.get("question", item.get("title", "")),
                content=item.get("answer", item.get("text", "")),
            )
            children.append(child)
        return self._base("divi/accordion", children=children)

    def make_pricing_tables(self, features: List[Dict]) -> Dict:
        tables = []
        for feat in features[:3]:
            table = self._base("divi/pricing-table",
                title=feat.get("title", ""),
                subtitle=feat.get("subtitle", ""),
                price=feat.get("price", ""),
                currencyFrequency=feat.get("currency_frequency", ""),
                content=feat.get("text", ""),
            )
            tables.append(table)
        return self._base("divi/pricing-tables", children=tables)

    def make_contact_form(self) -> Dict:
        return self._base("divi/contact-form")

    def _build_text_decoration(self, props: Dict) -> Dict:
        """Build decoration object from text props."""
        deco = {}
        for key, val in props.items():
            if key.startswith("text_"):
                if key == "text_color" and val:
                    deco.setdefault("font", {}).setdefault("desktop", {}).setdefault("value", {})["color"] = val
                if key == "text_font_size" and val:
                    deco.setdefault("font", {}).setdefault("desktop", {}).setdefault("value", {})["size"] = val
                if key == "text_alignment" and val:
                    deco.setdefault("font", {}).setdefault("desktop", {}).setdefault("value", {})["textAlign"] = val
                if key == "text_transform" and val:
                    deco.setdefault("font", {}).setdefault("desktop", {}).setdefault("value", {})["textTransform"] = val
                if key == "text_letter_spacing" and val:
                    deco.setdefault("font", {}).setdefault("desktop", {}).setdefault("value", {})["letterSpacing"] = val
                if key == "text_line_height" and val:
                    deco.setdefault("font", {}).setdefault("desktop", {}).setdefault("value", {})["lineHeight"] = val
                if key == "text_font_family" and val:
                    deco.setdefault("font", {}).setdefault("desktop", {}).setdefault("value", {})["font"] = val
        return deco


# ===============================================================
# 8. SECTION BUILDER — assembles sections from blocks + rules
# ===============================================================

class SectionBuilder:
    """Builds complete sections using the dataset blocks and catalog props."""

    def __init__(self, director: ImpactDirector, module_builder: ModuleBuilder,
                 decorator: DecorationBuilder):
        self.director = director
        self.mb = module_builder
        self.decorator = decorator
        self.resolver = director.resolver

    def build(self, sec_def: Dict, index: int) -> Dict:
        """Build a rich section from brief definition."""
        st = sec_def.get("section_type", "generic")

        # 1. Select best block (position-aware)
        block = self.director.select_block(st, index)
        if not block:
            return self._build_fallback_section(sec_def)
        block_id = block.get("id", "unknown")

        # 2. Get adapted props
        props = self.director.adapt_block_props(block)
        props = self.director.apply_combination_rules(props)

        # 3. Determine section presets from strategy + section type (dataset blocks don't carry section presets)
        section_presets = self._resolve_section_presets(st, block)

        # 4. Build decoration
        section_deco = self._build_section_decoration(props.get("section", {}), st)

        # 5. Build rows (module presets are handled by ModuleBuilder internally)
        rows = self._build_rows(sec_def, st, block, props)

        # 6. Assemble
        section = {
            "type": "regular",
            "module": "divi/section",
            "presets": section_presets,
            "decoration": section_deco,
            "rows": rows,
            "_block_id": block_id,
        }

        return section

    def _resolve_section_presets(self, section_type: str, block: Dict) -> List[str]:
        """Resolve section-level presets based on type and strategy."""
        strategy = self.resolver.get_strategy()
        presets = []

        # Map section_type to section preset
        if section_type in ("hero", "hero-split"):
            if "glass" in strategy or section_type == "hero-split":
                presets.append("section:hero-glass")
            else:
                presets.append("section:hero-dark")
        elif section_type == "hero-centered":
            presets.append("section:hero-dark")
        elif section_type == "cta":
            presets.append("section:cta-epic")
        elif section_type in ("features", "stats", "faq"):
            if "glass" in strategy or "luxury" in strategy:
                presets.append("section:dark")
            else:
                presets.append("section:light")
        elif section_type == "testimonials":
            presets.append("section:white")
        elif section_type == "pricing":
            if "luxury" in strategy:
                presets.append("section:dark")
            else:
                presets.append("section:light")
        else:
            presets.append("section:light")

        # Filter by existence in design system
        return [p for p in presets if self.resolver.has_preset(p.split(":")[0], p.split(":")[1]) if ":" in p]

    def _build_section_decoration(self, section_props: Dict, section_type: str) -> Dict:
        """Construct decoration object from block section props."""
        deco = {}

        if "bg_color" in section_props:
            overlay = section_props.get("overlay_gradient")
            deco["background"] = self.decorator.build_background(section_props["bg_color"], overlay)

        if "padding" in section_props:
            pad = section_props["padding"]
            deco["spacing"] = self.decorator.build_spacing(
                pad.get("top", "80px"),
                pad.get("bottom", "80px"),
                pad.get("right", "96px"),
                pad.get("left", "96px")
            )

        if "anim_style" in section_props:
            deco["animation"] = self.decorator.build_animation(
                style=section_props.get("anim_style", "fade"),
                duration=section_props.get("anim_duration", "600ms"),
                delay=section_props.get("anim_delay", "0ms"),
                speed_curve=section_props.get("anim_speed_curve", "ease-out")
            )

        if "scroll_vertical_motion" in section_props:
            sm = section_props["scroll_vertical_motion"]
            if sm.get("enable") == "on":
                deco["scroll"] = self.decorator.build_scroll("verticalMotion", offset=sm.get("offset"))
        elif "scroll_fade" in section_props:
            sf = section_props["scroll_fade"]
            if sf.get("enable") == "on":
                deco["scroll"] = self.decorator.build_scroll("fade", offset=sf.get("offset"))
        elif "scroll_scaling" in section_props:
            sc = section_props["scroll_scaling"]
            if sc.get("enable") == "on":
                deco["scroll"] = self.decorator.build_scroll("scaling", offset=sc.get("offset"))

        if "shape_divider_top" in section_props:
            sd = section_props["shape_divider_top"]
            deco["shapeDivider"] = self.decorator.build_shape_divider(
                "top", sd.get("style", "curve"), sd.get("color", "{{design:color:surface-light}}"),
                sd.get("height", "100px"), sd.get("flip", "off"), sd.get("invert", "off")
            )
        if "shape_divider_bottom" in section_props:
            sd = section_props["shape_divider_bottom"]
            if "shapeDivider" not in deco:
                deco["shapeDivider"] = {}
            deco["shapeDivider"].update(self.decorator.build_shape_divider(
                "bottom", sd.get("style", "curve"), sd.get("color", "{{design:color:surface-light}}"),
                sd.get("height", "100px"), sd.get("flip", "off"), sd.get("invert", "off")
            ))

        return deco

    def _build_rows(self, sec_def: Dict, section_type: str, block: Dict, props: Dict) -> List[Dict]:
        rows = []

        # ── Hero layouts ──
        if section_type in ("hero", "hero-split"):
            text_modules = []
            if sec_def.get("eyebrow"):
                text_modules.append(self.mb.make_text(sec_def["eyebrow"], "eyebrow", is_dark=True,
                    custom_props=props.get("eyebrow_text")))
            if sec_def.get("title"):
                text_modules.append(self.mb.make_heading(sec_def["title"], "h1", is_dark=True,
                    custom_props=props.get("heading")))
            if sec_def.get("text"):
                text_modules.append(self.mb.make_text(sec_def["text"], "body", is_dark=True,
                    custom_props=props.get("body_text")))
            if sec_def.get("btn_primary_text"):
                text_modules.append(self.mb.make_button(
                    sec_def["btn_primary_text"],
                    sec_def.get("btn_primary_url", "#"),
                    custom_props=props.get("primary_button")
                ))
            if text_modules:
                rows.append(RowBuilder.split_row(
                    text_modules,
                    [self.mb.make_image(sec_def.get("image", ""), alt="")]
                ))

        elif section_type == "hero-centered":
            text_modules = []
            if sec_def.get("eyebrow"):
                text_modules.append(self.mb.make_text(sec_def["eyebrow"], "eyebrow", is_dark=True))
            if sec_def.get("title"):
                text_modules.append(self.mb.make_heading(sec_def["title"], "h1", is_dark=True))
            if sec_def.get("text"):
                text_modules.append(self.mb.make_text(sec_def["text"], "body", is_dark=True))
            if sec_def.get("btn_primary_text"):
                text_modules.append(self.mb.make_button(
                    sec_def["btn_primary_text"],
                    sec_def.get("btn_primary_url", "#")
                ))
            if text_modules:
                rows.append(RowBuilder.full_row(text_modules))

        # ── Features ──
        elif section_type == "features":
            items = sec_def.get("items", [])
            if items:
                modules = [self.mb.make_blurb(item, custom_props=props.get("card_blurb")) for item in items[:6]]
                for i in range(0, len(modules), 3):
                    chunk = modules[i:i+3]
                    rows.append(RowBuilder.grid_row(chunk, max_cols=3))

        # ── Stats ──
        elif section_type == "stats":
            stats = sec_def.get("stats", [])
            if stats:
                modules = [self.mb.make_stat(s) for s in stats[:4]]
                rows.append(RowBuilder.grid_row(modules, max_cols=4))

        # ── Testimonials ──
        elif section_type == "testimonials":
            testimonials = sec_def.get("testimonials", [])
            if testimonials:
                modules = [self.mb.make_testimonial(t) for t in testimonials[:6]]
                for i in range(0, len(modules), 3):
                    chunk = modules[i:i+3]
                    rows.append(RowBuilder.grid_row(chunk, max_cols=3))

        # ── Content split ──
        elif section_type == "content":
            content_modules = []
            if sec_def.get("title"):
                content_modules.append(self.mb.make_heading(sec_def["title"], "h2"))
            content_text = sec_def.get("text", sec_def.get("body", ""))
            if content_text:
                content_modules.append(self.mb.make_text(content_text, "body"))
            if sec_def.get("btn_primary_text"):
                content_modules.append(self.mb.make_button(
                    sec_def["btn_primary_text"],
                    sec_def.get("btn_primary_url", "#")
                ))
            if content_modules:
                rows.append(RowBuilder.split_row(
                    content_modules,
                    [self.mb.make_image(sec_def.get("image", ""), alt="")]
                ))

        # ── CTA ──
        elif section_type == "cta":
            cta_modules = []
            if sec_def.get("title"):
                cta_modules.append(self.mb.make_heading(sec_def["title"], "h2", is_dark=True))
            if sec_def.get("text"):
                cta_modules.append(self.mb.make_text(sec_def["text"], "body", is_dark=True))
            if sec_def.get("btn_primary_text"):
                cta_modules.append(self.mb.make_button(
                    sec_def["btn_primary_text"],
                    sec_def.get("btn_primary_url", "#"),
                    custom_props=props.get("primary_button")
                ))
            if cta_modules:
                rows.append(RowBuilder.full_row(cta_modules))

        # ── Pricing ──
        elif section_type == "pricing":
            features = sec_def.get("features", [])
            if features:
                rows.append(RowBuilder.full_row([self.mb.make_pricing_tables(features)]))

        # ── FAQ ──
        elif section_type == "faq":
            faqs = sec_def.get("faqs", [])
            if faqs:
                left_items = faqs[:len(faqs)//2 + len(faqs)%2]
                right_items = faqs[len(faqs)//2 + len(faqs)%2:]
                rows.append(RowBuilder.split_row(
                    [self.mb.make_accordion(left_items)],
                    [self.mb.make_accordion(right_items)] if right_items else []
                ))

        # ── Gallery ──
        elif section_type == "gallery":
            items = sec_def.get("items", sec_def.get("gallery_items", []))
            if items:
                images = []
                for item in items[:6]:
                    images.append(self.mb.make_image(item.get("image", ""), item.get("alt", "")))
                rows.append(RowBuilder.full_row([{
                    "type": "divi/gallery",
                    "module": "divi/gallery",
                    "children": images
                }]))

        # ── Contact ──
        elif section_type == "contact":
            left = [self.mb.make_contact_form()]
            right = []
            if sec_def.get("title"):
                right.append(self.mb.make_heading(sec_def["title"], "h2"))
            if sec_def.get("text"):
                right.append(self.mb.make_text(sec_def["text"], "body"))
            rows.append(RowBuilder.split_row(left, right))

        # ── Timeline ──
        elif section_type == "timeline":
            items = sec_def.get("items", [])
            if items:
                rows.append(RowBuilder.full_row([
                    self._base("divi/timeline", items=items)
                ]))

        # ── Trust bar ──
        elif section_type == "trust-bar":
            items = sec_def.get("logos", sec_def.get("items", []))
            if items:
                logo_modules = [self.mb.make_image(i.get("image", ""), i.get("alt", "")) for i in items[:5]]
                rows.append(RowBuilder.grid_row(logo_modules, max_cols=5))

        return rows

    def _build_fallback_section(self, sec_def: Dict) -> Dict:
        """Build a minimal fallback section when no block matches."""
        return {
            "type": "regular",
            "module": "divi/section",
            "presets": ["section:light"],
            "decoration": {},
            "rows": [RowBuilder.full_row([
                self.mb.make_text(sec_def.get("title", "Section"), "body")
            ])]
        }


# ===============================================================
# 9. VISUAL IMPACT ENGINE — main orchestrator
# ===============================================================

class VisualImpactEngine:
    """
    Main translator: brief + design system + catalog + dataset → rich page-def.

    Architecture:
        brief.json ──► CatalogLoader (127 props)
                     ──► DatasetLoader (12 blocks + rules)
                     ──► BrandResolver (tokens)
                     ──► ImpactDirector (rules + adaptation)
                     ──► SectionBuilder (assembles sections)
                           ──► DecorationBuilder (Divi props)
                           ──► ModuleBuilder (modules)
                           ──► RowBuilder (layouts)
                     ──► page-def.json RICO
    """

    def __init__(self, design_system: Dict[str, Any],
                 catalog_path: Optional[Path] = None,
                 dataset_path: Optional[Path] = None,
                 seed: Optional[int] = None):
        self.resolver = BrandResolver(design_system)
        self.catalog = CatalogLoader(catalog_path)
        self.dataset = DatasetLoader(dataset_path)
        self.strategy = self.resolver.get_strategy()
        self.block_engine = BlockSelectionEngine(
            self.dataset, self.strategy,
            self.dataset.get_strategy_adaptation(self.strategy)
        )
        self.director = ImpactDirector(self.resolver, self.catalog, self.dataset,
                                       block_engine=self.block_engine, seed=seed)
        self.decorator = DecorationBuilder(self.catalog, self.resolver)
        self.module_builder = ModuleBuilder(self.director, self.decorator)
        self.section_builder = SectionBuilder(self.director, self.module_builder, self.decorator)

    def translate_brief(self, brief: Dict[str, Any]) -> Dict[str, Any]:
        """Convert brief sections into rich page-def with intelligent block selection."""
        sections_list = brief.get("sections", [])

        # Phase 1: Analyze full page context
        page_profile = PageProfileAnalyzer.detect_narrative_profile(brief)
        contrast_plan = PageProfileAnalyzer.build_contrast_plan(sections_list, self.strategy)

        # Phase 2: Pre-select blocks for ALL sections with full context
        self.director._block_cache = self.block_engine.select_blocks(
            sections_list, page_profile, contrast_plan, seed=self.director.seed
        )

        # Phase 3: Build sections
        sections = []
        for i, sec_def in enumerate(sections_list):
            section = self.section_builder.build(sec_def, i)
            sections.append(section)

        return {
            "title": brief.get("title", "Page"),
            "slug": brief.get("slug", "page"),
            "description": brief.get("description", ""),
            "sections": sections,
            "_meta": {
                "narrative_profile": page_profile,
                "strategy": self.strategy,
            }
        }

    def evaluate_page_impact(self, page_def: Dict) -> Dict:
        """Score the visual impact of the entire page."""
        scores = {}
        total = 0
        for i, section in enumerate(page_def.get("sections", [])):
            score = self.director.evaluate_impact(section)
            st = section.get("presets", ["unknown"])[0] if section.get("presets") else f"section_{i}"
            scores[st] = score
            total += score
        return {
            "total": total,
            "per_section": scores,
            "average": total / len(scores) if scores else 0,
            "max_possible": len(scores) * 50 if scores else 0,
            "impact_percentage": (total / (len(scores) * 50) * 100) if scores else 0
        }


# ===============================================================
# CLI
# ===============================================================

def main():
    parser = argparse.ArgumentParser(description="Visual Impact Engine v3.0 — Deterministic page-def generator")
    parser.add_argument("--brief-file", required=True, help="Path to brief JSON")
    parser.add_argument("--design-system", required=True, help="Path to design system JSON")
    parser.add_argument("--catalog", default=None, help="Path to divi_catalog.json (optional)")
    parser.add_argument("--dataset", default=None, help="Path to diviplus_dataset.json (optional)")
    parser.add_argument("--output", required=True, help="Output path for page-def JSON")
    parser.add_argument("--evaluate", action="store_true", help="Print impact score")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducible variation")
    args = parser.parse_args()

    # Load inputs
    with open(args.brief_file, 'r', encoding='utf-8') as f:
        brief = json.load(f)
    with open(args.design_system, 'r', encoding='utf-8') as f:
        design_system = json.load(f)

    # Run engine
    catalog_path = Path(args.catalog) if args.catalog else None
    dataset_path = Path(args.dataset) if args.dataset else None
    engine = VisualImpactEngine(design_system, catalog_path, dataset_path, seed=args.seed)
    page_def = engine.translate_brief(brief)

    # Evaluate
    if args.evaluate:
        scores = engine.evaluate_page_impact(page_def)
        print(f"[VIE v3.0] Impact Score: {scores['total']}/{scores['max_possible']} ({scores['impact_percentage']:.1f}%)")
        for section, score in scores["per_section"].items():
            print(f"  - {section}: {score} pts")

    # Write output
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(page_def, f, indent=2, ensure_ascii=False)
    print(f"[VIE v3.0] Generated: {args.output}")


if __name__ == "__main__":
    main()
