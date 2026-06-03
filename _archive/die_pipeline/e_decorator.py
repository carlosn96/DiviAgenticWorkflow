#!/usr/bin/env python3
"""
e_decorator.py — Artifact E: Decoration Engine

Genera inteligencia de decoración visual para el DIE.
Dos modos de operación:

1. Standalone (build):
     python e_decorator.py --build
   → Parse dataset.jsonl, extraer decoration attributes, K-means clustering,
     mapear CSVs de ui-ux-pro-max, producir decoration-clusters.pkl + decoration-rules.json

2. Módulo importable:
     from e_decorator import DecorationEngine
     deco = DecorationEngine()
     blocks = deco.get_decoration(section_type="hero", tone="editorial", ...)

Fuentes de datos:
  - dataset.jsonl (877 templates Divi 4, decoration real)
  - ui-ux-pro-max/data/colors.csv (97 paletas curadas)
  - ui-ux-pro-max/data/styles.csv (~35 estilos con atributos CSS)
  - ui-ux-pro-max/data/typography.csv (57 font pairings)
  - ui-ux-pro-max/data/ux-guidelines.csv (100 reglas UX)
"""

import json
import os
import re
import sys
import pickle
import math
from pathlib import Path
from collections import Counter, defaultdict
from html import unescape
import csv
import io

import numpy as np

DAW_ROOT = Path(__file__).resolve().parent.parent.parent
UIUX_DIR = DAW_ROOT / "ui-ux-pro-max" / "data"
DATASET_PATH = DAW_ROOT / "ml-dataset" / "dataset.jsonl"
OUTPUT_DIR = Path(__file__).resolve().parent

