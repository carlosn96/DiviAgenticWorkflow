"""ImpactDirector — adapts dataset blocks and catalog props into concrete design decisions.

This is the original director class that orchestrates block selection, property
adaptation, and combination rules. It is preserved unchanged from the pre-refactor
implementation to maintain the exact behavior verified by verify_regression.py.

The new DesignDirector (for design_direction-aware profiles) lives in
vie/design_director.py and is used by SectionBuilder when `design_direction`
is present in the brief.
"""
from typing import Any, Dict, List, Optional

from vie.adapters import CatalogLoader, DatasetLoader
from vie.resolver import BrandResolver


class ImpactDirector:
    """Adapts dataset blocks and catalog props into concrete design decisions."""

    def __init__(self, resolver: BrandResolver, catalog: CatalogLoader,
                 dataset: DatasetLoader, block_engine=None, seed: Optional[int] = None):
        self.resolver = resolver
        self.catalog = catalog
        self.dataset = dataset
        self.block_engine = block_engine
        self.seed = seed
        self._block_cache: List[Optional[Dict]] = []

    @property
    def strategy(self) -> str:
        """Return the current strategy from resolver."""
        return self.resolver.get_strategy()

    # ── Block selection ──────────────────────────────────────────────────────

    def select_block(self, section_type: str, index: int) -> Optional[Dict]:
        """Return a cached block for the given section type and index."""
        if not self._block_cache:
            return None
        if index < len(self._block_cache):
            return self._block_cache[index]
        return None

    def evaluate_impact(self, section: Dict) -> int:
        """Score the visual impact of a single section."""
        score = 0
        presets = section.get("presets", [])
        for p in presets:
            if "glass" in p or "glow" in p:
                score += 20
            if "hero" in p or "cta" in p:
                score += 15
            if "dark" in p:
                score += 10
        deco = section.get("decoration", {})
        if deco.get("animation"):
            score += 10
        if deco.get("scroll"):
            score += 10
        if deco.get("shapeDivider"):
            score += 10
        rows = section.get("rows", [])
        for row in rows:
            for col in row.get("columns", []):
                for mod in col.get("modules", []):
                    if mod.get("presets"):
                        score += 5
        return min(score, 50)

    # ── Property adaptation ────────────────────────────────────────────────

    def adapt_block_props(self, block: Dict) -> Dict:
        """Extract and adapt properties from a selected block."""
        return block.get("props", {})

    def apply_combination_rules(self, props: Dict) -> Dict:
        """Apply cross-property combination rules (e.g. glass + dark spacing)."""
        # Currently a passthrough — preserved for future rules.
        return props

    # ── Style classification (legacy, kept for backwards compat) ───────────

    def _classify_page_style(self, tone: str, product_type: str) -> Dict[str, Any]:
        """Classify page style from tone + product_type."""
        # Minimal implementation — returns empty dict.
        # The full UXProBridge logic was never wired here; kept as stub.
        return {}

    def _apply_design_inspiration(self, props: Dict, classification: Dict) -> Dict:
        """Apply design inspiration from classification to props."""
        # Passthrough — preserved for future integration.
        return props
