"""Handler for `stats` section type."""
from typing import Any, Dict, List

from vie.building import RowBuilder
from vie.handlers._registry import register


@register("stats")
class StatsSectionHandler:
    section_type = "stats"

    def build(self, sec_def: Dict, index: int, director: Any,
              module_builder: Any, decorator: Any,
              block: Dict, props: Dict) -> List[Dict]:
        stats = sec_def.get("stats", [])
        if stats:
            modules = [module_builder.make_stat(s) for s in stats[:4]]
            return [RowBuilder.grid_row(modules, max_cols=4)]
        return []
