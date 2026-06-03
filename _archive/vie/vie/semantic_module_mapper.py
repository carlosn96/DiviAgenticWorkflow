"""SemanticModuleMapper — Mapea campos semanticos del brief a modulos Divi nativos.

Lee los 103 schemas de workspace/data/modules/ para saber que atributos soporta cada modulo.
"""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


# Mapeo semantico: campo del brief → modulo Divi nativo
SEMANTIC_MAP = {
    "image_url": "divi/image",
    "video_url": "divi/video",
    "gallery": "divi/gallery",
    "slider": "divi/slider",
    "testimonials": "divi/testimonial",
    "pricing": "divi/pricing-tables",
    "map": "divi/map",
    "form": "divi/contact-form",
    "accordion": "divi/accordion",
    "tabs": "divi/tabs",
    "audio": "divi/audio",
    "number_counter": "divi/number-counter",
    "eyebrow": "divi/text",
    "title": "divi/heading",
    "text": "divi/text",
    "body": "divi/text",
    "button": "divi/button",
    "blurb": "divi/blurb",
    "divider": "divi/divider",
    "logo": "divi/image",
    "person": "divi/blurb",
    "step": "divi/blurb",
    "quote": "divi/testimonial",
}

# Campos que cada modulo espera (del schema)
MODULE_SCHEMAS: Dict[str, Dict] = {}


def _load_module_schemas():
    """Carga los 103 schemas de modulos desde workspace/data/modules/."""
    global MODULE_SCHEMAS
    modules_dir = Path("DAW_bundle/workspace/data/modules")
    if not modules_dir.exists():
        return
    for f in modules_dir.glob("*.json"):
        try:
            with open(f, "r", encoding="utf-8") as fp:
                data = json.load(fp)
                slug = f.stem
                MODULE_SCHEMAS[f"divi/{slug}"] = data
        except Exception:
            continue

_load_module_schemas()


