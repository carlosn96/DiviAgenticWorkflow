"""BlockSelectionEngine — intelligent context-aware block selection.

4D weighted scoring:
  1. Strategy Alignment (20%)
  2. Content Density Fit (25%)
  3. Visual Harmony (25%)
  4. Narrative Bias (15%)
  + Impact bonus (15%)
"""
import random
from typing import Dict, List, Optional

from vie.adapters import DatasetLoader
from vie.analysis import PageProfileAnalyzer


class BlockSelectionEngine:
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
        layout = block.get("layout", "4_4")
        parts = layout.split(",")
        return len(parts)

    def _build_harmony_matrix(self) -> Dict[str, Dict[str, float]]:
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
