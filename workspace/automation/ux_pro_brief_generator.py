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

sys.path.insert(0, str(DAW_ROOT))

_UX_BRIDGE = None

def _get_bridge():
    global _UX_BRIDGE
    if _UX_BRIDGE is None:
        artifacts_dir = DAW_ROOT / "ml-dataset" / "artifacts"
        sys.path.insert(0, str(artifacts_dir))
        from ux_pro_bridge import UXProBridge
        _UX_BRIDGE = UXProBridge()
    return _UX_BRIDGE

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
        "landing": ["hero", "trust-bar", "features", "stats", "testimonials", "cta"],
        "home": ["hero", "trust-bar", "features", "stats", "testimonials", "cta"],
        "portfolio": ["hero", "gallery", "stats", "testimonials", "cta"],
        "pricing": ["hero", "pricing", "faq", "testimonials", "cta"],
        "about": ["hero", "content", "features", "team", "stats", "cta"],
        "contact": ["hero", "content", "contact", "testimonials", "cta"],
        "services": ["hero", "features", "process", "pricing", "faq", "cta"],
        "default": ["hero", "features", "stats", "testimonials", "cta"]
    },
    "design_direction": {
        "mood": "cool_luxury",
        "hero_layout": "centered",
        "about_layout": "centered",
        "features_layout": "grid_3",
        "cta_layout": "centered",
        "motion_intensity": "subtle",
        "card_style": "glass",
        "zone_dividers": True,
        "stagger_hero": True,
        "stagger_cta": True,
        "stagger_stats": True,
        "hero_divider_bottom": "curve",
        "button_gradient": True,
        "heading_text_shadow": True,
        "grain_texture": False
    }
}

_PAGE_LAYOUT_PRESETS = {
    "landing": ["hero", "trust-bar", "features", "stats", "testimonials", "cta"],
    "home": ["hero", "trust-bar", "features", "stats", "testimonials", "cta"],
    "portfolio": ["hero", "gallery", "stats", "testimonials", "cta"],
    "pricing": ["hero", "pricing", "faq", "testimonials", "cta"],
    "about": ["hero", "content", "features", "team", "stats", "cta"],
    "contact": ["hero", "content", "contact", "testimonials", "cta"],
    "services": ["hero", "features", "process", "pricing", "faq", "cta"],
    "default": ["hero", "features", "stats", "testimonials", "cta"],
}

_ART_DIRECTION_PRESETS = {
    "landing": {
        "mood": "cool_luxury",
        "hero_layout": "asymmetric",
        "about_layout": "image_left",
        "features_layout": "grid_3",
        "cta_layout": "full_width",
        "motion_intensity": "dramatic",
        "card_style": "glass",
        "hero_divider_bottom": "wave",
        "stagger_hero": True,
        "stagger_cta": True,
        "stagger_stats": True,
    },
    "home": {
        "mood": "cool_luxury",
        "hero_layout": "centered",
        "features_layout": "grid_3",
        "cta_layout": "1_3_2_3",
        "motion_intensity": "subtle",
        "card_style": "glass",
    },
    "portfolio": {
        "mood": "tech_glass",
        "hero_layout": "asymmetric",
        "about_layout": "image_left",
        "features_layout": "grid_2",
        "cta_layout": "full_width",
        "motion_intensity": "dramatic",
        "card_style": "glass",
        "hero_divider_bottom": "curve",
        "stagger_hero": True,
        "stagger_cta": True,
    },
    "pricing": {
        "mood": "warm_minimal",
        "hero_layout": "centered",
        "features_layout": "grid_2",
        "cta_layout": "centered",
        "motion_intensity": "subtle",
        "card_style": "outline",
        "hero_divider_bottom": "curve",
        "stagger_stats": True,
    },
    "about": {
        "mood": "academic_night",
        "hero_layout": "centered",
        "about_layout": "2_5_3_5",
        "features_layout": "grid_3",
        "cta_layout": "1_3_2_3",
        "motion_intensity": "subtle",
        "card_style": "outline",
        "hero_divider_bottom": "wave",
        "stagger_hero": True,
    },
    "contact": {
        "mood": "cool_luxury",
        "hero_layout": "centered",
        "features_layout": "grid_2",
        "cta_layout": "full_width",
        "motion_intensity": "subtle",
        "card_style": "solid",
        "zone_dividers": False,
    },
    "services": {
        "mood": "organic_modern",
        "hero_layout": "asymmetric",
        "about_layout": "image_left",
        "features_layout": "grid_3",
        "cta_layout": "full_width",
        "motion_intensity": "dramatic",
        "card_style": "glass",
        "hero_divider_bottom": "wave",
        "stagger_hero": True,
        "stagger_cta": True,
        "stagger_stats": True,
    },
    "default": {
        "mood": "cool_luxury",
        "hero_layout": "centered",
        "features_layout": "grid_3",
        "cta_layout": "centered",
        "motion_intensity": "subtle",
        "card_style": "glass",
    },
}

