"""Handler for `features` section type."""
from typing import Any, Dict, List

from vie.building import RowBuilder
from vie.handlers._registry import register


@register("features")
class FeaturesSectionHandler:
    section_type = "features"

    def build(self, sec_def: Dict, index: int, director: Any,
              module_builder: Any, decorator: Any,
              block: Dict, props: Dict) -> List[Dict]:
        items = sec_def.get("items", [])
        if items:
            modules = [module_builder.make_blurb(item, custom_props=props.get("card_blurb")) for item in items[:6]]
            rows = []
            for i in range(0, len(modules), 3):
                chunk = modules[i:i+3]
                rows.append(RowBuilder.grid_row(chunk, max_cols=3))
            return rows
        return []
