"""Handler for `contact` section type."""
from typing import Any, Dict, List

from vie.building import RowBuilder
from vie.handlers._registry import register


@register("contact")
class ContactSectionHandler:
    section_type = "contact"

    def build(self, sec_def: Dict, index: int, director: Any,
              module_builder: Any, decorator: Any,
              block: Dict, props: Dict) -> List[Dict]:
        left = [module_builder.make_contact_form()]
        right = []
        if sec_def.get("title"):
            right.append(module_builder.make_heading(sec_def["title"], "h2"))
        if sec_def.get("text"):
            right.append(module_builder.make_text(sec_def["text"], "body"))
        return [RowBuilder.split_row(left, right)]
