"""Handler for `trust-bar` section type."""
from typing import Any, Dict, List

from vie.building import RowBuilder
from vie.handlers._registry import register


@register("trust-bar")
class TrustBarSectionHandler:
    section_type = "trust-bar"

    def build(self, sec_def: Dict, index: int, director: Any,
              module_builder: Any, decorator: Any,
              block: Dict, props: Dict) -> List[Dict]:
        items = sec_def.get("logos", sec_def.get("items", []))
        if items:
            logo_modules = [module_builder.make_image(i.get("image", ""), i.get("alt", "")) for i in items[:5]]
            return [RowBuilder.grid_row(logo_modules, max_cols=5)]
        return []
