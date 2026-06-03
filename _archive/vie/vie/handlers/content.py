"""Handler for `content` section type."""
from typing import Any, Dict, List

from vie.building import RowBuilder
from vie.handlers._registry import register


@register("content")
class ContentSectionHandler:
    section_type = "content"

    def build(self, sec_def: Dict, index: int, director: Any,
              module_builder: Any, decorator: Any,
              block: Dict, props: Dict) -> List[Dict]:
        content_modules = []
        if sec_def.get("title"):
            content_modules.append(module_builder.make_heading(sec_def["title"], "h2"))
        content_text = sec_def.get("text", sec_def.get("body", ""))
        if content_text:
            content_modules.append(module_builder.make_text(content_text, "body"))
        if sec_def.get("btn_primary_text"):
            content_modules.append(module_builder.make_button(
                sec_def["btn_primary_text"],
                sec_def.get("btn_primary_url", "#")
            ))
        if content_modules:
            return [RowBuilder.split_row(
                content_modules,
                [module_builder.make_image(sec_def.get("image", ""), alt="")]
            )]
        return []
