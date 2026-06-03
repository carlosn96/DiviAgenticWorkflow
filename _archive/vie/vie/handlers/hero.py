"""Handler for `hero` and `hero-split` section types."""
from typing import Any, Dict, List

from vie.building import RowBuilder
from vie.handlers._registry import register


@register("hero")
@register("hero-split")
class HeroSectionHandler:
    section_type = "hero"  # also matches hero-split via second decorator

    def build(self, sec_def: Dict, index: int, director: Any,
              module_builder: Any, decorator: Any,
              block: Dict, props: Dict) -> List[Dict]:
        text_modules = []
        if sec_def.get("eyebrow"):
            text_modules.append(module_builder.make_text(sec_def["eyebrow"], "eyebrow", is_dark=True,
                custom_props=props.get("eyebrow_text")))
        if sec_def.get("title"):
            text_modules.append(module_builder.make_heading(sec_def["title"], "h1", is_dark=True,
                custom_props=props.get("heading")))
        if sec_def.get("text"):
            text_modules.append(module_builder.make_text(sec_def["text"], "body", is_dark=True,
                custom_props=props.get("body_text")))
        if sec_def.get("btn_primary_text"):
            text_modules.append(module_builder.make_button(
                sec_def["btn_primary_text"],
                sec_def.get("btn_primary_url", "#"),
                custom_props=props.get("primary_button")
            ))
        if text_modules:
            return [RowBuilder.split_row(
                text_modules,
                [module_builder.make_image(sec_def.get("image", ""), alt="")]
            )]
        return []


@register("hero-centered")
class HeroCenteredSectionHandler:
    section_type = "hero-centered"

    def build(self, sec_def: Dict, index: int, director: Any,
              module_builder: Any, decorator: Any,
              block: Dict, props: Dict) -> List[Dict]:
        text_modules = []
        if sec_def.get("eyebrow"):
            text_modules.append(module_builder.make_text(sec_def["eyebrow"], "eyebrow", is_dark=True))
        if sec_def.get("title"):
            text_modules.append(module_builder.make_heading(sec_def["title"], "h1", is_dark=True))
        if sec_def.get("text"):
            text_modules.append(module_builder.make_text(sec_def["text"], "body", is_dark=True))
        if sec_def.get("btn_primary_text"):
            text_modules.append(module_builder.make_button(
                sec_def["btn_primary_text"],
                sec_def.get("btn_primary_url", "#")
            ))
        if text_modules:
            return [RowBuilder.full_row(text_modules)]
        return []
