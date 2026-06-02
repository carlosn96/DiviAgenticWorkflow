#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import sys
import argparse
import random
import re
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DAW_ROOT = SCRIPT_DIR.parent.parent
UI_UX_DIR = DAW_ROOT / "ui-ux-pro-max" / "scripts"

sys.path.append(str(UI_UX_DIR))
sys.path.insert(0, str(DAW_ROOT))
try:
    from design_system import DesignSystemGenerator
except ImportError:
    print(f"Error: Could not import DesignSystemGenerator from {UI_UX_DIR}")
    sys.exit(1)

# ── Content Bank ───────────────────────────────────────────────────────
# All per-brand data lives in site/<DAW_SITE>/brand/_content_bank.json:
#   copy, page_layouts, design_direction, etc.
# The fallback below exists only so the pipeline doesn't crash without one.
# It produces generic output — edit _content_bank.json per brand for real work.

_DEFAULT = {
    "hero_titles": ["{brand}", "Bienvenido"],
    "hero_subtexts": ["Servicios profesionales."],
    "features": [{"title": "Calidad", "text": "Excelencia en cada servicio."}],
    "stats": [{"number": "10+", "label": "A\u00f1os"}],
    "team": [{"name": "Equipo", "role": "Profesional", "text": "Comprometido."}],
    "testimonials": [{"name": "Cliente", "role": "Cliente", "text": "Excelente."}],
    "cta": {"title": "\u00bfHablamos?", "text": "Cont\u00e1ctanos.", "btn": "Contactar"},
    "process": [{"title": "Proceso", "text": "Te acompa\u00f1amos.", "icon": "&#xe03a;"}],
    "gallery_titles": ["Proyecto 1"],
    "content_text": "En {brand}, hacemos las cosas bien.",
    "features_eyebrow_about": "SERVICIOS",
    "features_eyebrow_home": "QU\u00c9 OFRECEMOS",
    "features_title_about": "Nosotros",
    "features_title_home": "Lo Que Hacemos",
    "gallery_eyebrow": "GALER\u00cdA",
    "gallery_title": "Trabajo",
    "process_eyebrow": "PROCESO",
    "process_title": "C\u00f3mo Trabajamos",
    "pricing": [],
    "faq": [],
    "logos": [],
    "contact": {"title": "Cont\u00e1ctanos", "text": ""},
    "page_layouts": {
        "about": ["hero", "features", "cta"],
        "home": ["hero", "features", "cta"],
        "contact": ["hero", "features", "cta"],
        "services": ["hero", "features", "cta"],
        "default": ["hero", "features", "cta"]
    },
    "design_direction": {
        "mood": "cool_luxury",
        "color_temperature": "cool_on_dark",
        "typography_style": "sans_premium",
        "layout_rhythm": "centered",
        "spacing_density": "generous",
        "accent_material": "blue_brilliant",
        "motion_intensity": "subtle"
    }
}

_CACHE = {}

def _load() -> dict:
    if "bank" in _CACHE:
        return _CACHE["bank"]
    try:
        sys.path.insert(0, str(DAW_ROOT))
        from daw.cfg import load_daw_site, get_brand_dir
        site = load_daw_site()
        p = get_brand_dir() / "_content_bank.json"
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
                _CACHE["bank"] = data
                return data
    except Exception:
        pass
    _CACHE["bank"] = _DEFAULT
    return _DEFAULT

def _get(key: str, default=None):
    return _load().get(key, _DEFAULT.get(key, default))

# ── Helpers ────────────────────────────────────────────────────────────

def _load_brand_name() -> str:
    try:
        sys.path.insert(0, str(DAW_ROOT))
        from daw.cfg import load_daw_site, get_brand_dir
        site = load_daw_site()
        p = get_brand_dir() / "_design_vars.json"
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                d = json.load(f)
            return d.get("brand_name", "") or d.get("site_name", "") or ""
    except Exception:
        pass
    return ""

def _slugify(s: str) -> str:
    s = s.lower().strip()
    for a, b in [('\u00e1','a'),('\u00e9','e'),('\u00ed','i'),('\u00f3','o'),('\u00fa','u'),('\u00fc','u'),('\u00f1','n')]:
        s = s.replace(a, b)
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-') or 'brand'

def _img(brand: str, section: str, i: int = 0) -> str:
    return f"https://picsum.photos/seed/{_slugify(brand or 'brand')}-{section}{i}/800/600"

def _img_sq(brand: str, section: str, i: int = 0, size: int = 400) -> str:
    return f"https://picsum.photos/seed/{_slugify(brand or 'brand')}-{section}{i}/{size}/{size}"

def _brand(s: str, b: str) -> str:
    return s.replace("{brand}", b) if b and "{brand}" in s else s

def _detect_page_type(q: str) -> str:
    q = q.lower()
    if any(kw in q for kw in ("acerca", "about", "nosotros", "quienes", "historia", "team", "equipo")):
        return "about"
    if any(kw in q for kw in ("contacto", "contact", "ubicaci\u00f3n", "direcci\u00f3n")):
        return "contact"
    if any(kw in q for kw in ("servicio", "services", "paquete", "package", "precio", "pricing")):
        return "services"
    if any(kw in q for kw in ("home", "inicio", "principal", "landing", "portada")):
        return "home"
    return "default"

# ── Section builders ───────────────────────────────────────────────────