# Regex para parsear shortcodes Divi 4
SHORTCODE_RE = re.compile(r'\[(\w+)([^\]]*)\](.*?)\[\/\1\]', re.DOTALL)
SELFCLOSING_RE = re.compile(r'\[(\w+)([^\]]*?)/\]')
ATTR_RE = re.compile(r'(\w+)\s*=\s*("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'|(?:[^\s"\']+))')


# ─── 1. PARSER DE SHORTCODES DIVI 4 ─────────────────────────────────


def parse_shortcode_attr_value(value):
    if value.startswith('"') and value.endswith('"'):
        value = value[1:-1]
    if value.startswith("'") and value.endswith("'"):
        value = value[1:-1]
    return unescape(value)


def parse_attrs(attr_str):
    attrs = {}
    for match in ATTR_RE.finditer(attr_str):
        key = match.group(1)
        val = parse_shortcode_attr_value(match.group(2))
        attrs[key] = val
    return attrs


def extract_decoration(shortcode_text):
    """
    Extrae decoration attributes de shortcodes Divi 4.
    Retorna dict con atributos numéricos/categóricos de decoración.
    """
    deco = {
        # Gradients
        "has_gradient": 0,
        "gradient_stops": 0,
        "gradient_is_linear": 0,
        "gradient_is_radial": 0,
        "gradient_deg": 0.0,
        # Background
        "has_bg_image": 0,
        "has_bg_color": 0,
        "bg_color": None,
        "bg_is_dark": 0,
        # Box shadow
        "has_shadow": 0,
        "shadow_style": "none",
        "shadow_blur": 0.0,
        "shadow_spread": 0.0,
        "shadow_vertical": 0.0,
        # Border
        "has_border_radius": 0,
        "border_radius": 0.0,
        # Animation
        "has_animation": 0,
        "anim_style": "none",
        "anim_is_fade": 0,
        "anim_is_slide": 0,
        "anim_is_zoom": 0,
        "anim_is_flip": 0,
        "anim_duration_ms": 0.0,
        "anim_delay_ms": 0.0,
        # Hover
        "has_hover": 0,
        "hover_is_scale": 0,
        "hover_scale_pct": 0.0,
        "hover_is_translate": 0,
        "hover_is_rotate": 0,
        # Scroll
        "has_scroll": 0,
        "scroll_is_vertical": 0,
        "scroll_is_horizontal": 0,
        "scroll_is_opacity": 0,
        # Dividers
        "has_divider_top": 0,
        "has_divider_bottom": 0,
        "divider_style": "none",
        # Mask
        "has_mask": 0,
        "mask_style": "none",
        # Parallax
        "is_parallax": 0,
        # Layout
        "module_count": 0,
        "row_count": 0,
        "section_count": 0,
        "column_count": 0,
        # Third party
        "has_dipl_modules": 0,
    }

    ILLUMINANTS = [
        (0, 0, 0), (36, 36, 36), (66, 66, 66),
        (15, 23, 42), (26, 24, 20),
    ]

    def _is_dark(hex_color):
        if not hex_color or hex_color in ("rgba(0,0,0,0)", "transparent", ""):
            return None
        hex_color = hex_color.strip().lower()
        if hex_color.startswith("rgba"):
            match = re.search(r'rgba\((\d+),\s*(\d+),\s*(\d+)', hex_color)
            if match:
                r, g, b = int(match.group(1)), int(match.group(2)), int(match.group(3))
                lum = 0.299 * r + 0.587 * g + 0.114 * b
                return lum < 128
            return None
        if hex_color.startswith("rgb"):
            match = re.search(r'rgb\((\d+),\s*(\d+),\s*(\d+)', hex_color)
            if match:
                r, g, b = int(match.group(1)), int(match.group(2)), int(match.group(3))
                lum = 0.299 * r + 0.587 * g + 0.114 * b
                return lum < 128
            return None
        hex_color = hex_color.lstrip("#")
        if len(hex_color) == 6:
            try:
                r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
                lum = 0.299 * r + 0.587 * g + 0.114 * b
                return lum < 128
            except ValueError:
                return None
        return None

    def parse_section_attrs(attrs):
        # Gradient
        if attrs.get("use_background_color_gradient") == "on" or attrs.get("background_color_gradient_stops", ""):
            deco["has_gradient"] = 1
            stops_raw = attrs.get("background_color_gradient_stops", "")
            if stops_raw:
                deco["gradient_stops"] = stops_raw.count("|") + 1 if "|" in stops_raw else stops_raw.count("% ") + 1 if "%" in stops_raw else 2
            direction = attrs.get("background_color_gradient_direction", "")
            if "deg" in direction:
                try:
                    deco["gradient_deg"] = float(direction.replace("deg", "").strip())
                except ValueError:
                    deco["gradient_deg"] = 0.0
                deco["gradient_is_linear"] = 1
            else:
                deco["gradient_is_radial"] = 1
        # Background image
        if attrs.get("background_image", ""):
            deco["has_bg_image"] = 1
        # Background color
        bg = attrs.get("background_color", "")
        if bg and bg not in ("rgba(0,0,0,0)", "transparent", ""):
            deco["has_bg_color"] = 1
            deco["bg_color"] = bg
            dark = _is_dark(bg)
            if dark is True:
                deco["bg_is_dark"] = 1
        # Shadow
        shadow = attrs.get("box_shadow_style", "")
        if shadow and shadow != "none" and shadow != "":
            deco["has_shadow"] = 1
            deco["shadow_style"] = shadow
        if attrs.get("box_shadow_blur", ""):
            try:
                deco["shadow_blur"] = float(attrs["box_shadow_blur"].replace("px", "").strip())
            except ValueError:
                pass
        if attrs.get("box_shadow_spread", ""):
            try:
                deco["shadow_spread"] = float(attrs["box_shadow_spread"].replace("px", "").strip())
            except ValueError:
                pass
        if attrs.get("box_shadow_vertical", ""):
            try:
                deco["shadow_vertical"] = float(attrs["box_shadow_vertical"].replace("px", "").strip())
            except ValueError:
                pass
        # Border radius
        radii = attrs.get("border_radii", "")
        if radii and radii.startswith("on"):
            try:
                parts = radii.split("|")
                if len(parts) > 1:
                    val = parts[1].replace("px", "").strip()
                    if val:
                        deco["has_border_radius"] = 1
                        deco["border_radius"] = float(val)
            except ValueError:
                pass
        # Animation
        anim = attrs.get("animation_style", "")
        if anim and anim != "none" and anim != "":
            deco["has_animation"] = 1
            deco["anim_style"] = anim
            if "fade" in anim:
                deco["anim_is_fade"] = 1
            elif "slide" in anim:
                deco["anim_is_slide"] = 1
            elif "zoom" in anim:
                deco["anim_is_zoom"] = 1
            elif "flip" in anim:
                deco["anim_is_flip"] = 1
        if attrs.get("animation_duration", ""):
            d = attrs["animation_duration"].replace("ms", "").strip()
            try:
                deco["anim_duration_ms"] = float(d)
            except ValueError:
                pass
        if attrs.get("animation_delay", ""):
            d = attrs["animation_delay"].replace("ms", "").strip()
            try:
                deco["anim_delay_ms"] = float(d)
            except ValueError:
                pass
        # Hover
        hover_scale = attrs.get("transform_scale__hover", "")
        if hover_scale and "%" in hover_scale:
            try:
                pct = float(hover_scale.replace("%", "").strip())
                if pct != 100:
                    deco["has_hover"] = 1
                    deco["hover_is_scale"] = 1
                    deco["hover_scale_pct"] = pct
            except ValueError:
                pass
        if attrs.get("transform_translate__hover", ""):
            deco["has_hover"] = 1
            deco["hover_is_translate"] = 1
        if attrs.get("transform_rotate__hover", ""):
            deco["has_hover"] = 1
            deco["hover_is_rotate"] = 1
        # Scroll
        scroll_v = attrs.get("scroll_vertical_motion", "")
        if scroll_v:
            deco["has_scroll"] = 1
            deco["scroll_is_vertical"] = 1
        scroll_h = attrs.get("scroll_horizontal_motion", "")
        if scroll_h:
            deco["has_scroll"] = 1
            deco["scroll_is_horizontal"] = 1
        scroll_op = attrs.get("scroll_opacity", "")
        if scroll_op:
            deco["has_scroll"] = 1
            deco["scroll_is_opacity"] = 1
        # Dividers
        top_div = attrs.get("top_divider_style", "")
        if top_div and top_div not in ("none", ""):
            deco["has_divider_top"] = 1
            deco["divider_style"] = top_div
        bot_div = attrs.get("bottom_divider_style", "")
        if bot_div and bot_div not in ("none", ""):
            deco["has_divider_bottom"] = 1
            deco["divider_style"] = bot_div
        # Mask
        mask = attrs.get("background_mask_style", "")
        if mask and mask not in ("none", ""):
            deco["has_mask"] = 1
            deco["mask_style"] = mask
        # Parallax
        if attrs.get("parallax") == "on":
            deco["is_parallax"] = 1
        # Section count
        deco["section_count"] += 1

    def parse_row_attrs(attrs):
        deco["row_count"] += 1
        col_struct = attrs.get("column_structure", "4_4")
        deco["column_count"] += len(col_struct.split(","))

    def walk(text):
        for match in SHORTCODE_RE.finditer(text):
            tag = match.group(1)
            attr_str = match.group(2)
            content = match.group(3)
            attrs = parse_attrs(attr_str)
            if tag == "et_pb_section":
                parse_section_attrs(attrs)
            elif tag == "et_pb_row":
                parse_row_attrs(attrs)
            elif not tag.startswith("et_pb_") and tag.startswith("dipl_"):
                deco["has_dipl_modules"] = 1
            deco["module_count"] += 1
            walk(content)
        for match in SELFCLOSING_RE.finditer(text):
            tag = match.group(1)
            if not tag.startswith("et_pb_") and tag.startswith("dipl_"):
                deco["has_dipl_modules"] = 1
            deco["module_count"] += 1

    walk(shortcode_text)
    return deco


# ─── 2. VECTORIZACIÓN ──────────────────────────────────────────────


def decoration_to_vector(deco):
    """Convierte decoration dict a vector numérico para K-means."""
    return np.array([
        deco["has_gradient"],
        min(deco["gradient_stops"] / 10.0, 1.0),
        deco["gradient_is_linear"],
        deco["gradient_is_radial"],
        min(deco["gradient_deg"] / 360.0, 1.0),
        deco["has_bg_image"],
        deco["has_bg_color"],
        deco["bg_is_dark"],
        deco["has_shadow"],
        1.0 if deco["shadow_style"] != "none" and deco["shadow_style"] != "" else 0.0,
        min(deco["shadow_blur"] / 200.0, 1.0),
        min(deco["shadow_spread"] / 100.0, 1.0),
        deco["has_border_radius"],
        min(deco["border_radius"] / 50.0, 1.0),
        deco["has_animation"],
        deco["anim_is_fade"],
        deco["anim_is_slide"],
        deco["anim_is_zoom"],
        deco["anim_is_flip"],
        min(deco["anim_duration_ms"] / 2000.0, 1.0),
        min(deco["anim_delay_ms"] / 2000.0, 1.0),
        deco["has_hover"],
        deco["hover_is_scale"],
        min((abs(deco["hover_scale_pct"] - 100) / 100.0), 1.0),
        deco["has_scroll"],
        deco["scroll_is_vertical"],
        deco["has_divider_top"],
        deco["has_divider_bottom"],
        deco["has_mask"],
        deco["is_parallax"],
        min(deco["section_count"] / 5.0, 1.0),
        min(deco["row_count"] / 10.0, 1.0),
        min(deco["module_count"] / 30.0, 1.0),
        deco["has_dipl_modules"],
    ], dtype=np.float32)


FEATURE_NAMES = [
    "has_gradient", "gradient_stops_norm", "gradient_is_linear",
    "gradient_is_radial", "gradient_deg_norm", "has_bg_image",
    "has_bg_color", "bg_is_dark", "has_shadow", "shadow_active",
    "shadow_blur_norm", "shadow_spread_norm", "has_border_radius",
    "border_radius_norm", "has_animation", "anim_is_fade",
    "anim_is_slide", "anim_is_zoom", "anim_is_flip",
    "anim_duration_norm", "anim_delay_norm", "has_hover",
    "hover_is_scale", "hover_intensity_norm", "has_scroll",
    "scroll_is_vertical", "has_divider_top", "has_divider_bottom",
    "has_mask", "is_parallax", "section_count_norm", "row_count_norm",
    "module_count_norm", "has_dipl_modules",
]


# ─── 3. CLUSTERING ─────────────────────────────────────────────────


def cluster_templates(vectors, n_clusters=7):
    """K-means clustering sobre vectores decoration."""
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler

    scaler = StandardScaler()
    vectors_scaled = scaler.fit_transform(vectors)

    km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = km.fit_predict(vectors_scaled)

    return km, scaler, labels


def get_cluster_profiles(vectors, labels, names, all_deco):
    """Describe cada cluster: tamaño, feature proportions, templates representativos."""
    n_clusters = len(set(labels))
    profiles = {}
    for cid in range(n_clusters):
        mask = labels == cid
        count = int(mask.sum())
        centroid = vectors[mask].mean(axis=0).tolist()
        members = [names[i] for i in range(len(names)) if labels[i] == cid]
        top_members = sorted(members, key=lambda n: len(n), reverse=True)[:10]

        # Feature proportions (% of templates in cluster with each feature)
        decos_in_cluster = [all_deco[i] for i in range(len(all_deco)) if labels[i] == cid]
        proportions = {}
        prop_features = [
            "has_gradient", "has_bg_image", "has_bg_color", "bg_is_dark",
            "has_shadow", "has_border_radius", "has_animation",
            "has_hover", "has_scroll", "has_divider_top", "has_divider_bottom",
            "has_mask", "is_parallax", "has_dipl_modules",
        ]
        for f in prop_features:
            vals = [d[f] for d in decos_in_cluster]
            proportions[f] = round(sum(vals) / len(vals), 3) if vals else 0

        profiles[f"cluster_{cid}"] = {
            "size": count,
            "pct": round(count / len(labels) * 100, 1),
            "centroid": [round(v, 4) for v in centroid],
            "feature_proportions": proportions,
            "representatives": top_members,
        }
    return profiles


# ─── 4. MAPEO DE CLUSTERS A TONE ──────────────────────────────────


TONE_STYLE_KEYWORDS = {
    "editorial": ["classic", "elegant", "editorial", "minimal", "swiss", "literary", "serif", "refined", "editorial"],
    "modern": ["modern", "tech", "startup", "geometric", "sleek", "sans", "bold", "vibrant", "gradient", "glass"],
    "premium": ["premium", "luxury", "elegant", "gold", "sophisticated", "high-end", "refined", "dark", "dramatic"],
    "minimal": ["minimal", "clean", "white space", "swiss", "functional", "simple", "neutral", "flat"],
    "dramatic": ["dramatic", "bold", "dark", "impactful", "large", "contrast", "hero", "cinematic"],
    "playful": ["playful", "fun", "friendly", "rounded", "colorful", "warm", "casual", "bouncy"],
}


def map_clusters_to_tone(cluster_profiles, labels, section_types):
    """Mapea clusters decoration a tone usando feature_proportions (0-1)."""
    cluster_tone_map = {}
    for cid, profile in cluster_profiles.items():
        props = profile.get("feature_proportions", {})
        scores = {}
        for tone, keywords in TONE_STYLE_KEYWORDS.items():
            kw_str = " ".join(keywords)
            score = 0.0
            if props.get("bg_is_dark", 0) > 0.25:
                score += 0.3 * ("dark" in kw_str or "dramatic" in kw_str or "premium" in kw_str)
            if props.get("has_gradient", 0) > 0.2:
                score += 0.3 * ("gradient" in kw_str or "modern" in kw_str or "vibrant" in kw_str)
            if props.get("has_animation", 0) > 0.25:
                score += 0.2 * ("animated" in kw_str or "modern" in kw_str)
            if props.get("has_border_radius", 0) > 0.25:
                score += 0.2 * ("rounded" in kw_str or "friendly" in kw_str or "modern" in kw_str)
            if props.get("has_shadow", 0) > 0.25:
                score += 0.2 * ("premium" in kw_str or "modern" in kw_str)
            if props.get("is_parallax", 0) > 0.15:
                score += 0.2 * ("dramatic" in kw_str or "cinematic" in kw_str)
            if props.get("has_hover", 0) > 0.25:
                score += 0.15 * ("modern" in kw_str or "bold" in kw_str)
            if props.get("has_divider_top", 0) > 0.2 or props.get("has_divider_bottom", 0) > 0.2:
                score += 0.15 * ("editorial" in kw_str or "premium" in kw_str)
            if props.get("has_bg_image", 0) > 0.3:
                score += 0.1 * ("hero" in kw_str or "dramatic" in kw_str or "editorial" in kw_str)
            if props.get("is_parallax", 0) > 0.1:
                score += 0.1 * ("dramatic" in kw_str or "cinematic" in kw_str)
            scores[tone] = round(score, 3)

        best_tone = max(scores, key=scores.get) if max(scores.values()) > 0 else "editorial"
        cluster_tone_map[cid] = {
            "primary_tone": best_tone,
            "tone_scores": scores,
            "feature_proportions_used": props,
        }
    return cluster_tone_map


# ─── 5. CARGA DE CSVs ──────────────────────────────────────────────


def load_csv(path):
    """Carga CSV como lista de dicts."""
    if not path.exists():
        print(f"[E] CSV not found: {path}", file=sys.stderr)
        return []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [row for row in reader]


def load_colors_csv(path):
    """Carga colors.csv y organiza por Product Type."""
    rows = load_csv(path)
    colors_by_product = {}
    for row in rows:
        product = row.get("Product Type", "").strip()
        if not product:
            continue
        colors_by_product[product] = {
            "primary": row.get("Primary (Hex)", ""),
            "secondary": row.get("Secondary (Hex)", ""),
            "cta": row.get("CTA (Hex)", ""),
            "background": row.get("Background (Hex)", ""),
            "text": row.get("Text (Hex)", ""),
            "border": row.get("Border (Hex)", ""),
            "notes": row.get("Notes", ""),
        }
    return colors_by_product


def load_styles_csv(path):
    """Carga styles.csv y organiza por Style Category + Type."""
    rows = load_csv(path)
    styles_by_tone = defaultdict(list)
    for row in rows:
        keywords = (row.get("Keywords", "") + " " + row.get("Type", "")).lower()
        for tone, tone_kw in TONE_STYLE_KEYWORDS.items():
            for kw in tone_kw:
                if kw in keywords:
                    styles_by_tone[tone].append(row)
                    break
    return styles_by_tone


def load_typography_csv(path):
    """Carga typography.csv y organiza por Mood/Keywords."""
    rows = load_csv(path)
    fonts_by_tone = defaultdict(list)
    for row in rows:
        mood = (row.get("Mood/Style Keywords", "") + " " + row.get("Category", "")).lower()
        for tone, tone_kw in TONE_STYLE_KEYWORDS.items():
            for kw in tone_kw:
                if kw in mood:
                    fonts_by_tone[tone].append(row)
                    break
    return fonts_by_tone


def load_ux_csv(path):
    """Carga ux-guidelines.csv y organiza por Category."""
    rows = load_csv(path)
    ux_by_category = defaultdict(list)
    for row in rows:
        cat = row.get("Category", "").strip()
        ux_by_category[cat].append(row)
    return ux_by_category


# ─── 6. GENERACIÓN DE REGLAS DE DECORACIÓN ─────────────────────────


def generate_decoration_rules(
    cluster_profiles, tone_map, colors_by_product,
    styles_by_tone, fonts_by_tone, ux_by_category,
    section_types_distribution
):
    """Genera decoration-rules.json completo."""
    # Clean cluster_profiles for JSON: remove centroid (noisy), keep proportions
    clean_profiles = {}
    for cid, prof in cluster_profiles.items():
        clean_profiles[cid] = {
            "size": prof["size"],
            "pct": prof["pct"],
            "feature_proportions": prof["feature_proportions"],
            "section_types": prof.get("section_types", {}),
            "representatives": prof["representatives"][:5],
        }

    rules = {
        "meta": {
            "version": "2.0",
            "description": "Decoration rules for DIE — Artifact E",
            "clusters": len(cluster_profiles),
            "features": FEATURE_NAMES,
            "sources": {
                "templates_analyzed": sum(p["size"] for p in cluster_profiles.values()),
                "colors_csv": len(colors_by_product),
                "styles_csv": sum(len(v) for v in styles_by_tone.values()),
                "typography_csv": sum(len(v) for v in fonts_by_tone.values()),
                "ux_csv": sum(len(v) for v in ux_by_category.values()),
            },
        },
        "cluster_profiles": clean_profiles,
        "decoration_by_tone": {},
        "style_by_tone": {},
        "typography_by_tone": {},
        "color_by_product_type": colors_by_product,
        "ux_constraints": {},
    }

    # Mapeo tone → decoration profile (desde clusters)
    for tone in TONE_STYLE_KEYWORDS:
        # Encontrar clusters que mejor matchan este tone
        matching = []
        for cid, tm in tone_map.items():
            score = tm["tone_scores"].get(tone, 0)
            matching.append((score, cid, tm))
        matching.sort(reverse=True)
        best = matching[0] if matching else (0, None, {})

        if best[0] > 0:
            cid_key = best[1]
            profile = cluster_profiles.get(cid_key, {})
            props = profile.get("feature_proportions", {})
        else:
            props = {}

        rules["decoration_by_tone"][tone] = {
            "matched_cluster": best[1] if best[1] is not None else None,
            "cluster_score": round(best[0], 2) if best[0] > 0 else 0,
            "suggestions": {
                "bg_is_dark": bool(props.get("bg_is_dark", 0) > 0.3),
                "has_gradient": bool(props.get("has_gradient", 0) > 0.25),
                "has_shadow": bool(props.get("has_shadow", 0) > 0.3),
                "has_animation": bool(props.get("has_animation", 0) > 0.3),
                "has_hover": bool(props.get("has_hover", 0) > 0.3),
                "has_scroll": bool(props.get("has_scroll", 0) > 0.2),
                "has_dividers": bool(props.get("has_divider_top", 0) > 0.2 or props.get("has_divider_bottom", 0) > 0.2),
                "has_border_radius": bool(props.get("has_border_radius", 0) > 0.3),
                "has_parallax": bool(props.get("is_parallax", 0) > 0.15),
            },
        }

        # Mapeo tone → style
        matching_styles = styles_by_tone.get(tone, [])[:3]
        rules["style_by_tone"][tone] = [
            {
                "name": s.get("Style Category", s.get("Type", "")),
                "keywords": s.get("Keywords", ""),
                "effects": s.get("Effects & Animation", ""),
                "checklist": s.get("Implementation Checklist", ""),
            }
            for s in matching_styles
        ]

        # Mapeo tone → typography
        matching_fonts = fonts_by_tone.get(tone, [])[:2]
        rules["typography_by_tone"][tone] = [
            {
                "name": f.get("Font Pairing Name", ""),
                "heading": f.get("Heading Font", ""),
                "body": f.get("Body Font", ""),
                "mood": f.get("Mood/Style Keywords", ""),
                "notes": f.get("Notes", ""),
            }
            for f in matching_fonts
        ]

    # UX constraints — solo las de alto impacto
    for cat in ["Animation", "Touch", "Layout", "Interaction"]:
        items = ux_by_category.get(cat, [])
        rules["ux_constraints"][cat] = [
            {
                "issue": i.get("Issue", ""),
                "description": i.get("Description", ""),
                "do": i.get("Do", ""),
                "dont": i.get("Don't", ""),
                "severity": i.get("Severity", ""),
            }
            for i in items[:6]
        ]

    return rules


# ─── 7. DECORATION ENGINE (importable) ─────────────────────────────


class DecorationEngine:
    """Motor de decoración para DIE. Importable desde design_intelligence.py.

    Uso:
        deco = DecorationEngine()
        blocks = deco.get_decoration(
            section_type="hero",
            tone="editorial",
            product_type="Digital Library",
            brand_vars=brand_vars,
            brand_presets=brand_presets
        )
    """

    def __init__(self, rules_path=None, clusters_path=None):
        self.rules_path = Path(rules_path) if rules_path else OUTPUT_DIR / "decoration-rules.json"
        self.clusters_path = Path(clusters_path) if clusters_path else OUTPUT_DIR / "decoration-clusters.pkl"
        self.rules = None
        self.km = None
        self.scaler = None
        self._rules_loaded = False
        self._clusters_loaded = False

    def load(self):
        """Carga rules y clusters desde disco."""
        if self.rules_path.exists():
            self.rules = json.loads(self.rules_path.read_text("utf-8"))
            self._rules_loaded = True
            print(f"[E] Rules loaded: {len(self.rules.get('decoration_by_tone', {}))} tones", file=sys.stderr)
        if self.clusters_path.exists():
            with open(self.clusters_path, "rb") as f:
                data = pickle.load(f)
            self.km = data["kmeans"]
            self.scaler = data["scaler"]
            self._clusters_loaded = True
            print(f"[E] Clusters loaded: {self.km.n_clusters} clusters", file=sys.stderr)
        return self

    def is_ready(self):
        return self._rules_loaded and self._clusters_loaded

    def build(self, dataset_path=None, uiux_dir=None, n_clusters=7):
        """Build decoration clusters + rules desde cero.

        Corre local (0 tokens). Produce:
          - decoration-clusters.pkl
          - decoration-rules.json
        """
        dp = Path(dataset_path) if dataset_path else DATASET_PATH
        ux_dir = Path(uiux_dir) if uiux_dir else UIUX_DIR

        print("[E] Loading dataset...", file=sys.stderr)
        records = []
        with open(dp, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

        print(f"[E] Parsing {len(records)} templates for decoration...", file=sys.stderr)
        vectors = []
        names = []
        section_type_counter = Counter()
        metadata_list = []

        for rec in records:
            source = rec.get("source", "unknown")
            raw = rec.get("raw_shortcode", "")
            if not raw:
                continue

            deco = extract_decoration(raw)
            vec = decoration_to_vector(deco)
            vectors.append(vec)
            names.append(source)

            # Infer section_type from source name (same logic as extract_patterns.py)
            sec_type = categorize_section_by_name(source, deco)
            section_type_counter[sec_type] += 1
            metadata_list.append({
                "source": source,
                "section_type": sec_type,
                "decoration": deco,
            })

        vectors = np.array(vectors)
        print(f"[E] Vectors shape: {vectors.shape}", file=sys.stderr)

        # Cluster
        print(f"[E] Clustering into {n_clusters} decoration personas...", file=sys.stderr)
        self.km, self.scaler, labels = cluster_templates(vectors, n_clusters)

        # Collect full deco objects for proportion analysis
        all_deco = [m["decoration"] for m in metadata_list]

        # Profiles
        cluster_profiles = get_cluster_profiles(vectors, labels, names, all_deco)

        # Section type distribution per cluster
        cluster_sec_types = defaultdict(lambda: defaultdict(int))
        for i, meta in enumerate(metadata_list):
            cid = int(labels[i])
            cluster_sec_types[f"cluster_{cid}"][meta["section_type"]] += 1

        for cid_str, sec_counts in cluster_sec_types.items():
            cluster_profiles[cid_str]["section_types"] = dict(
                sorted(sec_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            )

        # Load CSVs
        print(f"[E] Loading ui-ux-pro-max CSVs...", file=sys.stderr)
        colors_path = ux_dir / "colors.csv"
        styles_path = ux_dir / "styles.csv"
        typography_path = ux_dir / "typography.csv"
        ux_path = ux_dir / "ux-guidelines.csv"

        colors_by_product = load_colors_csv(colors_path) if colors_path.exists() else {}
        styles_by_tone = load_styles_csv(styles_path) if styles_path.exists() else {}
        fonts_by_tone = load_typography_csv(typography_path) if typography_path.exists() else {}
        ux_by_category = load_ux_csv(ux_path) if ux_path.exists() else {}

        # Map clusters to tone
        tone_map = map_clusters_to_tone(cluster_profiles, labels, [m["section_type"] for m in metadata_list])

        # Generate rules
        print(f"[E] Generating decoration rules...", file=sys.stderr)
        section_types_distribution = dict(section_type_counter.most_common())
        self.rules = generate_decoration_rules(
            cluster_profiles, tone_map, colors_by_product,
            styles_by_tone, fonts_by_tone, ux_by_category,
            section_types_distribution
        )

        # Save
        self._save()
        print(f"[E] Done.", file=sys.stderr)
        return self

    def _save(self):
        """Save clusters and rules to disk."""
        cluster_data = {
            "kmeans": self.km,
            "scaler": self.scaler,
        }
        with open(self.clusters_path, "wb") as f:
            pickle.dump(cluster_data, f)
        self.rules_path.write_text(json.dumps(self.rules, indent=2, ensure_ascii=False), "utf-8")
        print(f"[E] Saved: {self.clusters_path.name} + {self.rules_path.name}", file=sys.stderr)

    def get_decoration(self, section_type, tone="editorial", product_type=None,
                       brand_vars=None, brand_presets=None):
        """
        Genera decoration blocks completos para una sección.

        Args:
            section_type: str — tipo de sección (hero, features, cta, etc.)
            tone: str — tono visual (editorial, modern, premium, minimal, dramatic, playful)
            product_type: str — tipo de producto (para paleta de colores)
            brand_vars: dict — _design_vars.json (colores, fonts)
            brand_presets: dict — _design_presets.json (64 presets)

        Returns:
            dict — decoration blocks listos para page-def
        """
        if not self._rules_loaded:
            self.load()

        if not self.rules:
            return {}

        deco_profile = self.rules.get("decoration_by_tone", {}).get(tone, {})
        suggestions = deco_profile.get("suggestions", {})
        tone_styles = self.rules.get("style_by_tone", {}).get(tone, [])
        tone_fonts = self.rules.get("typography_by_tone", {}).get(tone, [])
        color_data = self.rules.get("color_by_product_type", {})

        # Elegir paleta de colores
        found_color = None
        if product_type and product_type in color_data:
            found_color = color_data[product_type]
        elif color_data:
            # Fallback: primera paleta disponible
            found_color = list(color_data.values())[0]

        # Mapear colores a tokens del brand si existen
        color_blocks = {}
        if brand_vars and found_color:
            color_blocks = {
                "bg": brand_vars.get("color_surface_deep", brand_vars.get("color_parchment_100", found_color.get("background", ""))),
                "text": brand_vars.get("color_text_primary", found_color.get("text", "")),
                "accent": brand_vars.get("color_accent", found_color.get("primary", "")),
                "cta": brand_vars.get("color_accent_hover", found_color.get("cta", "")),
            }
        elif found_color:
            color_blocks = {
                "bg": found_color.get("background", ""),
                "text": found_color.get("text", ""),
                "accent": found_color.get("primary", ""),
                "cta": found_color.get("cta", ""),
            }

        # Elegir estilo visual
        style_name = tone_styles[0].get("name", "") if tone_styles else ""

        # Elegir typography
        font_pair = tone_fonts[0] if tone_fonts else {}
        if brand_vars:
            font_pair = {
                "heading": brand_vars.get("font_display", font_pair.get("heading", "")),
                "body": brand_vars.get("font_body", font_pair.get("body", "")),
            }

        # Animación desde UX rules
        ux_constraints = self.rules.get("ux_constraints", {})
        anim_rules = ux_constraints.get("Animation", [])

        duration_ms = "800ms"
        easing = "ease-out"
        for rule in anim_rules:
            if "Duration" in rule.get("issue", ""):
                do_text = rule.get("do", "")
                ms_match = re.search(r'(\d+)ms', do_text)
                if ms_match:
                    duration_ms = ms_match.group(1) + "ms"
                break

        # Construir decoration blocks
        decoration = {
            "style_name": style_name,
            "color_scheme": color_blocks,
            "typography": font_pair,
            "motion": {
                "duration": duration_ms,
                "easing": easing,
            },
        }

        if suggestions.get("has_gradient"):
            decoration["gradient"] = self._select_gradient(tone, color_blocks)

        if suggestions.get("has_shadow"):
            decoration["shadow"] = {
                "style": "preset2",
                "color": "rgba(0,0,0,0.1)",
                "blur": "30px",
                "spread": "0px",
            }

        if suggestions.get("has_hover"):
            decoration["hover_transform"] = {
                "scale": "105%",
                "transition": "300ms ease-out",
            }

        if suggestions.get("has_animation"):
            decoration["animation"] = {
                "desktop": {
                    "value": {
                        "style": "fade",
                        "duration": duration_ms,
                        "delay": "0ms",
                    }
                }
            }

        if suggestions.get("has_scroll"):
            decoration["scroll"] = {
                "desktop": {
                    "value": {
                        "verticalMotion": {
                            "enable": "on",
                            "offset": {"start": "6", "mid": "0", "end": "-4"},
                        }
                    }
                }
            }

        if suggestions.get("has_dividers"):
            decoration["divider_style"] = tone if tone in ("editorial", "premium") else "modern"

        if suggestions.get("has_border_radius"):
            decoration["border_radius"] = 12 if tone in ("modern", "playful") else 4 if tone == "minimal" else 0

        return decoration

    def _select_section_preset(self, section_type, tone, brand_presets=None):
        """Selecciona preset de sección según tone + section_type."""
        tone_presets = {
            "editorial": {
                "hero": "section:hero-dark",
                "features": "section:light",
                "cta": "section:cta-epic",
                "testimonials": "section:light",
                "stats": "section:trust-bar",
                "logos": "section:light",
                "content": "section:light",
                "about": "section:hero-dark",
                "faq": "section:light",
                "team": "section:light",
                "contact": "section:light",
                "pricing": "section:light",
                "gallery": "section:dark",
                "blog": "section:light",
                "generic": "section:light",
            },
            "modern": {
                "hero": "section:hero-dark",
                "features": "section:light",
                "cta": "section:cta-epic",
                "testimonials": "section:light",
                "stats": "section:trust-bar",
                "logos": "section:light",
                "content": "section:light",
                "about": "section:light",
                "hero-centered": "section:hero-dark",
            },
            "premium": {
                "hero": "section:hero-dark",
                "cta": "section:cta-epic",
            },
            "minimal": {
                "hero": "section:hero-dark",
                "features": "section:light",
                "cta": "section:light",
            },
            "dramatic": {
                "hero": "section:hero-dark",
                "cta": "section:hero-dark",
                "features": "section:dark",
            },
        }

        mapping = tone_presets.get(tone, tone_presets.get("editorial", {}))
        return mapping.get(section_type, "section:light")

    def _select_gradient(self, tone, color_blocks):
        """Selecciona gradiente según tone."""
        accent = color_blocks.get("accent", "#A67C40")
        bg = color_blocks.get("bg", "#1A1814")
        gradients = {
            "editorial": {"type": "linear", "direction": "135deg", "stops": [
                {"color": accent, "position": "0"},
                {"color": bg, "position": "100"},
            ]},
            "modern": {"type": "linear", "direction": "90deg", "stops": [
                {"color": accent, "position": "0"},
                {"color": bg, "position": "100"},
            ]},
            "premium": {"type": "linear", "direction": "180deg", "stops": [
                {"color": accent, "position": "25"},
                {"color": bg, "position": "100"},
            ]},
            "dramatic": {"type": "linear", "direction": "45deg", "stops": [
                {"color": bg, "position": "0"},
                {"color": accent, "position": "100"},
            ]},
            "playful": {"type": "radial", "direction": "circle at center", "stops": [
                {"color": accent, "position": "0"},
                {"color": bg, "position": "100"},
            ]},
        }
        return gradients.get(tone, gradients["editorial"])


# ─── 8. STUB PARA categorize_section_by_name ────────────────────────


SECTION_TYPE_KEYWORDS = {
    'hero': ['hero', 'heroes', 'landing', 'cover', 'intro', 'banner', 'header', 'under construction', 'coming soon'],
    'about': ['about', 'story', 'who we are', 'our story', 'our mission'],
    'features': ['feature', 'features', 'service', 'services', 'what we do', 'we offer', 'why choose', 'our expertise', 'capabilities', 'offering', 'offerings'],
    'testimonials': ['testimonial', 'testimonials', 'review', 'reviews', 'client', 'clients', 'customer say', 'customer says', 'feedback', 'people say', 'love'],
    'cta': ['call to action', 'cta', 'ctas', 'get started', 'sign up', 'join', 'register', 'book'],
    'pricing': ['pricing', 'pricings', 'plan', 'plans', 'package', 'packages', 'subscription', 'subscriptions', 'membership', 'memberships', 'tier', 'tiers'],
    'team': ['team', 'teams', 'member', 'members', 'people', 'expert', 'experts', 'trainer', 'trainers', 'staff', 'founder', 'founders'],
    'contact': ['contact', 'contacts', 'contacting', 'contacted', 'get in touch', 'reach', 'location', 'locations'],
    'gallery': ['gallery', 'galleries', 'portfolio', 'portfolios', 'project', 'projects', 'work', 'works', 'showcase', 'showcases', 'collection', 'collections'],
    'blog': ['blog', 'blogs', 'news', 'article', 'articles', 'post', 'posts', 'update', 'updates'],
    'faq': ['faq', 'faqs', 'question', 'questions', 'doubt', 'doubts', 'answer', 'answers'],
    'stats': ['counter', 'counters', 'stat', 'stats', 'number', 'numbers', 'achievement', 'achievements', 'milestone', 'milestones'],
    'countdown': ['countdown', 'countdowns', 'coming soon', 'sale', 'offer', 'deal', 'limited'],
    'logos': ['logo', 'logos', 'brand', 'brands', 'partner', 'partners', 'client logo', 'client logos', 'collaborator', 'collaborators'],
    'timeline': ['timeline', 'timelines', 'process', 'processes', 'journey', 'journeys', 'roadmap', 'roadmaps', 'history'],
    'product': ['product', 'products', 'shop', 'shops', 'store', 'stores', 'item', 'items', 'collection', 'collections', 'category', 'categories'],
}


def categorize_section_by_name(dir_name, deco_info):
    """Categoriza una sección por su nombre de directorio más fingerprint decoration."""
    name_lower = dir_name.lower()
    scores = {}
    for cat, keywords in SECTION_TYPE_KEYWORDS.items():
        for kw in keywords:
            if re.search(r'\b' + re.escape(kw) + r'\b', name_lower):
                if name_lower.startswith(kw) or name_lower.endswith(kw):
                    scores[cat] = scores.get(cat, 0) + 15
                else:
                    scores[cat] = scores.get(cat, 0) + 5
    # Module fingerprint boost
    if deco_info.get("has_dipl_modules", 0):
        pass
    if not scores:
        return "generic"
    return max(scores, key=scores.get)


# ─── 9. CLI ────────────────────────────────────────────────────────


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Artifact E: Decoration Engine")
    parser.add_argument("--build", action="store_true", help="Build clusters + rules from dataset")
    parser.add_argument("--dataset", default=str(DATASET_PATH), help="Path to dataset.jsonl")
    parser.add_argument("--uiux-dir", default=str(UIUX_DIR), help="Path to ui-ux-pro-max/data/")
    parser.add_argument("--clusters", type=int, default=7, help="Number of decoration clusters")
    args = parser.parse_args()

    if args.build:
        engine = DecorationEngine()
        engine.build(
            dataset_path=args.dataset,
            uiux_dir=args.uiux_dir,
            n_clusters=args.clusters,
        )
        return 0
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
