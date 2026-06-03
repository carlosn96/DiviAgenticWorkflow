"""Catalog and Dataset loaders — single source of truth for Divi prop catalog
and the Divi+ block dataset.
"""
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

# adapters.py lives in DAW_bundle/vie/ — so DAW_bundle is its parent.
DAW_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_CATALOG = DAW_ROOT / "workspace" / "data" / "divi_catalog.json"
_DEFAULT_DATASET = DAW_ROOT / "workspace" / "data" / "diviplus_dataset.json"


class CatalogLoader:
    """Loads and provides structured access to the Divi prop catalog."""

    def __init__(self, catalog_path: Optional[Path] = None):
        self.catalog_path = catalog_path or _DEFAULT_CATALOG
        self.catalog: Dict = {}
        self.prop_index: Dict[str, Dict] = {}
        self._load()

    def _load(self):
        with open(self.catalog_path, 'r', encoding='utf-8') as f:
            self.catalog = json.load(f)
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
            return True
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


class DatasetLoader:
    """Loads the Divi+ dataset and provides block resolution."""

    def __init__(self, dataset_path: Optional[Path] = None):
        self.dataset_path = dataset_path or _DEFAULT_DATASET
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

            if compatible and strategy not in compatible:
                continue
            if "bg_is_light" in contras and strategy in ("minimal", "clean"):
                continue

            matches.append(block)

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
