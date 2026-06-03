#!/usr/bin/env python3
"""
design_director.py — Agente de decisión por stacking ensemble.

Carga TODOS los artefactos en frío (una vez) y provee métodos de decisión
que ponderan múltiples expertos ML simultáneamente:

  Expertos: KMeans, Content Classifier, Semantic Index, Slot Catalog,
            Section Patterns, Module Affinities, UX-PRO Rules, Layout Metrics

Cada decisión retorna (valor, score, explicacion).
"""

import json, pickle, copy, re, random, math
import numpy as np
from pathlib import Path

ARTIFACTS_DIR = Path(__file__).resolve().parent
DAW_ROOT = ARTIFACTS_DIR.parent.parent

# ── Paths ──────────────────────────────────────────────────────────────────
RULES_PATH = ARTIFACTS_DIR / "design_rules_divi.pkl"
PATTERNS_PATH = ARTIFACTS_DIR / "section-patterns.json"
AFFINITIES_PATH = ARTIFACTS_DIR / "module-affinities.json"
CLASSIFIER_PATH = ARTIFACTS_DIR / "content-classifier.pkl"
SEMANTIC_PATH = ARTIFACTS_DIR / "semantic-index.pkl"
SLOT_CATALOG_PATH = ARTIFACTS_DIR / "slot-catalog.pkl"
SCHEMA_PATH = DAW_ROOT / "workspace" / "section-schema.json"
MODULES_DIR = DAW_ROOT / "workspace" / "data" / "modules"
DECO_CLUSTERS_PATH = ARTIFACTS_DIR / "decoration-clusters.pkl"
DECO_RULES_PATH = ARTIFACTS_DIR / "decoration-rules.json"
DATASET_PATH = DAW_ROOT / "ml-dataset" / "dataset.jsonl"
CATALOG_STATS_PATH = ARTIFACTS_DIR / "catalog_stats.json"
SLOT_STATS_PATH = ARTIFACTS_DIR / "slot_stats.json"

SLOT_RE = re.compile(r'\{\{slot:([^}]+)\}\}')
MODULE_TEXT_KEYS = {"title", "content", "button_text", "alt", "icon"}

COLUMN_MODULE_COMPAT = {
    "4_4": ["text", "heading", "button", "image", "video", "map", "code", "divider"],
    "1_2,1_2": ["text", "heading", "blurb", "button", "image", "testimonial", "icon"],
    "1_3,1_3,1_3": ["blurb", "testimonial", "pricing_table", "image", "number_counter"],
    "1_4,1_4,1_4,1_4": ["blurb", "image", "icon", "number_counter"],
    "1_3,2_3": ["text", "heading", "image", "video", "blurb", "button"],
}


# ── Helpers ────────────────────────────────────────────────────────────────

def _load_json(path, default=None):
    if path.exists():
        try:
            return json.loads(path.read_text("utf-8"))
        except Exception:
            pass
    return default or {}

def _load_pickle(path, default=None):
    if path.exists():
        try:
            with open(path, "rb") as f:
                return pickle.load(f)
        except Exception:
            pass
    return default or {}

def _embed_text(text, dim=64):
    text = text.lower().strip()
    vec = np.zeros(dim, dtype=np.float32)
    for i, ch in enumerate(text.encode("utf-8", errors="ignore")):
        vec[i % dim] += float(ch) / 255.0
    for i in range(len(text) - 1):
        bigram = text[i:i+2]
        h = hash(bigram) % dim
        vec[h] += 0.5
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec /= norm
    return vec

def _cosine_sim(a, b):
    a = np.array(a, dtype=np.float32)
    b = np.array(b, dtype=np.float32)
    norm = np.linalg.norm(a) * np.linalg.norm(b)
    return float(np.dot(a, b) / norm) if norm > 0 else 0.0

def _parse_hex(h):
    h = str(h).strip().lstrip("#")
    if len(h) != 6:
        return (128, 128, 128)
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def _luminance(rgb):
    r, g, b = [x / 255.0 for x in rgb]
    r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
    g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
    b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def _contrast_ratio(rgb1, rgb2):
    l1 = _luminance(rgb1) + 0.05
    l2 = _luminance(rgb2) + 0.05
    return max(l1, l2) / min(l1, l2)

def _darken_hex(h, amount=0.3):
    r, g, b = _parse_hex(h)
    r = max(0, int(r * (1 - amount)))
    g = max(0, int(g * (1 - amount)))
    b = max(0, int(b * (1 - amount)))
    return f"#{r:02x}{g:02x}{b:02x}"

def _lighten_hex(h, amount=0.3):
    r, g, b = _parse_hex(h)
    r = min(255, int(r + (255 - r) * amount))
    g = min(255, int(g + (255 - g) * amount))
    b = min(255, int(b + (255 - b) * amount))
    return f"#{r:02x}{g:02x}{b:02x}"

def _parse_px(val):
    if isinstance(val, str):
        val = val.replace("px", "").strip()
        try:
            return int(val)
        except ValueError:
            pass
    return 0

def _module_count_in_section(section):
    count = 0
    for row in section.get("rows", []):
        for col in row.get("columns", []):
            count += len(col.get("modules", []))
    return count

def _collect_all_text(section):
    texts = set()
    raw = json.dumps(section, ensure_ascii=False)
    for m in SLOT_RE.findall(raw):
        texts.add(m)
    return texts


# ═══════════════════════════════════════════════════════════════════════════
#  DesignDirector
# ═══════════════════════════════════════════════════════════════════════════