class SemanticModuleMapper:
    """Mapea un dict de seccion (del brief) a una lista de modulos Divi nativos."""

    @staticmethod
    def map_section(sec_def: Dict) -> List[Dict]:
        """Convierte una seccion del brief en una lista de modulos Divi nativos.

        Cada modulo es un dict con: type, module, [atributos especificos], decoration.
        """
        st = sec_def.get("section_type", sec_def.get("type", "generic"))
        modules = []

        # 1. Eyebrow
        eyebrow = sec_def.get("eyebrow", "")
        if eyebrow:
            modules.append(SemanticModuleMapper._make_text(eyebrow, style="eyebrow"))

        # 2. Title / Heading
        title = sec_def.get("title", sec_def.get("heading", ""))
        if title:
            level = "h1" if st in ("hero", "hero-centered", "hero-split") else "h2"
            modules.append(SemanticModuleMapper._make_heading(title, level=level))

        # 3. Divider (si hay titulo y texto)
        text = sec_def.get("text", sec_def.get("body", ""))
        if title and text:
            modules.append({"type": "divi/divider", "module": "divi/divider", "show_divider": "on"})

        # 4. Body text
        if text:
            modules.append(SemanticModuleMapper._make_text(text, style="body"))

        # 5. Botones
        btn_text = sec_def.get("btn_primary_text", "")
        btn_url = sec_def.get("btn_primary_url", "#")
        if btn_text:
            modules.append(SemanticModuleMapper._make_button(btn_text, btn_url, style="primary"))

        btn2_text = sec_def.get("btn_secondary_text", "")
        btn2_url = sec_def.get("btn_secondary_url", "#")
        if btn2_text:
            modules.append(SemanticModuleMapper._make_button(btn2_text, btn2_url, style="secondary"))

        # 6. Image (si existe)
        image_url = sec_def.get("image", "")
        if image_url:
            modules.append(SemanticModuleMapper._make_image(image_url, alt=title or ""))

        # 7. Video (si existe)
        video_url = sec_def.get("video", "")
        if video_url:
            modules.append(SemanticModuleMapper._make_video(video_url))

        # 8. Gallery / Slider
        gallery = sec_def.get("gallery", [])
        if gallery:
            modules.append(SemanticModuleMapper._make_gallery(gallery))

        slider = sec_def.get("slider", [])
        if slider:
            modules.append(SemanticModuleMapper._make_slider(slider))

        # 9. Items → Blurbs (except trust-bar, which uses items as logos)
        items = sec_def.get("items", [])
        if items and st != "trust-bar":
            for item in items:
                modules.append(SemanticModuleMapper._make_blurb(item))

        # 10. Stats → Number-counters
        stats = sec_def.get("stats", [])
        if stats:
            for stat in stats:
                modules.append(SemanticModuleMapper._make_number_counter(stat))

        # 11. Testimonials
        testimonials = sec_def.get("testimonials", [])
        if testimonials:
            for t in testimonials:
                modules.append(SemanticModuleMapper._make_testimonial(t))

        # 12. Pricing (soporta "pricing" y "packages")
        pricing = sec_def.get("pricing", sec_def.get("packages", []))
        if pricing:
            for p in pricing:
                modules.append(SemanticModuleMapper._make_pricing_table(p))

        # 13. Map
        map_data = sec_def.get("map", None)
        if map_data:
            modules.append(SemanticModuleMapper._make_map(map_data))

        # 14. Form
        form_data = sec_def.get("form", None)
        if form_data:
            modules.append(SemanticModuleMapper._make_contact_form(form_data))

        # 15. Trust bar (logos)
        trust_items = sec_def.get("items", []) if st == "trust-bar" else []
        if st == "trust-bar" and trust_items:
            for item in trust_items:
                if "image" in item:
                    modules.append(SemanticModuleMapper._make_image(item["image"], alt=item.get("alt", "")))

        # 16. Team / People
        team = sec_def.get("team", [])
        if team:
            for person in team:
                modules.append(SemanticModuleMapper._make_person(person))

        # 17. Accordion / FAQ
        accordion = sec_def.get("accordion", [])
        if accordion:
            modules.append(SemanticModuleMapper._make_accordion(accordion))

        return modules

    @staticmethod
    def _make_text(content: str, style: str = "body") -> Dict:
        return {
            "type": "divi/text",
            "module": "divi/text",
            "content": content if content.startswith("<") else f"<p>{content}</p>",
            "_semantic_style": style,
        }

    @staticmethod
    def _make_heading(content: str, level: str = "h2") -> Dict:
        return {
            "type": "divi/heading" if level == "h1" else "divi/text",
            "module": "divi/heading" if level == "h1" else "divi/text",
            "content": f"<{level}>{content}</{level}>",
            "level": level,
            "_semantic_style": "heading",
        }

    @staticmethod
    def _make_button(text: str, url: str, style: str = "primary") -> Dict:
        return {
            "type": "divi/button",
            "module": "divi/button",
            "button_text": text,
            "button_url": url,
            "_semantic_style": style,
        }

    @staticmethod
    def _make_image(src: str, alt: str = "") -> Dict:
        return {
            "type": "divi/image",
            "module": "divi/image",
            "image": {"innerContent": {"desktop": {"value": {"src": src, "alt": alt}}}},
            "_semantic_style": "image",
        }

    @staticmethod
    def _make_video(src: str) -> Dict:
        return {
            "type": "divi/video",
            "module": "divi/video",
            "video": {"src": src},
            "_semantic_style": "video",
        }

    @staticmethod
    def _make_gallery(images) -> Dict:
        # Accept List[str] (URLs) or List[Dict]
        if images and isinstance(images[0], str):
            image_dicts = [{"src": url, "alt": ""} for url in images]
        else:
            image_dicts = images
        return {
            "type": "divi/gallery",
            "module": "divi/gallery",
            "gallery": {"images": image_dicts},
            "_semantic_style": "gallery",
        }

    @staticmethod
    def _make_slider(slides: List[Dict]) -> Dict:
        return {
            "type": "divi/slider",
            "module": "divi/slider",
            "slider": {"slides": slides},
            "_semantic_style": "slider",
        }

    @staticmethod
    def _make_blurb(item: Dict) -> Dict:
        icon = item.get("icon", "&#xe03a;")
        title = item.get("title", "")
        text = item.get("text", item.get("body", ""))
        return {
            "type": "divi/blurb",
            "module": "divi/blurb",
            "title": title,
            "content": text,
            "icon": icon,
            "_semantic_style": "blurb",
        }

    @staticmethod
    def _make_number_counter(stat: Dict) -> Dict:
        num = stat.get("number", "0")
        label = stat.get("label", "")
        return {
            "type": "divi/number-counter",
            "module": "divi/number-counter",
            "number": str(num).replace("+", "").replace("%", "").strip(),
            "title": label,
            "_semantic_style": "stat",
        }

    @staticmethod
    def _make_testimonial(t: Dict) -> Dict:
        return {
            "type": "divi/testimonial",
            "module": "divi/testimonial",
            "author": {"innerContent": {"desktop": {"value": t.get("name", "")}}},
            "content": {"innerContent": {"desktop": {"value": "<p>" + t.get("text", t.get("quote", "")) + "</p>"}}},
            "portraitUrl": {"innerContent": {"desktop": {"value": t.get("image", "")}}},
            "companyName": {"innerContent": {"desktop": {"value": t.get("role", "")}}},
            "_semantic_style": "testimonial",
        }

    @staticmethod
    def _make_pricing_table(p: Dict) -> Dict:
        features_html = "".join(f"<li>{f}</li>" for f in p.get("features", []))
        return {
            "type": "divi/pricing-table",
            "module": "divi/pricing-table",
            "title": {"innerContent": {"desktop": {"value": p.get("name", "")}}},
            "price": {"innerContent": {"desktop": {"value": p.get("price", "")}}},
            "content": {"innerContent": {"desktop": {"value": "<ul>" + features_html + "</ul>" if features_html else ""}}},
            "featured": {"desktop": {"value": "on" if p.get("highlight") else "off"}},
            "_semantic_style": "pricing",
        }

    @staticmethod
    def _make_map(map_data: Dict) -> Dict:
        return {
            "type": "divi/map",
            "module": "divi/map",
            "map": {
                "address": map_data.get("address", ""),
                "lat": map_data.get("lat", ""),
                "lng": map_data.get("lng", ""),
            },
            "_semantic_style": "map",
        }

    @staticmethod
    def _make_contact_form(form_data: Dict) -> Dict:
        fields = form_data.get("fields", ["name", "email", "message"])
        return {
            "type": "divi/contact-form",
            "module": "divi/contact-form",
            "contact_form": {"fields": fields},
            "_semantic_style": "form",
        }

    @staticmethod
    def _make_person(person: Dict) -> Dict:
        return {
            "type": "divi/blurb",
            "module": "divi/blurb",
            "title": person.get("name", ""),
            "content": person.get("role", ""),
            "image": person.get("image", ""),
            "_semantic_style": "person",
        }

    @staticmethod
    def _make_accordion(items: List[Dict]) -> Dict:
        return {
            "type": "divi/accordion",
            "module": "divi/accordion",
            "accordion": {"items": items},
            "_semantic_style": "accordion",
        }