def _hero(brand: str) -> dict:
    titles = _get("hero_titles")
    subs = _get("hero_subtexts")
    cta = _get("cta")
    return {
        "section_type": "hero",
        "eyebrow": (brand or "WELCOME").upper(),
        "title": _brand(random.choice(titles), brand),
        "text": random.choice(subs),
        "btn_primary_text": cta["btn"],
        "btn_primary_url": "/",
        "image": _img(brand, "hero"),
    }

def _stats() -> dict:
    return {"section_type": "stats", "stats": _get("stats")}

def _features(page_type: str) -> dict:
    items = _get("features")[:]
    random.shuffle(items)
    return {
        "section_type": "features",
        "eyebrow": _get("features_eyebrow_about") if page_type == "about" else _get("features_eyebrow_home"),
        "title": _get("features_title_about") if page_type == "about" else _get("features_title_home"),
        "items": [
            {"title": f["title"], "icon": random.choice(["&#xe03a;","&#xe065;","&#xe0bf;","&#xe050;","&#xe052;"]), "text": f["text"]}
            for f in items[:4]
        ],
    }

def _team(brand: str) -> dict:
    return {
        "section_type": "team",
        "eyebrow": "EQUIPO",
        "title": f"Conoce a {brand}" if brand else "Nuestro Equipo",
        "members": [
            {**m, "image": _img_sq(brand, "team", i+1)}
            for i, m in enumerate(_get("team"))
        ],
    }

def _process() -> dict:
    return {
        "section_type": "process",
        "eyebrow": _get("process_eyebrow"),
        "title": _get("process_title"),
        "phases": _get("process"),
    }

def _testimonials(brand: str) -> dict:
    return {
        "section_type": "testimonials",
        "eyebrow": "TESTIMONIOS",
        "title": "Lo Que Dicen Nuestros Clientes",
        "testimonials": [{**m, "text": _brand(m.get("text",""), brand)} for m in _get("testimonials")],
    }

def _cta(brand: str) -> dict:
    c = _get("cta")
    return {
        "section_type": "cta",
        "eyebrow": "CONTACTO",
        "title": _brand(c["title"], brand),
        "text": c["text"],
        "btn_primary_text": c["btn"],
        "btn_primary_url": "/contacto",
    }

def _gallery(brand: str) -> dict:
    return {
        "section_type": "gallery",
        "eyebrow": _get("gallery_eyebrow"),
        "title": _get("gallery_title"),
        "items": [
            {"image": _img(brand, "gallery", i+1), "alt": t, "title": t}
            for i, t in enumerate(_get("gallery_titles")[:3])
        ],
    }

def _content(brand: str, title: str = "") -> dict:
    return {
        "section_type": "content",
        "eyebrow": "NOSOTROS" if brand else "ABOUT",
        "title": title or (f"Sobre {brand}" if brand else "Sobre Nosotros"),
        "text": _brand(_get("content_text"), brand),
        "image": _img(brand, "content"),
    }

def _pricing() -> dict:
    return {
        "section_type": "pricing",
        "features": _get("pricing"),
    }

def _faq() -> dict:
    return {
        "section_type": "faq",
        "eyebrow": "FAQ",
        "title": "Preguntas Frecuentes",
        "faqs": _get("faq"),
    }

def _trust_bar() -> dict:
    return {
        "section_type": "trust-bar",
        "items": _get("logos"),
    }

def _contact(brand: str) -> dict:
    c = _get("contact")
    return {
        "section_type": "contact",
        "title": c.get("title", "Cont\u00e1ctanos"),
        "text": c.get("text", ""),
    }

_SECTION_BUILDERS = {
    "hero": _hero,
    "stats": _stats,
    "features": _features,
    "team": _team,
    "process": _process,
    "testimonials": _testimonials,
    "cta": _cta,
    "gallery": _gallery,
    "content": _content,
    "pricing": _pricing,
    "faq": _faq,
    "trust-bar": _trust_bar,
    "contact": _contact,
}

def generate_brief_for_page(query: str, brand: str = "", page_type: str = "") -> dict:
    if not page_type:
        page_type = _detect_page_type(query)
    if not brand:
        brand = _load_brand_name()

    slug = query.lower().replace(" ", "-")[:40]
    layouts = _get("page_layouts")
    dd = _get("design_direction")

    brief = {
        "title": query,
        "slug": slug,
        "tone": "premium",
        "description": f"{brand} - {page_type}" if brand else f"Page - {page_type}",
        "design_direction": dd,
        "sections": [],
    }

    for sec in layouts.get(page_type, layouts.get("default", _DEFAULT["page_layouts"]["default"])):
        builder = _SECTION_BUILDERS.get(sec)
        if builder:
            if sec in ("features",):
                brief["sections"].append(builder(page_type))
            elif sec in ("hero", "team", "testimonials", "cta", "content", "gallery", "contact"):
                brief["sections"].append(builder(brand))
            else:
                brief["sections"].append(builder())

    return brief


def generate_brief(query):
    return generate_brief_for_page(query, _load_brand_name(), _detect_page_type(query))

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--query", default="Landing Page")
    p.add_argument("--out", default=None)
    a = p.parse_args()
    b = generate_brief(a.query)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            json.dump(b, f, indent=2, ensure_ascii=False)
        print(f"Brief generated at {a.out}")
    else:
        print(json.dumps(b, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
