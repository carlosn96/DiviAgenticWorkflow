"""Handler for `cta` section type."""
from typing import Any, Dict, List

from vie.building import RowBuilder
from vie.handlers._registry import register


@register("cta")
class CtaSectionHandler:
    section_type = "cta"

    def build(self, sec_def: Dict, index: int, director: Any,
              module_builder: Any, decorator: Any,
              block: Dict, props: Dict) -> List[Dict]:
        cta_modules = []
        if sec_def.get("title"):
            cta_modules.append(module_builder.make_heading(sec_def["title"], "h2", is_dark=True))
        if sec_def.get("text"):
            cta_modules.append(module_builder.make_text(sec_def["text"], "body", is_dark=True))
        if sec_def.get("btn_primary_text"):
            cta_modules.append(module_builder.make_button(
                sec_def["btn_primary_text"],
                sec_def.get("btn_primary_url", "#"),
                custom_props=props.get("primary_button")
            ))
        if cta_modules:
            return [RowBuilder.full_row(cta_modules)]
        return []