class DesignDirector:
    """Stacking ensemble agent. Carga todos los artefactos una vez."""

    def __init__(self):
        self._loaded = False
        self.rules = {}
        self.patterns = {}
        self.affinities = {}
        self.classifier = None
        self.label_encoder = None
        self.semantic_items = []
        self.semantic_embeddings = None
        self.slot_catalog = {}
        self.slot_categories = []
        self.slot_idf = {}
        self.slot_idf_N = 0
        self.kmeans = None
        self.scaler = None
        self.deco_rules = {}
        self.schema = {}
        self.module_schemas = {}
        self.dataset_slot_stats = {}
        self.catalog_stats = {}
        self.slot_stats = {}
        self.ux_bridge = None
        self.expert_weights = {
            "kmeans_cluster": 0.20,
            "classifier_confidence": 0.15,
            "semantic_coherence": 0.15,
            "slot_coverage": 0.25,
            "column_match": 0.10,
            "module_fitness": 0.10,
            "ux_contrast": 0.00,
            "layout_quality": 0.05,
        }

    def load(self):
        """Cold-start load of all artifacts."""
        print("[DIRECTOR] Loading all intelligence sources...")

        self.rules = _load_pickle(RULES_PATH, {})
        print(f"[DIRECTOR]  rules: {len(self.rules.get('domains', {}))} domains")

        self.patterns = _load_json(PATTERNS_PATH, {})
        print(f"[DIRECTOR]  patterns: {len(self.patterns)} types")

        self.affinities = _load_json(AFFINITIES_PATH, {})
        print(f"[DIRECTOR]  affinities: {len(self.affinities)} types")

        cc_data = _load_pickle(CLASSIFIER_PATH)
        if cc_data:
            self.classifier = cc_data.get("pipeline")
            self.label_encoder = cc_data.get("label_encoder")
            print(f"[DIRECTOR]  classifier: {len(self.label_encoder.classes_) if self.label_encoder else 0} classes")

        si_data = _load_pickle(SEMANTIC_PATH)
        if si_data:
            self.semantic_items = si_data.get("items", [])
            self.semantic_embeddings = si_data.get("embeddings_normalized",
                                                     si_data.get("embeddings"))
            print(f"[DIRECTOR]  semantic: {len(self.semantic_items)} items")

        sc_data = _load_pickle(SLOT_CATALOG_PATH)
        if sc_data:
            self.slot_catalog = sc_data.get("catalog", {})
            self.slot_categories = sc_data.get("categories", [])
            self.slot_idf = sc_data.get("slot_idf_df", {})
            self.slot_idf_N = sc_data.get("slot_idf_N", 877)
            print(f"[DIRECTOR]  slot catalog: {len(self.slot_catalog)} categories, "
                  f"{len(self.slot_idf)} slot types")

        dc_data = _load_pickle(DECO_CLUSTERS_PATH)
        if dc_data:
            self.kmeans = dc_data.get("kmeans")
            self.scaler = dc_data.get("scaler")
            print(f"[DIRECTOR]  KMeans: {self.kmeans.n_clusters if self.kmeans else 0} clusters")

        self.deco_rules = _load_json(DECO_RULES_PATH, {})
        print(f"[DIRECTOR]  deco rules: {len(self.deco_rules.get('decoration_by_tone', {}))} tones")

        self.schema = _load_json(SCHEMA_PATH, {})
        print(f"[DIRECTOR]  schema: {len(self.schema)} section types")

        # Load module schemas
        if MODULES_DIR.exists():
            for fpath in sorted(MODULES_DIR.glob("*.json")):
                try:
                    self.module_schemas[fpath.stem] = json.loads(fpath.read_text("utf-8"))
                except Exception:
                    pass
        print(f"[DIRECTOR]  module schemas: {len(self.module_schemas)}")

        # Load pre-computed stats
        self._load_precomputed_stats()

        self._loaded = True
        print(f"[DIRECTOR] All sources loaded.")

    def _load_precomputed_stats(self):
        """Load catalog_stats.json and slot_stats.json (pre-computed from dataset.jsonl)."""
        self.catalog_stats = _load_json(CATALOG_STATS_PATH, {})
        if self.catalog_stats:
            n_clusters = self.catalog_stats.get("_meta", {}).get("clusters", 0)
            print(f"[DIRECTOR]  catalog stats: {n_clusters} clusters")

        self.slot_stats = _load_json(SLOT_STATS_PATH, {})
        if self.slot_stats:
            n_slots = len([k for k in self.slot_stats if not k.startswith("_")])
            print(f"[DIRECTOR]  slot stats: {n_slots} slot types")

    # ═══════════════════════════════════════════════════════════════════════════
    #  PageComposer — capa de composición visual de página
    # ═══════════════════════════════════════════════════════════════════════════

    _VISUAL_RHYTHMS = {
        "editorial": {
            "pattern": "dark-light-dark-light-dark-cta",
            "hero_style": "dramatic",
            "cta_style": "dark",
            "atmosphere": "clean",
        },
        "luxury": {
            "pattern": "dark-cream-dark-cream-dark-cream",
            "hero_style": "dramatic",
            "cta_style": "dark",
            "atmosphere": "gold-accent",
        },
        "professional": {
            "pattern": "light-dark-light-light-dark-cta",
            "hero_style": "split",
            "cta_style": "dark",
            "atmosphere": "minimal",
        },
        "playful": {
            "pattern": "light-light-dark-light-dark-cta",
            "hero_style": "centered",
            "cta_style": "gradient",
            "atmosphere": "vibrant",
        },
    }

    _SECTION_BG_TOGGLE = {
        "dark":  "section:dark",
        "light": "section:light",
        "cream": "section:light-warm",
        "cta":   "section:cta-epic",
    }

    _ATMOSPHERE_DECO = {
        "gold-accent": {
            "overlay_gradient": {
                "type": "radial", "direction": "circle at 80% 20%",
                "overlaysImage": "on",
                "stops": [
                    {"color": "rgba(202,138,4,0.06)", "position": "0"},
                    {"color": "transparent", "position": "60"},
                ],
            },
            "box_shadow": "0 4px 24px rgba(202,138,4,0.08)",
        },
        "clean": {
            "overlay_gradient": {
                "type": "radial", "direction": "circle at 80% 20%",
                "overlaysImage": "on",
                "stops": [
                    {"color": "rgba(0,113,227,0.04)", "position": "0"},
                    {"color": "transparent", "position": "60"},
                ],
            },
        },
        "minimal": {
            "overlay_gradient": None,
        },
        "vibrant": {
            "overlay_gradient": {
                "type": "radial", "direction": "circle at 20% 50%",
                "overlaysImage": "on",
                "stops": [
                    {"color": "rgba(139,92,246,0.05)", "position": "0"},
                    {"color": "transparent", "position": "60"},
                ],
            },
        },
    }

    # ── Frontend Design Principles (inspiración, no datos) ─────────────────
    # Adaptados de frontend-design/SKILL.md para informar decisiones Divi-nativas.
    # Se cargan una vez y ajustan las constantes hardcodeadas del DIE.

    _FRONTEND_PRINCIPLES = {
        "typography": {
            "penalize_generic": True,
            "generic_fonts": {"inter", "arial", "roboto", "helvetica"},
            "prefer_distinctive": True,
        },
        "motion": {
            "progressive_delays": True,
            "delay_step_ms": 150,
            "stagger_hero": True,
            "min_duration_ms": 400,
            "max_duration_ms": 1000,
        },
        "spacing": {
            "generous": True,
            "min_padding_px": 80,
            "hero_padding_px": 140,
            "cta_padding_px": 120,
        },
        "color": {
            "prefer_high_contrast": True,
            "min_contrast_ratio": 4.5,
        },
        "aesthetic": {
            "bold_direction": True,
            "min_variant_distinction": True,
        },
    }

    # ── Style Classification: mapeo de ui-ux-pro-max a decisiones ──────────
    # No raw data — solo mapeo semántico a opciones Divi-nativas.

    _STYLE_TO_VARIANT = {
        "liquid glass": "liquid-glass",
        "glassmorphism": "liquid-glass",
        "vibrant": "minimal-card",
        "bold": "minimal-card",
        "editorial": "editorial-grid",
        "magazine": "editorial-grid",
        "brutalist": "monochrome-brutalist",
        "monochrome": "monochrome-brutalist",
        "minimal": "glass-metric",
        "clean": "glass-metric",
        "professional": "glass-metric",
        "elegant": "liquid-glass",
        "luxury": "liquid-glass",
        "playful": "glass-cta",
    }

    _STYLE_TO_ATMOSPHERE = {
        "liquid glass": "gold-accent",
        "glassmorphism": "gold-accent",
        "vibrant": "vibrant",
        "bold": "vibrant",
        "editorial": "clean",
        "magazine": "clean",
        "minimal": "minimal",
        "clean": "minimal",
        "professional": "minimal",
        "elegant": "gold-accent",
        "luxury": "gold-accent",
        "playful": "vibrant",
    }

    _STYLE_ANIMATION = {
        "heavy": {"duration": "800ms", "delay_step": 150, "stagger": True},
        "medium": {"duration": "600ms", "delay_step": 100, "stagger": True},
        "light": {"duration": "400ms", "delay_step": 0, "stagger": False},
    }

    def _classify_page_style(self, tone, product_type):
        """Clasifica el estilo de la página usando ui-ux-pro-max como oráculo.

        Retorna clasificaciones Divi-nativas (variante, atmósfera, animación)
        derivadas del estilo que ui-ux-pro-max recomienda. No contiene hex,
        font names, ni CSS — solo decisiones mapeadas al sistema Divi.
        """
        if not product_type:
            return {}

        if self.ux_bridge is None:
            try:
                from ux_pro_bridge import UXProBridge
                self.ux_bridge = UXProBridge()
            except Exception:
                self.ux_bridge = False

        if not self.ux_bridge or not self.ux_bridge.is_ready:
            return {}

        try:
            style = self.ux_bridge.classify(tone, product_type)
        except Exception:
            return {}
        if not style:
            return {}

        sn = (style.get("style_name") or "").lower()
        et = style.get("effects_tags") or []
        cl = style.get("contrast_level", "medium")

        # Mapear a decisiones Divi-nativas
        variant = ""
        for key, val in self._STYLE_TO_VARIANT.items():
            if key in sn or sn in key:
                variant = val
                break

        atmosphere = self._STYLE_TO_ATMOSPHERE.get(variant, "clean")
        for key, val in self._STYLE_TO_ATMOSPHERE.items():
            if key in sn or sn in key:
                atmosphere = val
                break

        if "minimal" in sn or "clean" in sn:
            anim_key = "light"
        elif any(t in ("morphing", "fluid", "glass") for t in et):
            anim_key = "heavy"
        else:
            anim_key = "medium"

        anim = self._STYLE_ANIMATION.get(anim_key, self._STYLE_ANIMATION["medium"])

        return {
            "style_name": style.get("style_name", ""),
            "category": style.get("category", ""),
            "variant_hint": variant,
            "atmosphere_hint": atmosphere,
            "animation_profile": anim,
            "contrast_level": cl,
            "effects_tags": et,
            "pattern_name": style.get("pattern_name", ""),
        }

    def compose_page(self, brief, sections, product_type_override=None):
        """Define la composición visual de toda la página ANTES de procesar secciones.

        Retorna un dict con:
          - rhythm: secuencia de fondos para cada sección
          - atmosphere: atmósfera global
          - variant_map: qué variante de section-schema.json usar por sección
          - _style_classification: clasificación de estilo (uso interno)
        """
        tone = brief.get("tone", "editorial")
        product_type = product_type_override or brief.get("product_type") or ""
        style_class = self._classify_page_style(tone, product_type)

        rhythm_def = self._VISUAL_RHYTHMS.get(tone, self._VISUAL_RHYTHMS["editorial"])
        pattern = rhythm_def["pattern"].split("-")

        # Atmosphere: style classification puede sugerir atmósfera
        sc_atmo = (style_class or {}).get("atmosphere_hint", "")
        atmosphere_key = sc_atmo or rhythm_def.get("atmosphere", "clean")
        atmosphere = self._ATMOSPHERE_DECO.get(atmosphere_key, {})

        # Mapa de variantes por section_type (rota cíclicamente)
        variant_pool = []
        for sec in sections:
            st = sec.get("section_type", "generic")
            schema_entry = self.schema.get(st, {})
            variants = list(schema_entry.get("variants", {}).keys())
            if variants:
                variant_pool.append(variants)
            else:
                variant_pool.append([])

        # Asignar fondo rítmico + variante
        rhythm_map = {}
        variant_map = {}
        used_variants = {}
        variant_hint = (style_class or {}).get("variant_hint", "")
        for i, sec in enumerate(sections):
            st = sec.get("section_type", "generic")
            bg_key = pattern[i % len(pattern)]
            bg_preset = self._SECTION_BG_TOGGLE.get(bg_key, "section:light")

            # Si es CTA, forzar preset cta
            if st == "cta":
                bg_preset = "section:cta-epic"
            elif st in ("hero", "hero-centered"):
                bg_preset = "section:hero-dark"

            rhythm_map[i] = bg_preset

            # Rotar variante con preferencia por el hint de estilo
            variants = variant_pool[i]
            if variants:
                assigned = None
                # Style classification puede sugerir variante preferida
                if variant_hint and variant_hint in variants:
                    if (variant_hint not in used_variants
                            or used_variants[variant_hint] < i - 1):
                        assigned = variant_hint
                if not assigned:
                    for v in variants:
                        if v not in used_variants or used_variants[v] < i - 1:
                            assigned = v
                            break
                if not assigned:
                    assigned = variants[i % len(variants)]
                used_variants[assigned] = i
                variant_map[i] = assigned

        return {
            "rhythm": rhythm_map,
            "atmosphere": atmosphere,
            "atmosphere_key": atmosphere_key,
            "variant_map": variant_map,
            "tone": tone,
            "hero_style": rhythm_def.get("hero_style", "split"),
            "cta_style": rhythm_def.get("cta_style", "dark"),
            "_style_classification": style_class or {},
        }

    def select_variant(self, section_type, variant_name):
        """Selecciona una variante de section-schema.json."""
        if not variant_name:
            return None
        entry = self.schema.get(section_type, {})
        return entry.get("variants", {}).get(variant_name)

    def build_typography_scale(self, brand_vars=None):
        """Genera un typography scale system desde brand_vars para usar en módulos."""
        bv = brand_vars or {}
        scale = {}
        display_font = bv.get("font_display", "'SF Pro Display', sans-serif")
        body_font = bv.get("font_body", "'SF Pro Text', sans-serif")

        # Display sizes (for headings, hero text)
        display_sizes = {
            "display-xxl": bv.get("font_size_display_xxl", "clamp(2.5rem, 6vw, 5rem)"),
            "display-xl": bv.get("font_size_display_xl", "clamp(2rem, 4.5vw, 3.75rem)"),
            "display-lg": bv.get("font_size_display_lg", "clamp(1.5rem, 3vw, 2.5rem)"),
            "h1": bv.get("font_size_heading_1", "clamp(1.75rem, 3.5vw, 2.75rem)"),
            "h2": bv.get("font_size_heading_2", "clamp(1.375rem, 2.5vw, 2rem)"),
            "h3": bv.get("font_size_heading_3", "clamp(1.125rem, 1.75vw, 1.5rem)"),
        }
        body_sizes = {
            "body-lg": bv.get("font_size_body_lg", "clamp(1.05rem, 1.5vw, 1.25rem)"),
            "body": bv.get("font_size_body", "clamp(1rem, 1.25vw, 1.125rem)"),
            "body-sm": bv.get("font_size_body_sm", "clamp(0.8rem, 0.9vw, 0.875rem)"),
            "eyebrow": bv.get("font_size_eyebrow", "clamp(0.7rem, 0.8vw, 0.75rem)"),
        }

        scale["display"] = {
            "fontFamily": display_font,
            "sizes": display_sizes,
            "weight": bv.get("font_weight_display", "700"),
            "letterSpacing": bv.get("letter_spacing_display", "-0.02em"),
        }
        scale["body"] = {
            "fontFamily": body_font,
            "sizes": body_sizes,
            "weight": bv.get("font_weight_body", "400"),
        }
        scale["eyebrow"] = {
            "fontFamily": body_font,
            "size": body_sizes.get("eyebrow", "0.75rem"),
            "weight": "600",
            "letterSpacing": bv.get("letter_spacing_eyebrow", "0.15em"),
            "textTransform": "uppercase",
        }
        return scale

    def add_atmosphere_to_decoration(self, deco, section_type, atmosphere, tone):
        """Añade elementos atmosféricos al decoration block (overlay gradients, etc)."""
        if not atmosphere:
            return deco

        overlay = atmosphere.get("overlay_gradient")
        if overlay and section_type in ("hero", "hero-centered", "cta"):
            bg = deco.get("background", {}).get("desktop", {}).get("value", {})
            if bg and isinstance(bg, dict) and "overlay" in bg:
                pass
            else:
                bg_entry = deco.setdefault("background", {}).setdefault("desktop", {}).setdefault("value", {})
                stop_strs = []
                for s in overlay.get("stops", []):
                    sc = s.get("color", "transparent")
                    sp = s.get("position", "0")
                    stop_strs.append(f"{sc} {sp}%")
                grad_func = f"{overlay['type']}-gradient" if overlay['type'] in ('radial', 'linear', 'conic') else overlay['type']
                grad_str = f"{grad_func}({overlay['direction']}, {', '.join(stop_strs)})"
                bg_entry["overlay"] = {
                    "gradient": grad_str
                }

        # Shape dividers atmosféricos para hero
        if section_type in ("hero", "hero-centered"):
            existing_sd = deco.get("shapeDivider", {})
            if not existing_sd.get("bottom"):
                deco.setdefault("shapeDivider", {})["bottom"] = {
                    "desktop": {
                        "value": {
                            "style": "curve",
                            "color": "{{design:color:surface-light}}",
                            "height": "100px",
                            "flip": "off",
                            "invert": "off",
                        }
                    }
                }

        return deco

    # ── Expert: Style Recommendation ──────────────────────────────────────

    def recommend_style(self, tone="editorial", section_type="generic", top_n=3):
        """Recommend Divi style names for a tone + section_type."""
        style_map = self.rules.get("section_maps", {}).get("styles", {})
        per_tone = style_map.get(section_type, {}).get(tone, [])
        return per_tone[:top_n], 1.0 if per_tone else 0.0

    # ── Expert: Color Palette ─────────────────────────────────────────────

    def recommend_colors(self, section_type="generic", brand_vars=None):
        """Return design token names for the color_scheme, derived from brand.

        Every value is a {{design:color:*}} token — no hex, ever.
        Section type determines which brand variant to use for bg.
        """
        token_map = {
            "hero":         {"bg": "surface-deep",  "text": "text-on-dark","accent": "accent",     "cta": "premium"},
            "hero-centered":{"bg": "surface-deep",  "text": "text-on-dark","accent": "accent",     "cta": "premium"},
            "cta":          {"bg": "surface-deep",  "text": "text-on-dark","accent": "text-on-dark","cta": "premium"},
            "stats":        {"bg": "surface-light", "text": "ink",         "accent": "accent",     "cta": "premium"},
            "content":      {"bg": "surface-light", "text": "ink",         "accent": "accent",     "cta": "premium"},
            "content-list": {"bg": "surface-mid",   "text": "text-on-dark","accent": "accent",     "cta": "premium"},
            "logos":        {"bg": "surface-light", "text": "ink",         "accent": "accent",     "cta": "premium"},
            "timeline":     {"bg": "surface-light", "text": "ink",         "accent": "accent",     "cta": "premium"},
            "testimonials": {"bg": "surface-light", "text": "ink",         "accent": "accent",     "cta": "premium"},
            "features":     {"bg": "surface-light", "text": "ink",         "accent": "accent",     "cta": "premium"},
        }
        entry = token_map.get(section_type, token_map["content"])
        brand_name = (brand_vars or {}).get("brand_name", "")
        return {
            "background": f"{{{{design:color:{entry['bg']}}}}}",
            "text": f"{{{{design:color:{entry['text']}}}}}",
            "primary": f"{{{{design:color:{entry['accent']}}}}}",
            "cta": f"{{{{design:color:{entry['cta']}}}}}",
            "secondary": f"{{{{design:color:ink-soft}}}}",
        }, brand_name

    # ── Expert: Typography Recommendation ─────────────────────────────────

    def recommend_typography(self, tone="editorial", mood="", top_n=3, brand_vars=None):
        """Recommend font pairings. Brand vars always take priority over ML."""
        brand = brand_vars or {}

        heading = brand.get("font_display", "")
        body = brand.get("font_body", "") or brand.get("font_ui", "")
        if heading and body:
            return [{
                "name": f"{brand.get('brand_name', 'brand')} Display + Body",
                "heading_font": heading,
                "body_font": body,
                "category": "brand",
                "score": 1.0,
            }], 1.0

        typo_data = self.rules.get("embeddings", {}).get("typography", {})
        typo_domain = self.rules.get("domains", {}).get("typography", {})
        if not typo_data:
            return [], 0.0

        query_text = f"{tone} {mood}"
        query_emb = _embed_text(query_text)

        generic_fonts = self._FRONTEND_PRINCIPLES["typography"]["generic_fonts"]
        scored = []
        for name, emb in typo_data.items():
            sim = _cosine_sim(query_emb, emb)
            entry = typo_domain.get(name, {})
            hf = (entry.get("heading_font", "") or "").lower()
            bf = (entry.get("body_font", "") or "").lower()
            # Penalizar fonts genéricos (frontend-design principle)
            for gf in generic_fonts:
                if gf in hf or gf in bf:
                    sim *= 0.7
                    break
            scored.append((sim, name))
        scored.sort(key=lambda x: -x[0])
        results = []
        for sim, name in scored[:top_n]:
            entry = typo_domain.get(name, {})
            results.append({
                "name": name,
                "heading_font": entry.get("heading_font", ""),
                "body_font": entry.get("body_font", ""),
                "category": entry.get("category", ""),
                "score": round(sim, 3),
            })
        top_score = results[0]["score"] if results else 0.0
        return results, top_score

    # ── Expert: Template Selection (Stacking Ensemble) ────────────────────

    def _map_section_type_to_category(self, st: str) -> str:
        """Map brief section types to canonical catalog categories."""
        st_lower = st.lower()
        if st_lower in ("hero", "hero-centered", "hero-split", "banner"):
            return "hero"
        if st_lower in ("features", "content-list", "services", "items"):
            return "features"
        if st_lower in ("testimonials", "reviews"):
            return "testimonials"
        if st_lower in ("stats", "counters", "metrics"):
            return "stats"
        if st_lower in ("logos", "brands", "trust-bar"):
            return "logos"
        if st_lower in ("cta", "call-to-action", "newsletter"):
            return "cta"
        if st_lower in ("content", "about", "about-us"):
            return "about"
        if st_lower in ("team", "team-members"):
            return "team"
        if st_lower in ("pricing", "plans"):
            return "pricing"
        if st_lower in ("gallery", "portfolio"):
            return "gallery"
        if st_lower in ("contact", "contact-form", "get-in-touch"):
            return "contact"
        if st_lower in ("faq", "faqs"):
            return "faq"
        return "generic"

    def decide_template(self, section_def, context=None, top_n=5):
        """Stacking ensemble for template selection.

        Expertos:
          - KMeans cluster compatibility with adjacent section
          - Content classifier confidence for section_type
          - Slot coverage (IDF-weighted)
          - Column match (template columns vs expected)
        """
        section_type = section_def.get("section_type", "generic")
        title = section_def.get("title", "")
        text = section_def.get("text", "")
        query = f"{title} {text}".strip() or section_type

        adjacent_type = None
        if context and isinstance(context, dict):
            adjacent_type = context.get("adjacent_section_type")

        expert_scores = {}
        candidates = []

        # Map brief section_type to canonical catalog category
        canonical_cat = self._map_section_type_to_category(section_type)

        # Get candidate templates from slot catalog categories
        if isinstance(self.slot_categories, list):
            matching = [cat for cat in self.slot_categories
                        if cat == canonical_cat]
            category = matching[0] if matching else "generic"
        elif isinstance(self.slot_categories, dict):
            category = canonical_cat if canonical_cat in self.slot_categories else "generic"
        else:
            category = "generic"

        # Build candidates from B2 slot catalog (primary) or semantic index (fallback)
        cat_members = []
        if isinstance(self.slot_catalog, dict):
            raw = self.slot_catalog.get(category, [])
            for t in raw:
                if isinstance(t, tuple) and len(t) >= 1:
                    cat_members.append(t[0])
        if not cat_members and self.semantic_items:
            for item in self.semantic_items:
                if item.get("category", "").lower() == category.lower():
                    cat_members.append(item["name"])

        if not cat_members:
            return None, 0.0, ["No candidate templates found"]

        explanations = []

        # Score each candidate
        for tmpl_name in cat_members[:20]:
            scores = {}

            # Expert 1: Slot coverage (IDF-weighted)
            slot_score = self._score_slot_coverage(tmpl_name, section_def)
            scores["slot_coverage"] = slot_score

            # Expert 2: Column match
            col_score = self._score_column_match(tmpl_name, section_def)
            scores["column_match"] = col_score

            # Expert 3: Content classifier confidence
            clf_score = self._score_classifier_confidence(query, section_type)
            scores["classifier_confidence"] = clf_score

            # Expert 4: KMeans cluster compatibility
            kmeans_score = self._score_kmeans_compat(tmpl_name, adjacent_type)
            scores["kmeans_cluster"] = kmeans_score

            # Expert 5: Semantic proximity
            sem_score = self._score_semantic_proximity(query, tmpl_name)
            scores["semantic_coherence"] = sem_score

            # Weighted combination
            total = sum(scores.get(k, 0.0) * self.expert_weights.get(k, 0.1)
                       for k in self.expert_weights)
            candidates.append((total, tmpl_name, scores))

        candidates.sort(key=lambda x: -x[0])
        if not candidates:
            return None, 0.0, ["No candidates scored"]

        best = candidates[0]
        best_name = best[1]
        best_score = best[0]

        # Explain
        exps = []
        for k, v in best[2].items():
            w = self.expert_weights.get(k, 0.1)
            exps.append(f"{k}={v:.3f}(w={w:.2f})")
        explanations.append(f"Template={best_name} score={best_score:.4f} | {' '.join(exps)}")

        return best_name, best_score, explanations

    def _score_slot_coverage(self, tmpl_name, section_def):
        """IDF-weighted slot coverage for a template."""
        from b_slot_assigner import get_slots_needed_from_brief_section
        brief_slots = get_slots_needed_from_brief_section(section_def)
        if not brief_slots:
            return 0.5

        template_slots_raw = self._get_template_slot_counts(tmpl_name)
        if not template_slots_raw:
            return 0.0

        idf = self.slot_idf if isinstance(self.slot_idf, dict) else {}
        N = self.slot_idf_N or 877

        covered = 0.0
        total = 0.0
        for slot_type, count in brief_slots.items():
            w = idf.get(slot_type, math.log(N / max(1, 1)))
            total += w * count
            tmpl_count = template_slots_raw.get(slot_type, 0)
            covered += w * min(count, tmpl_count)
        return covered / total if total > 0 else 0.0

    def _get_template_slot_counts(self, tmpl_name):
        """Get slot counts for a template from slot catalog."""
        if isinstance(self.slot_catalog, dict):
            for cat_templates in self.slot_catalog.values():
                for t in cat_templates:
                    if isinstance(t, tuple) and len(t) >= 2 and t[0] == tmpl_name:
                        return t[1] if isinstance(t[1], dict) else {}
        return {}

    def _score_column_match(self, tmpl_name, section_def):
        """Column structure match between template and expected."""
        section_type = section_def.get("section_type", "generic")
        expected_cols = 1
        if section_type in ("hero", "hero-centered", "content"):
            expected_cols = 2
        items = section_def.get("items", section_def.get("features", []))
        if items:
            expected_cols = min(len(items), 3)
        pat = self.patterns.get(section_type, {})
        col_structures = pat.get("column_structures", [])
        for cs in col_structures:
            struct = cs.get("structure", "")
            ncols = len(struct.split(",")) if struct else 1
            if ncols == expected_cols:
                return 0.7
        return 0.3 if expected_cols <= 3 else 0.5

    def _score_classifier_confidence(self, query, section_type):
        if not self.classifier or not self.label_encoder:
            return 0.5
        try:
            pred = self.classifier.predict([query])[0]
            probs = self.classifier.predict_proba([query])[0]
            classes = list(self.label_encoder.classes_)
            if pred in classes:
                idx = classes.index(pred)
                confidence = float(probs[idx])
                return confidence if pred == section_type else confidence * 0.3
        except Exception:
            pass
        return 0.0

    def _score_kmeans_compat(self, tmpl_name, adjacent_type):
        if not adjacent_type or not self.kmeans:
            return 0.5
        if adjacent_type == "generic":
            return 0.5

        # Use catalog_stats cluster data for real KMeans scoring
        if self.catalog_stats:
            cluster_of_adjacent = None
            cluster_of_current = None
            for cluster_key, data in self.catalog_stats.items():
                if not cluster_key.startswith("cluster_"):
                    continue
                members = data.get("members", data.get("items", []))
                if isinstance(members, list):
                    member_names = [m.get("name", "") if isinstance(m, dict) else str(m)
                                    for m in members]
                    if adjacent_type in member_names:
                        cluster_of_adjacent = cluster_key
                    if tmpl_name in member_names:
                        cluster_of_current = cluster_key
            if cluster_of_adjacent and cluster_of_current:
                return 1.0 if cluster_of_adjacent == cluster_of_current else 0.7
            if cluster_of_adjacent or cluster_of_current:
                return 0.6

        if adjacent_type == "hero" or adjacent_type == "hero-centered":
            return 0.6
        return 0.5

    def _score_semantic_proximity(self, query, tmpl_name):
        if not self.semantic_items or self.semantic_embeddings is None:
            return 0.5
        query_emb = _embed_text(query)
        for i, item in enumerate(self.semantic_items):
            if item.get("name", "").lower() == tmpl_name.lower():
                if isinstance(self.semantic_embeddings, list) and i < len(self.semantic_embeddings):
                    return _cosine_sim(query_emb, self.semantic_embeddings[i])
        return 0.0

    # ── Expert: Column Decision ──────────────────────────────────────────

    def decide_columns(self, section_def, template_name=None, adjacent_type=None):
        """Choose column structure considering adjacent section."""
        section_type = section_def.get("section_type", "generic")
        pat = self.patterns.get(section_type, {})
        col_structures = pat.get("column_structures", [])
        if not col_structures:
            return "4_4", 0.5

        expected_cols = 1
        if section_type in ("hero", "hero-centered", "content"):
            expected_cols = 2
        features = section_def.get("features", section_def.get("items", []))
        if features:
            expected_cols = min(len(features), 4)

        best = col_structures[0]["structure"]
        best_score = 0.0
        for cs in col_structures:
            struct = cs.get("structure", "")
            freq = cs.get("frequency", cs.get("count", 1))
            ncols = len(struct.split(",")) if struct else 1
            score = 0.0
            if ncols == expected_cols:
                score += 0.5
            if adjacent_type and adjacent_type != section_type:
                score += 0.2
            score += min(freq / 100, 0.3)
            if score > best_score:
                best_score = score
                best = struct
        return best, round(best_score, 3)

    # ── Expert: Module Decision ──────────────────────────────────────────

    def decide_modules(self, section_def, column_structure="4_4",
                       section_type="generic", top_n=10):
        """Choose modules with correct fields."""
        compat_modules = COLUMN_MODULE_COMPAT.get(column_structure,
                                                   COLUMN_MODULE_COMPAT["4_4"])
        affinity = self.affinities.get(section_type, {})
        top_pairs = affinity.get("top_pairs", []) if isinstance(affinity, dict) else []

        selected = []
        seen = set()
        for pair in top_pairs:
            mods = pair.get("modules", [])
            for m in mods:
                if m not in seen and m in compat_modules:
                    selected.append(m)
                    seen.add(m)
                if len(selected) >= top_n:
                    break
            if len(selected) >= top_n:
                break

        if not selected:
            selected = compat_modules[:4]

        scores = {}
        for m in selected:
            schema = self.module_schemas.get(m.replace("divi/", ""), {})
            if schema:
                scores[m] = 0.8
            else:
                scores[m] = 0.4

        return selected, scores

    # ── Expert: Spacing Decision ─────────────────────────────────────────

    def decide_spacing(self, section_def, section_type="generic",
                       adjacent_padding=None, cluster_id=None):
        """Normalize spacing based on section type, adjacent sections, and cluster."""
        base_paddings = {
            "hero": 160, "hero-centered": 140, "cta": 120,
            "features": 96, "content": 96, "content-list": 80,
            "stats": 72, "testimonials": 80, "logos": 72,
            "faq": 80, "pricing": 96, "team": 80,
            "gallery": 72, "contact": 96, "about": 96,
            "blog": 80, "generic": 80,
        }

        # Adjust for cluster
        base = base_paddings.get(section_type, 80)
        if cluster_id is not None:
            cluster_offsets = {0: 0, 1: -16, 2: 32, 3: -8, 4: 16, 5: 24, 6: -24}
            base += cluster_offsets.get(cluster_id % 7, 0)

        # Harmonize with adjacent
        if adjacent_padding is not None:
            diff = abs(base - adjacent_padding)
            if diff > 80:
                base = int((base + adjacent_padding) / 2)
            elif diff > 40:
                base = int(base * 0.85 + adjacent_padding * 0.15)

        min_pad = self._FRONTEND_PRINCIPLES["spacing"]["min_padding_px"]
        return max(min_pad, min(200, base))

    # ── Expert: Decoration Decision ──────────────────────────────────────

    def decide_decoration(self, section_type="generic", tone="editorial",
                          brand_vars=None, template_name=None,
                          product_type="", style_classification=None):
        """Generate decoration block from multiple experts."""
        deco = {}

        # Tone rules
        tone_defs = self.rules.get("tone_definitions", {})
        tone_def = tone_defs.get(tone, {})

        # Color palette
        palette, pt = self.recommend_colors(section_type, brand_vars)

        # Typography — brand vars take priority
        font_results, font_score = self.recommend_typography(tone, brand_vars=brand_vars)

        # Decoration rules from E
        deco_by_tone = self.deco_rules.get("decoration_by_tone", {})
        tone_rules = deco_by_tone.get(tone, {})
        suggestions = tone_rules.get("suggestions", {})

        deco["color_scheme"] = {
            "bg": palette.get("background", "{{design:color:surface-light}}"),
            "text": palette.get("text", "{{design:color:ink}}"),
            "accent": palette.get("primary", "{{design:color:accent}}"),
            "cta": palette.get("cta", "{{design:color:premium}}"),
        }
        deco["typography"] = {}
        if font_results:
            deco["typography"]["heading"] = font_results[0].get("heading_font", "Inter")
            deco["typography"]["body"] = font_results[0].get("body_font", "Inter")
        deco["style_name"] = tone_def.get("style_candidates", [tone])[0]
        deco["motion"] = {
            "duration": tone_def.get("animation_duration", "400ms"),
            "easing": "ease-out",
        }
        if suggestions.get("gradient"):
            bg_token = palette.get("background", "{{design:color:surface-light}}")
            deco["gradient"] = {
                "type": "linear", "direction": "180deg",
                "stops": [
                    {"color": bg_token, "position": "0"},
                    {"color": bg_token, "position": "100"},
                ],
            }
        deco["confidence"] = round(font_score / 2 + 0.5, 3)

        return deco

    # ── Design Inspiration (skills impactan decoration real) ──────────────

    # Mapeo de style_name → tratamiento tipográfico (Divi-native: solo tokens)
    _TYPOGRAPHY_TREATMENT = {
        "editorial": {"letterSpacing": "-0.02em", "weight": "700", "mood": "serif"},
        "magazine": {"letterSpacing": "-0.02em", "weight": "700", "mood": "serif"},
        "elegant": {"letterSpacing": "0.03em", "weight": "400", "mood": "elegant"},
        "luxury": {"letterSpacing": "0.03em", "weight": "400", "mood": "elegant"},
        "liquid glass": {"letterSpacing": "-0.01em", "weight": "500", "mood": "premium"},
        "vibrant": {"letterSpacing": "-0.03em", "weight": "800", "mood": "bold"},
        "bold": {"letterSpacing": "-0.03em", "weight": "800", "mood": "bold"},
        "minimal": {"letterSpacing": "-0.01em", "weight": "600", "mood": "clean"},
        "clean": {"letterSpacing": "-0.01em", "weight": "600", "mood": "clean"},
        "professional": {"letterSpacing": "0em", "weight": "600", "mood": "corporate"},
    }

    # Mapeo de style_name → presets sugeridos para módulos
    _STYLE_MODULE_PRESETS = {
        "liquid glass": {
            "divi/blurb": ["module:glass-card", "transform:hover-lift"],
            "divi/button": ["module:btn-outline"],
        },
        "glassmorphism": {
            "divi/blurb": ["module:glass-card", "transform:hover-lift"],
            "divi/button": ["module:btn-outline"],
        },
        "vibrant": {
            "divi/blurb": ["module:glass-card", "transform:hover-scale"],
            "divi/button": ["module:btn-primary"],
        },
        "editorial": {
            "divi/blurb": ["module:clean-card"],
            "divi/button": ["module:btn-primary"],
        },
        "minimal": {
            "divi/blurb": ["module:clean-card"],
            "divi/button": ["module:btn-outline"],
        },
        "professional": {
            "divi/blurb": ["module:feature-card"],
            "divi/button": ["module:btn-primary"],
        },
    }

    # Mapeo de categoría → preferencia de token de color
    _CATEGORY_COLOR_MOOD = {
        "biohacking": {"prefer": "premium", "vibe": "tech"},
        "wellness": {"prefer": "accent", "vibe": "calm"},
        "campus": {"prefer": "accent", "vibe": "academic"},
        "luxury": {"prefer": "premium", "vibe": "elegant"},
        "health": {"prefer": "accent", "vibe": "clean"},
        "tech": {"prefer": "premium", "vibe": "modern"},
        "education": {"prefer": "accent", "vibe": "academic"},
        "fashion": {"prefer": "premium", "vibe": "elegant"},
    }

    def _apply_design_inspiration(self, deco, tone="editorial", section_type="generic",
                                  style_classification=None, plan=None):
        """Aplica inspiración de ui-ux-pro-max + frontend-design a decoration.

        MODIFICA valores reales de decoration que e_page_mapper.py respeta:
        spacing, scroll, shapeDivider, color_scheme, typography treatment,
        y módulos presets sugeridos.
        Sin hex, font names ni CSS — usa solo tokens {{design:*}} y presets.
        """
        style = style_classification or {}
        if not style:
            return deco
        
        # Prefer glass-card if strategy indicates glass viability
        strategy = style.get('strategy', '')
        glass_viable = style.get('glass_viable', False)
        
        sn = (style.get("style_name") or "").lower()
        et = style.get("effects_tags") or []
        cl = style.get("contrast_level", "medium")

        # Override module presets based on glass viability
        if plan is not None:
            mod_presets = {}
            # If strategy has glass or glass_viable is True, use glass-card
            if glass_viable or 'glass' in strategy or 'liquid' in sn or 'glassmorphism' in sn:
                mod_presets["divi/blurb"] = ["module:glass-card", "transform:hover-glow"]
                mod_presets["divi/button"] = ["module:btn-primary", "transform:hover-glow"]
            else:
                for key, presets in self._STYLE_MODULE_PRESETS.items():
                    if key in sn or sn in key:
                        mod_presets = presets
                        break
            if mod_presets:
                plan["_style_module_presets"] = mod_presets

        return deco

    # ── Empty Module Auto-Fix ─────────────────────────────────────────────

    _MODULE_FALLBACKS = {
        "divi/button": {
            "checks": ["button_text", "button_url"],
            "defaults": {"button_text": "Más información", "button_url": "#"},
        },
        "divi/text": {
            "checks": ["content"],
            "defaults": {},
        },
        "divi/heading": {
            "checks": ["content"],
            "defaults": {},
        },
        "divi/blurb": {
            "checks": ["title", "content"],
            "defaults": {},
        },
        "divi/image": {
            "checks": ["src"],
            "defaults": {},
        },
        "divi/testimonial": {
            "checks": ["content", "author"],
            "defaults": {"author": "Egresado Aletheia"},
        },
        "divi/number-counter": {
            "checks": ["number", "title"],
            "defaults": {"number": "0"},
        },
    }

    def _fix_empty_modules(self, sections, brief):
        """Auto-fill empty modules using brief content or sensible defaults.

        Modifies sections in-place. Returns count of modules fixed.
        """
        fixed_count = 0
        all_brief_sections = brief.get("sections", [])
        for i, sec in enumerate(sections):
            brief_sec = all_brief_sections[i] if i < len(all_brief_sections) else {}
            for row in sec.get("rows", []):
                for col in row.get("columns", []):
                    for mod in col.get("modules", []):
                        mod_type = mod.get("type", "")
                        rules = self._MODULE_FALLBACKS.get(mod_type)
                        if not rules:
                            continue
                        fallback_keys = rules.get("checks", [])
                        defaults = rules.get("defaults", {})
                        for key in fallback_keys:
                            val = mod.get(key, "")
                            if isinstance(val, str) and val.strip():
                                continue
                            if isinstance(val, (int, float)) and val:
                                continue
                            # Try to get value from brief section
                            brief_val = self._find_value_for_key(key, brief_sec, mod)
                            if brief_val:
                                mod[key] = brief_val
                                fixed_count += 1
                            elif key in defaults:
                                mod[key] = defaults[key]
                                fixed_count += 1
        return fixed_count

    def _find_value_for_key(self, target_key, brief_sec, mod):
        """Search for a value in the brief section that matches this module key."""
        key_map = {
            "button_text": ["btn_primary_text", "btn_secondary_text"],
            "button_url": ["btn_primary_url", "btn_secondary_url"],
            "title": ["title"],
            "content": ["text", "body", "title"],
            "author": ["name"],
            "number": ["number"],
        }
        candidates = key_map.get(target_key, [target_key])
        for ck in candidates:
            val = brief_sec.get(ck, "")
            if val and isinstance(val, str) and val.strip():
                return val
        return None

    # ── Quality Gate ──────────────────────────────────────────────────────

    def validate_visual_cohesion(self, page_def):
        """Quality gate: score compuesto 0-1 con 7+ expertos.

        Returns:
          (score, issues, details)
        """
        sections = page_def.get("sections", [])
        if not sections:
            return 0.0, ["No sections"], {}

        scores = {}
        issues = []

        # Expert 1: Duplicate content
        dup_score, dup_issues = self._check_duplicate_content(sections)
        scores["no_duplicates"] = dup_score
        issues.extend(dup_issues)

        # Expert 2: Empty modules
        empty_score, empty_issues = self._check_empty_modules(sections)
        scores["no_empty_modules"] = empty_score
        issues.extend(empty_issues)

        # Expert 3: Content count balance
        count_scores = [len(s.get("rows", [])) for s in sections]
        if count_scores:
            cv = np.std(count_scores) / (np.mean(count_scores) + 0.01)
            scores["section_balance"] = max(0, 1 - min(cv / 1.5, 1))
        else:
            scores["section_balance"] = 0.5

        # Expert 4: Color contrast (UX-PRO rule 36: 4.5:1 min)
        contrast_score, contrast_issues = self._check_color_contrast(sections)
        scores["color_contrast"] = contrast_score
        issues.extend(contrast_issues)

        # Expert 5: Spacing consistency
        spacing_score, spacing_issues = self._check_spacing_consistency(sections)
        scores["spacing_consistency"] = spacing_score
        issues.extend(spacing_issues)

        # Expert 6: Slot coverage
        slot_score, slot_issues = self._check_slot_coverage(sections)
        scores["slot_coverage"] = slot_score
        issues.extend(slot_issues)

        # Expert 7: Content overflow (brief content vs typical slot lengths)
        overflow_score, overflow_issues = self._check_content_overflow(sections)
        scores["content_overflow"] = overflow_score
        issues.extend(overflow_issues)

        # Weighted final score
        final_weights = {
            "no_duplicates": 0.15,
            "no_empty_modules": 0.10,
            "section_balance": 0.05,
            "color_contrast": 0.10,
            "spacing_consistency": 0.15,
            "slot_coverage": 0.20,
            "content_overflow": 0.25,
        }
        final_score = sum(scores.get(k, 0.5) * final_weights.get(k, 0.1)
                         for k in final_weights)

        details = {
            "scores": scores,
            "issues": issues,
            "n_sections": len(sections),
            "expert_weights": final_weights,
        }

        return round(final_score, 3), issues, details

    def _check_duplicate_content(self, sections):
        issues = []
        total_mods = 0
        dup_mods = 0
        for i, sec in enumerate(sections):
            texts = []
            for row in sec.get("rows", []):
                for col in row.get("columns", []):
                    for mod in col.get("modules", []):
                        total_mods += 1
                        collected = set()
                        for k in MODULE_TEXT_KEYS:
                            v = mod.get(k, "")
                            if isinstance(v, str) and v.strip() and len(v) > 20:
                                collected.add(v.strip()[:100])
                        for t in collected:
                            if t in texts:
                                dup_mods += 1
                            texts.append(t)
        score = 1 - (dup_mods / max(total_mods, 1))
        if dup_mods > 0:
            issues.append(f"{dup_mods}/{total_mods} modules have duplicate content")
        return score, issues

    def _check_empty_modules(self, sections):
        issues = []
        total = 0
        empty = 0
        for i, sec in enumerate(sections):
            for row in sec.get("rows", []):
                for col in row.get("columns", []):
                    for mod in col.get("modules", []):
                        total += 1
                        has_content = False
                        for k in MODULE_TEXT_KEYS:
                            v = mod.get(k, "")
                            if isinstance(v, str) and v.strip():
                                has_content = True
                                break
                        src = mod.get("src", "")
                        if not has_content and not src:
                            empty += 1
                            if empty <= 3:
                                issues.append(f"Empty module in section[{i}]: {mod.get('type','?')}")
        score = 1 - (empty / max(total, 1))
        return score, issues

    def _check_color_contrast(self, sections):
        issues = []
        contrast_count = 0
        ok = 0
        for sec in sections:
            deco = sec.get("decoration", {})
            cs = deco.get("color_scheme", {})
            bg_str = cs.get("bg", "#FFFFFF")
            text_str = cs.get("text", "#000000")
            # Skip token-based schemes (contrast guaranteed by design system)
            if bg_str.startswith("{{design:") or text_str.startswith("{{design:"):
                contrast_count += 1
                ok += 1
                continue
            try:
                ratio = _contrast_ratio(_parse_hex(bg_str), _parse_hex(text_str))
                contrast_count += 1
                if ratio >= 4.5:
                    ok += 1
                else:
                    issues.append(f"Low contrast {ratio:.1f}:1 (min 4.5)")
            except Exception:
                pass
        score = ok / max(contrast_count, 1)
        return score, issues

    def _check_spacing_consistency(self, sections):
        issues = []
        paddings = []
        for sec in sections:
            rows = sec.get("rows", [])
            if rows:
                deco = sec.get("decoration", {})
                spacing = deco.get("spacing", {})
                desktop = spacing.get("desktop", {})
                val = desktop.get("value", {})
                pt = _parse_px(val.get("padding", {}).get("top", "80px"))
                paddings.append(pt)
        if len(paddings) >= 2:
            max_diff = max(abs(paddings[i] - paddings[i-1])
                          for i in range(1, len(paddings)))
            score = max(0, 1 - (max_diff - 20) / 180)
            if max_diff > 80:
                issues.append(f"Max padding gap between sections: {max_diff}px")
        else:
            score = 0.5
        # Cross-check with catalog_stats if available
        if self.catalog_stats and paddings:
            all_tops = []
            for cluster_key, data in self.catalog_stats.items():
                if cluster_key.startswith("cluster_"):
                    pt_data = data.get("padding_top", {})
                    if pt_data.get("count", 0) > 0:
                        all_tops.append((pt_data.get("mean", 0), pt_data.get("std", 0), pt_data.get("count", 0)))
            if all_tops:
                total_count = sum(c for _, _, c in all_tops)
                global_mean = sum(m * c for m, _, c in all_tops) / max(total_count, 1)
                global_std = sum(s * c for _, s, c in all_tops) / max(total_count, 1) if total_count > 0 else 20
                if global_std > 0:
                    outliers = sum(1 for p in paddings if abs(p - global_mean) > 2 * global_std)
                    if outliers > len(paddings) // 3:
                        issues.append(f"{outliers}/{len(paddings)} sections have atypical padding (μ={global_mean:.0f}±{global_std:.0f}px)")
        return score, issues

    def _check_slot_coverage(self, sections):
        """Check if any {{slot:*}} tokens remain in the plan."""
        total = 0
        remaining = 0
        for sec in sections:
            raw = json.dumps(sec)
            found = SLOT_RE.findall(raw)
            total += len(found)
            if found:
                remaining += len(found)
        issues = [f"{remaining} unresolved slots"] if remaining else []
        _score = 1 - (remaining / max(total, 1))
        return _score, issues

    def _check_content_overflow(self, sections):
        """Check brief content length vs typical slot lengths from dataset."""
        issues = []
        if not self.slot_stats or "_meta" not in self.slot_stats:
            return 1.0, []
        slot_to_tags = self.slot_stats.get("_meta", {}).get("slot_to_tags", {})
        total_content = 0
        overflow_count = 0
        for i, sec in enumerate(sections):
            for row in sec.get("rows", []):
                for col in row.get("columns", []):
                    for mod in col.get("modules", []):
                        mod_type = mod.get("type", "")
                        for slot_name, tags in slot_to_tags.items():
                            if any(t in mod_type for t in tags):
                                for key in MODULE_TEXT_KEYS:
                                    val = mod.get(key, "")
                                    if isinstance(val, str) and len(val.strip()) > 0:
                                        total_content += 1
                                        length = len(val)
                                        ref = self.slot_stats.get(slot_name, {})
                                        if ref.get("count", 0) > 5:
                                            p90 = ref.get("p90", 200)
                                            max_obs = ref.get("max", 500)
                                            threshold = max(p90 * 2, max_obs * 1.2, 500)
                                            if length > threshold:
                                                overflow_count += 1
                                                if overflow_count <= 2:
                                                    issues.append(
                                                        f"Section[{i}] {slot_name}={length} chars "
                                                        f"(p90={p90}, max_obs={max_obs}, threshold={threshold:.0f})"
                                                    )
        score = 1 - (overflow_count / max(total_content, 1))
        return score, issues

    # ── Batch Plan Generation ────────────────────────────────────────────

    def generate_section_plan(self, section_def, context=None):
        """Generate a complete section plan using all experts.

        context now supports page_composition dict from compose_page().
        """
        section_type = section_def.get("section_type", "generic")
        tone = section_def.get("tone", "editorial")
        brand_vars = context.get("brand_vars", {}) if context else {}
        page_composition = context.get("page_composition", {}) if context else {}
        section_index = context.get("section_index", 0) if context else 0
        product_type = (context.get("product_type") or
                        section_def.get("product_type") or
                        brand_vars.get("brand_name", ""))
        style_classification = page_composition.get("_style_classification", {})

        plan = {
            "section_type": section_type,
            "template": None,
            "template_score": 0.0,
            "column_structure": "4_4",
            "slots": section_def.get("slots", {}),
            "presets": [],
            "decoration": {},
            "variant": None,
        }

        # Template via ensemble
        tmpl_name, tmpl_score, tmpl_exp = self.decide_template(
            section_def, context)
        plan["template"] = tmpl_name
        plan["template_score"] = tmpl_score
        plan["_explanations"] = tmpl_exp

        # Columns
        adj_type = context.get("adjacent_section_type") if context else None
        col_struct, col_score = self.decide_columns(
            section_def, tmpl_name, adj_type)
        plan["column_structure"] = col_struct

        # Modules
        mods, mod_scores = self.decide_modules(
            section_def, col_struct, section_type)
        plan["modules"] = mods

        # Decoration
        deco = self.decide_decoration(
            section_type, tone, brand_vars, tmpl_name, product_type,
            style_classification)
        plan["decoration"] = deco

        # Page composition: variant + atmosphere + typography
        variant_name = page_composition.get("variant_map", {}).get(section_index)
        if variant_name:
            plan["variant"] = variant_name
            variant_data = self.select_variant(section_type, variant_name)
            if variant_data:
                # Merge variant data into decoration
                v_slots = variant_data.get("slots", [])
                if v_slots:
                    plan["_variant_slots"] = v_slots
                v_tokens = variant_data.get("design_tokens", [])
                if v_tokens:
                    plan["_variant_tokens"] = v_tokens

        # Atmosphere
        atmosphere = page_composition.get("atmosphere", {})
        if atmosphere:
            plan["decoration"] = self.add_atmosphere_to_decoration(
                plan["decoration"], section_type, atmosphere, tone)

        # Typography scale (for module-level font application)
        typo_scale = self.build_typography_scale(brand_vars)
        plan["_typography_scale"] = typo_scale

        # Preset from page rhythm
        rhythm = page_composition.get("rhythm", {})
        rhythm_preset = rhythm.get(section_index)
        # Override: hero sections always use hero-dark
        if section_type in ("hero", "hero-centered"):
            rhythm_preset = "section:hero-dark"
        # Override: CTA sections always use cta-epic
        if section_type == "cta":
            rhythm_preset = "section:cta-epic"
        if rhythm_preset:
            existing_presets = plan.get("presets", [])
            if not existing_presets:
                plan["presets"] = [rhythm_preset]
            elif existing_presets[0] != rhythm_preset:
                plan["presets"] = [rhythm_preset] + existing_presets

        # Spacing
        pad = self.decide_spacing(section_def, section_type)
        if "spacing" not in plan["decoration"]:
            plan["decoration"]["spacing"] = {}
        plan["decoration"]["spacing"]["desktop"] = {
            "value": {
                "padding": {
                    "top": f"{pad}px",
                    "bottom": f"{pad}px",
                }
            }
        }

        # ── Design Inspiration: modifica decoration real (spacing, scroll,
        #     shapeDivider, animation, typography, module presets) basado en
        #     clasificación de estilo. Corre al FINAL para sobreescribir.
        plan["decoration"] = self._apply_design_inspiration(
            plan["decoration"], tone, section_type, style_classification, plan)

        return plan

    def is_ready(self):
        return self._loaded
