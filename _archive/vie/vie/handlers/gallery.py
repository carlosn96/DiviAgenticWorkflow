"""Handler for `gallery` section type."""
from typing import Any, Dict, List

from vie.building import RowBuilder
from vie.handlers._registry import register


@register("gallery")
class GallerySectionHandler:
    section_type = "gallery"

    def build(self, sec_def: Dict, index: int, director: Any,
              module_builder: Any, decorator: Any,
              block: Dict, props: Dict) -> List[Dict]:
        items = sec_def.get("items", sec_def.get("gallery_items", []))
        if items:
            images = []
            for item in items[:6]:
                images.append(module_builder.make_image(item.get("image", ""), item.get("alt", "")))
            return [RowBuilder.full_row([{
                "type": "divi/gallery",
                "module": "divi/gallery",
                "children": images
            }])]
        return []
