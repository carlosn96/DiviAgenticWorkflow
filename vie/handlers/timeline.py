"""Handler for `timeline` section type."""
from typing import Any, Dict, List

from vie.building import RowBuilder
from vie.handlers._registry import register


@register("timeline")
class TimelineSectionHandler:
    section_type = "timeline"

    def build(self, sec_def: Dict, index: int, director: Any,
              module_builder: Any, decorator: Any,
              block: Dict, props: Dict) -> List[Dict]:
        items = sec_def.get("items", [])
        if items:
            return [RowBuilder.full_row([
                module_builder._base("divi/timeline", items=items)
            ])]
        return []