_TONE_BY_PAGE_TYPE = {
    "landing": "premium",
    "home": "premium",
    "portfolio": "vibrant",
    "pricing": "professional",
    "about": "editorial",
    "contact": "professional",
    "services": "professional",
    "default": "premium",
}

_ART_DIRECTION_NOTES = {
    "landing": {
        "narrative": "hero-led conversion page with clear proof and a strong closing CTA",
        "composition": "asymmetric",
        "rhythm": "expansive",
        "surface": "glass-on-dark",
        "motion": "layered reveal",
    },
    "home": {
        "narrative": "brand overview page with enough visual lift to feel editorial, not template-like",
        "composition": "balanced-asymmetric",
        "rhythm": "steady",
        "surface": "cool-luxury",
        "motion": "measured reveal",
    },
    "portfolio": {
        "narrative": "case-study showcase with image-first storytelling and measured proof",
        "composition": "editorial-grid",
        "rhythm": "gallery-paced",
        "surface": "dark-glass",
        "motion": "progressive reveal",
    },
    "pricing": {
        "narrative": "pricing ladder with confidence-building proof and a frictionless decision path",
        "composition": "centered",
        "rhythm": "clarity-first",
        "surface": "light-contrast",
        "motion": "quiet emphasis",
    },
    "about": {
        "narrative": "brand story page with authority, credibility and a measured progression",
        "composition": "split-editorial",
        "rhythm": "sectional",
        "surface": "deep-ink",
        "motion": "restrained",
    },
    "contact": {
        "narrative": "low-friction contact page with trust cues and clear next actions",
        "composition": "centered",
        "rhythm": "calm",
        "surface": "soft-contrast",
        "motion": "minimal",
    },
    "services": {
        "narrative": "service catalog with layered evidence and a premium conversion finish",
        "composition": "asymmetric",
        "rhythm": "modular",
        "surface": "dark-luxury",
        "motion": "confident",
    },
    "default": {
        "narrative": "premium brand page with enough contrast and hierarchy to avoid filler",
        "composition": "asymmetric",
        "rhythm": "balanced",
        "surface": "cool-luxury",
        "motion": "measured",
    },
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


def _merge_page_layouts() -> dict:
    layouts = dict(_PAGE_LAYOUT_PRESETS)
    bank_layouts = _get("page_layouts", {})
    if isinstance(bank_layouts, dict):
        layouts.update(bank_layouts)
    return layouts


def _merge_design_direction(page_type: str) -> dict:
    base = dict(_DEFAULT["design_direction"])
    bank_direction = _get("design_direction", {})
    if isinstance(bank_direction, dict):
        base.update(bank_direction)
    base.update(_ART_DIRECTION_PRESETS.get(page_type, _ART_DIRECTION_PRESETS["default"]))
    return base

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
    if any(kw in q for kw in ("portfolio", "portafolio", "gallery", "work", "works", "case study", "proyectos", "proyecto")):
        return "portfolio"
    if any(kw in q for kw in ("pricing", "price", "precios", "planes", "tarifas", "coste", "cost")):
        return "pricing"
    if any(kw in q for kw in ("servicio", "services", "paquete", "package")):
        return "services"
    if any(kw in q for kw in ("home", "inicio", "principal", "landing", "portada")):
        return "landing"
    return "landing"

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
    layouts = _merge_page_layouts()
    dd = _merge_design_direction(page_type)

    bridge = _get_bridge()
    if bridge and bridge.is_ready:
        bridge_dd = bridge.to_design_direction(query, brand)
        if bridge_dd:
            dd.update(bridge_dd)

    brief = {
        "title": query,
        "slug": slug,
        "page_type": page_type,
        "tone": _TONE_BY_PAGE_TYPE.get(page_type, _TONE_BY_PAGE_TYPE["default"]),
        "description": f"{brand} - {page_type}" if brand else f"Page - {page_type}",
        "design_direction": dd,
        "art_direction": {
            "page_type": page_type,
            **_ART_DIRECTION_NOTES.get(page_type, _ART_DIRECTION_NOTES["default"]),
        },
        "sections": [],
    }

    for sec in layouts.get(page_type, layouts.get("default", _PAGE_LAYOUT_PRESETS["default"])):
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
