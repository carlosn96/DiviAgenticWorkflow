"""PageProfileAnalyzer — derives narrative profile, content density, and
contrast plan from a brief.
"""
from typing import Dict, List


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
                try:
                    from daw.types import Strategy
                    dark = Strategy(strat).contains_glass()
                except (ValueError, KeyError):
                    dark = "glass" in strat or "luxury" in strat
                return "dark" if dark else "light"
            if st == "faq":
                try:
                    from daw.types import Strategy
                    dark = Strategy(strat).contains_glass()
                except (ValueError, KeyError):
                    dark = "glass" in strat or "luxury" in strat
                return "dark" if dark else "light"
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
