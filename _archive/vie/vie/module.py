"""ModuleBuilder — builds Divi 5 module instances with rich decoration.
"""
from typing import Dict, List, Optional

from vie.building import DecorationBuilder
from vie.director import ImpactDirector


class ModuleBuilder:
    """Builds Divi 5 module instances with rich decoration."""

    def __init__(self, director: ImpactDirector, decorator: DecorationBuilder):
        self.director = director
        self.decorator = decorator
        self.resolver = director.resolver

    def _base(self, module_type: str, **fields) -> Dict:
        base = {"type": module_type, "module": module_type}
        base.update(fields)
        return base

    def make_text(self, content: str, text_type: str = "body", is_dark: bool = False,
                  custom_props: Optional[Dict] = None) -> Dict:
        """Build a text module with contextual presets."""
        presets = []

        if text_type == "eyebrow":
            if is_dark and self.resolver.has_preset("text", "eyebrow-dark"):
                presets = ["text:eyebrow-dark"]
            elif self.resolver.has_preset("text", "eyebrow"):
                presets = ["text:eyebrow"]
        elif text_type == "headline" and self.resolver.has_preset("text", "headline"):
            presets = ["text:headline-light" if is_dark else "text:headline"]

        fields = {"content": content, "presets": presets}
        if custom_props:
            fields["decoration"] = self._build_text_decoration(custom_props)
        return self._base("divi/text", **fields)

    def make_heading(self, content: str, level: str = "h2", is_dark: bool = False,
                     custom_props: Optional[Dict] = None) -> Dict:
        presets = []
        if level == "h1" and self.resolver.has_preset("text", "hero-title"):
            presets = ["text:hero-title"]
        elif level == "h2":
            if is_dark and self.resolver.has_preset("text", "headline-light"):
                presets = ["text:headline-light"]
            elif self.resolver.has_preset("text", "headline"):
                presets = ["text:headline"]

        fields = {"content": content, "level": level, "presets": presets}
        if custom_props:
            fields["decoration"] = self._build_text_decoration(custom_props)
        return self._base("divi/heading", **fields)

    def make_button(self, text: str, url: str, is_primary: bool = True,
                    custom_props: Optional[Dict] = None) -> Dict:
        presets = []
        if self.resolver.has_preset("module", "btn-primary"):
            presets.append("module:btn-primary")
        if self.resolver.has_preset("transform", "hover-glow"):
            presets.append("transform:hover-glow")

        fields = {
            "button_text": text,
            "button_url": url,
            "presets": presets,
        }
        return self._base("divi/button", **fields)

    def make_image(self, src: str, alt: str = "",
                   custom_props: Optional[Dict] = None) -> Dict:
        presets = []
        if self.resolver.has_preset("module", "image-shadow"):
            presets.append("module:image-shadow")
        if self.resolver.has_preset("transform", "hover-scale"):
            presets.append("transform:hover-scale")

        fields = {"src": src, "alt": alt, "presets": presets}
        return self._base("divi/image", **fields)

    def make_blurb(self, item: Dict, custom_props: Optional[Dict] = None) -> Dict:
        """Build a blurb with glass card support when strategy allows."""
        presets = []
        from daw.types import Strategy
        try:
            strat = Strategy(self.director.strategy)
            use_glass = strat.contains_glass()
        except ValueError:
            use_glass = "glass" in self.director.strategy or "luxury" in self.director.strategy

        if use_glass and self.resolver.has_preset("module", "glass-card"):
            presets.append("module:glass-card")
        elif self.resolver.has_preset("module", "feature-card"):
            presets.append("module:feature-card")

        if self.resolver.has_preset("transform", "hover-glow"):
            presets.append("transform:hover-glow")

        fields = {
            "title": item.get("title", ""),
            "content": item.get("text", item.get("content", "")),
            "presets": presets,
        }
        if item.get("icon"):
            fields["icon"] = item.get("icon")
        return self._base("divi/blurb", **fields)

    def make_stat(self, stat: Dict) -> Dict:
        number = stat.get("number", "")
        enable_percent = "off"
        if "%" in number:
            number = number.replace("%", "").strip()
            enable_percent = "on"
        number = number.replace("+", "").strip()

        presets = []
        if self.resolver.has_preset("module", "stat-item"):
            presets.append("module:stat-item")
        if self.resolver.has_preset("transform", "hover-scale"):
            presets.append("transform:hover-scale")

        return self._base("divi/number-counter",
            number=number,
            title=stat.get("label", ""),
            presets=presets,
        )

    def make_testimonial(self, testimonial: Dict) -> Dict:
        presets = []
        if self.resolver.has_preset("module", "testimonial-card"):
            presets.append("module:testimonial-card")
        if self.resolver.has_preset("transform", "hover-glow"):
            presets.append("transform:hover-glow")

        return self._base("divi/testimonial",
            content=testimonial.get("text", ""),
            author=testimonial.get("name", ""),
            jobTitle=testimonial.get("role", ""),
            presets=presets,
        )

    def make_accordion(self, items: List[Dict]) -> Dict:
        children = []
        for item in items[:8]:
            child = self._base("divi/accordion-item",
                title=item.get("question", item.get("title", "")),
                content=item.get("answer", item.get("text", "")),
            )
            children.append(child)
        return self._base("divi/accordion", children=children)

    def make_pricing_tables(self, features: List[Dict]) -> Dict:
        tables = []
        for i, feat in enumerate(features[:3]):
            is_featured = i == 1
            table = self._base("divi/pricing-table",
                title=feat.get("title", ""),
                subtitle=feat.get("subtitle", ""),
                price=feat.get("price", ""),
                currencyFrequency={
                    "currency": "",
                    "per": feat.get("currency_frequency", "/mes"),
                },
                content=feat.get("text", ""),
                featured="on" if is_featured else "off",
            )
            if feat.get("button_text") or is_featured:
                table["button_text"] = feat.get("button_text", "Elegir Plan" if is_featured else "")
                table["button_url"] = feat.get("button_url", "/contacto" if is_featured else "")
            tables.append(table)
        return self._base("divi/pricing-tables", children=tables)

    def make_contact_form(self) -> Dict:
        return self._base("divi/contact-form")

    def _build_text_decoration(self, props: Dict) -> Dict:
        """Build decoration object from text props."""
        deco = {}
        for key, val in props.items():
            if key.startswith("text_"):
                if key == "text_color" and val:
                    deco.setdefault("font", {}).setdefault("desktop", {}).setdefault("value", {})["color"] = val
                if key == "text_font_size" and val:
                    deco.setdefault("font", {}).setdefault("desktop", {}).setdefault("value", {})["size"] = val
                if key == "text_alignment" and val:
                    deco.setdefault("font", {}).setdefault("desktop", {}).setdefault("value", {})["textAlign"] = val
                if key == "text_transform" and val:
                    deco.setdefault("font", {}).setdefault("desktop", {}).setdefault("value", {})["textTransform"] = val
                if key == "text_letter_spacing" and val:
                    deco.setdefault("font", {}).setdefault("desktop", {}).setdefault("value", {})["letterSpacing"] = val
                if key == "text_line_height" and val:
                    deco.setdefault("font", {}).setdefault("desktop", {}).setdefault("value", {})["lineHeight"] = val
                if key == "text_font_family" and val:
                    deco.setdefault("font", {}).setdefault("desktop", {}).setdefault("value", {})["font"] = val
        return deco
