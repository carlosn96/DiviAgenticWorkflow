"""Handler for `pricing` section type."""
from typing import Any, Dict, List

from vie.building import RowBuilder
from vie.handlers._registry import register


@register("pricing")
class PricingSectionHandler:
    section_type = "pricing"

    def build(self, sec_def: Dict, index: int, director: Any,
              module_builder: Any, decorator: Any,
              block: Dict, props: Dict) -> List[Dict]:
        features = sec_def.get("features", [])
        if features:
            return [RowBuilder.full_row([module_builder.make_pricing_tables(features)])]
        return []
