"""Handler for `testimonials` section type."""
from typing import Any, Dict, List

from vie.building import RowBuilder
from vie.handlers._registry import register


@register("testimonials")
class TestimonialsSectionHandler:
    section_type = "testimonials"

    def build(self, sec_def: Dict, index: int, director: Any,
              module_builder: Any, decorator: Any,
              block: Dict, props: Dict) -> List[Dict]:
        testimonials = sec_def.get("testimonials", [])
        if testimonials:
            modules = [module_builder.make_testimonial(t) for t in testimonials[:6]]
            rows = []
            for i in range(0, len(modules), 3):
                chunk = modules[i:i+3]
                rows.append(RowBuilder.grid_row(chunk, max_cols=3))
            return rows
        return []
