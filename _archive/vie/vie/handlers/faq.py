"""Handler for `faq` section type."""
from typing import Any, Dict, List

from vie.building import RowBuilder
from vie.handlers._registry import register


@register("faq")
class FaqSectionHandler:
    section_type = "faq"

    def build(self, sec_def: Dict, index: int, director: Any,
              module_builder: Any, decorator: Any,
              block: Dict, props: Dict) -> List[Dict]:
        faqs = sec_def.get("faqs", [])
        if faqs:
            left_items = faqs[:len(faqs)//2 + len(faqs)%2]
            right_items = faqs[len(faqs)//2 + len(faqs)%2:]
            return [RowBuilder.split_row(
                [module_builder.make_accordion(left_items)],
                [module_builder.make_accordion(right_items)] if right_items else []
            )]
        return []
