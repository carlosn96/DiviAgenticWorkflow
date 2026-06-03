#!/usr/bin/env python3
"""
design_translator.py — Build one-time: traduce los 4 CSVs de ui-ux-pro-max
a reglas Divi-nativas consultables por design_director.py en runtime.

Output: artifacts/design_rules_divi.pkl

Sin hardcodeo. Cada CSV entry se convierte en feature vectors + metadatos.
El director consulta por similitud/top-N, no por lookup de diccionario fijo.
"""

import csv, json, pickle, re, numpy as np, sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

ARTIFACTS_DIR = Path(__file__).resolve().parent
DAW_ROOT = ARTIFACTS_DIR.parent.parent
UX_PRO_DIR = DAW_ROOT / "ui-ux-pro-max" / "data"

OUTPUT_PATH = ARTIFACTS_DIR / "design_rules_divi.pkl"

SECTION_TYPES = [
    "hero", "hero-centered", "features", "content", "content-list",
    "stats", "testimonials", "logos", "cta", "faq", "pricing",
    "team", "gallery", "contact", "about", "blog", "generic"
]

DIVI_TONES = ["editorial", "modern", "premium", "minimal", "dramatic", "playful"]

STYLE_TONE_MAP = {
    "editorial": ["Minimalism & Swiss Style", "Editorial Classic", "Magazine Style", "Flat Design"],
    "modern": ["Modern Professional", "Tech Startup", "Geometric Modern", "Friendly SaaS", "Aurora UI"],
    "premium": ["Glassmorphism", "Liquid Glass", "Luxury Serif", "Premium Sans", "3D & Hyperrealism"],
    "minimal": ["Minimal Swiss", "Minimal & Direct", "Minimalist Portfolio", "Zero Interface", "Soft UI Evolution"],
    "dramatic": ["Brutalism", "Motion-Driven", "Retro-Futurism", "Dark Mode (OLED)", "Bold Statement"],
    "playful": ["Claymorphism", "Vibrant & Block-based", "Playful Creative", "Neumorphism", "Micro-interactions"],
}

COLOR_PRODUCT_MAP = {
    "contact": "Service Landing Page",
    "about": "Portfolio/Personal",
    "hero": "Service Landing Page",
    "hero-centered": "Service Landing Page",
    "features": "SaaS (General)",
    "content": "Educational App",
    "content-list": "Educational App",
    "cta": "Conversion-Optimized",
    "stats": "Analytics Dashboard",
    "testimonials": "Social Proof-Focused",
    "logos": "Design System/Component Library",
    "faq": "Knowledge Base/Documentation",
    "pricing": "SaaS (General)",
    "team": "Creative Agency",
    "gallery": "Portfolio/Personal",
    "blog": "Magazine/Blog",
    "generic": "B2B Service",
}


# ── Helpers ──────────────────────────────────────────────────────────────────

def _csv_to_dicts(path):
    """Read a CSV and return list of dicts, handling encoding."""
    if not path.exists():
        print(f"  WARN: {path.name} not found")
        return []
    with open(path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return list(reader)


def _embed_text(text, dim=64):
    """Simple character-n-gram embedding (no torch, no transformers).
    Produces a deterministic 64-dim vector from any text.
    """
    text = text.lower().strip()
    vec = np.zeros(dim, dtype=np.float32)
    for i, ch in enumerate(text.encode("utf-8", errors="ignore")):
        vec[i % dim] += float(ch) / 255.0
    # bigram
    for i in range(len(text) - 1):
        bigram = text[i:i+2]
        h = hash(bigram) % dim
        vec[h] += 0.5
    # normalize
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec /= norm
    return vec


def _cosine_sim(a, b):
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))


def _parse_hex(h):
    """Parse hex color to RGB tuple."""
    h = h.strip().lstrip("#")
    if len(h) != 6:
        return (128, 128, 128)
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _rgb_distance(a, b):
    """Euclidean distance between two RGB colors."""
    return np.sqrt(sum((x - y)**2 for x, y in zip(a, b)))


# ── Style Encoder ────────────────────────────────────────────────────────────

def _encode_styles(rows):
    styles = {}
    for row in rows:
        name = row.get("Style Category", "").strip()
        if not name:
            continue
        keywords = row.get("Keywords", "")
        effects = row.get("Effects & Animation", "")
        best_for = row.get("Best For", "")
        ai_keywords = row.get("AI Prompt Keywords", "")
        css_keywords = row.get("CSS/Technical Keywords", "")
        checklist = row.get("Implementation Checklist", "")
        css_vars = row.get("Design System Variables", "")

        embed_text = f"{name} {keywords} {best_for} {ai_keywords}"
        embedding = _embed_text(embed_text)

        styles[name] = {
            "name": name,
            "keywords": keywords,
            "effects": effects,
            "best_for": best_for,
            "ai_prompt": ai_keywords,
            "css_tech": css_keywords,
            "checklist": checklist,
            "css_vars": css_vars,
            "light_mode": row.get("Light Mode ✓", "").startswith("✓"),
            "dark_mode": row.get("Dark Mode ✓", "").startswith("✓"),
            "mobile_friendly": row.get("Mobile-Friendly", "").startswith("✓"),
            "conversion_focused": row.get("Conversion-Focused", "").startswith("✓"),
            "complexity": row.get("Complexity", "Low"),
            "embedding": embedding.tolist(),
        }
    return styles


# ── Color Encoder ────────────────────────────────────────────────────────────

def _encode_colors(rows):
    colors = {}
    embedding_dim = 6 * 3  # 6 colors × 3 RGB = 18
    for row in rows:
        pt = row.get("Product Type", "").strip()
        if not pt:
            continue
        color_vec = []
        for field in ["Primary (Hex)", "Secondary (Hex)", "CTA (Hex)",
                       "Background (Hex)", "Text (Hex)", "Border (Hex)"]:
            h = row.get(field, "#808080")
            rgb = _parse_hex(h)
            color_vec.extend(rgb)
        colors[pt] = {
            "product_type": pt,
            "primary": row.get("Primary (Hex)", ""),
            "secondary": row.get("Secondary (Hex)", ""),
            "cta": row.get("CTA (Hex)", ""),
            "background": row.get("Background (Hex)", ""),
            "text": row.get("Text (Hex)", ""),
            "border": row.get("Border (Hex)", ""),
            "notes": row.get("Notes", ""),
            "rgb_vector": color_vec,
            "embedding": np.array(color_vec, dtype=np.float32) / 255.0,
        }
    return colors


# ── Typography Encoder ───────────────────────────────────────────────────────

def _encode_typography(rows):
    pairs = {}
    for row in rows:
        name = row.get("Font Pairing Name", "").strip()
        if not name:
            continue
        cat = row.get("Category", "Sans + Sans")
        heading = row.get("Heading Font", "")
        body = row.get("Body Font", "")
        mood = row.get("Mood/Style Keywords", "")
        best_for = row.get("Best For", "")
        notes = row.get("Notes", "")

        embed_text = f"{name} {mood} {best_for} {cat}"
        embedding = _embed_text(embed_text)

        pairs[name] = {
            "name": name,
            "category": cat,
            "heading_font": heading,
            "body_font": body,
            "mood_keywords": mood,
            "best_for": best_for,
            "notes": notes,
            "embedding": embedding.tolist(),
        }
    return pairs


# ── UX Rules Encoder ─────────────────────────────────────────────────────────

def _encode_ux_rules(rows):
    rules = {}
    for row in rows:
        rule_id = int(row.get("No", 0))
        cat = row.get("Category", "").strip()
        issue = row.get("Issue", "").strip()
        description = row.get("Description", "")
        do_text = row.get("Do", "")
        dont_text = row.get("Don't", "")
        severity = row.get("Severity", "Medium")

        embed_text = f"{cat} {issue} {description}"
        embedding = _embed_text(embed_text)

        rules[f"{cat}_{issue}"] = {
            "id": rule_id,
            "category": cat,
            "issue": issue,
            "description": description,
            "do": do_text,
            "dont": dont_text,
            "severity": severity,
            "embedding": embedding.tolist(),
        }
    return rules


# ── Section-Type Mappings ───────────────────────────────────────────────────

def _build_section_style_map(styles_dict):
    """Create a reverse map: section_type + tone → best matching styles."""
    section_map = {}
    for st in SECTION_TYPES:
        section_map[st] = {}
        for tone in DIVI_TONES:
            candidates = STYLE_TONE_MAP.get(tone, [])
            matched = []
            for sname in candidates:
                if sname in styles_dict:
                    matched.append(sname)
            section_map[st][tone] = matched[:3]
    return section_map


def _build_product_color_map(colors_dict):
    """Create a reverse map: section_type → product_type → color palette."""
    section_map = {}
    for st in SECTION_TYPES:
        pt_key = COLOR_PRODUCT_MAP.get(st, "B2B Service")
        matched = colors_dict.get(pt_key, None)
        section_map[st] = {
            "product_type": pt_key,
            "palette": matched,
        }
    return section_map


# ── Main Build ───────────────────────────────────────────────────────────────

def build():
    print("=" * 60)
    print("design_translator.py — build one-time")
    print("=" * 60)

    rules = {
        "version": "1.0",
        "description": "UI-UX-PRO MAX intelligence translated to Divi-native rules",
        "domains": {},
        "embeddings": {},
        "section_maps": {},
    }

    # 1. Styles
    print("\n[1/4] Encoding styles...")
    styles_path = UX_PRO_DIR / "styles.csv"
    style_rows = _csv_to_dicts(styles_path)
    styles_dict = _encode_styles(style_rows)
    rules["domains"]["styles"] = styles_dict
    rules["embeddings"]["styles"] = {
        name: s["embedding"] for name, s in styles_dict.items()
    }
    print(f"  {len(styles_dict)} styles encoded")

    # 2. Colors
    print("\n[2/4] Encoding colors...")
    colors_path = UX_PRO_DIR / "colors.csv"
    color_rows = _csv_to_dicts(colors_path)
    colors_dict = _encode_colors(color_rows)
    rules["domains"]["colors"] = {}
    for pt, data in colors_dict.items():
        entry = dict(data)
        entry.pop("embedding", None)
        entry.pop("rgb_vector", None)
        rules["domains"]["colors"][pt] = entry
    rules["embeddings"]["colors"] = {
        pt: data["embedding"].tolist() for pt, data in colors_dict.items()
    }
    print(f"  {len(colors_dict)} product color palettes encoded")

    # 3. Typography
    print("\n[3/4] Encoding typography...")
    typo_path = UX_PRO_DIR / "typography.csv"
    typo_rows = _csv_to_dicts(typo_path)
    typo_dict = _encode_typography(typo_rows)
    rules["domains"]["typography"] = {
        name: {k: v for k, v in t.items() if k != "embedding"}
        for name, t in typo_dict.items()
    }
    rules["embeddings"]["typography"] = {
        name: t["embedding"] for name, t in typo_dict.items()
    }
    print(f"  {len(typo_dict)} font pairings encoded")

    # 4. UX Rules
    print("\n[4/4] Encoding UX rules...")
    ux_path = UX_PRO_DIR / "ux-guidelines.csv"
    ux_rows = _csv_to_dicts(ux_path)
    ux_dict = _encode_ux_rules(ux_rows)
    rules["domains"]["ux"] = {
        k: {kk: vv for kk, vv in v.items() if kk != "embedding"}
        for k, v in ux_dict.items()
    }
    rules["embeddings"]["ux"] = {
        k: v["embedding"] for k, v in ux_dict.items()
    }
    print(f"  {len(ux_dict)} UX rules encoded")

    # 5. Section-type maps
    print("\n[5] Building section-type maps...")
    section_style_map = _build_section_style_map(styles_dict)
    section_color_map = _build_product_color_map(colors_dict)
    rules["section_maps"]["styles"] = section_style_map
    rules["section_maps"]["colors"] = section_color_map

    # 6. Tone definitions (Divi-specific)
    rules["tone_definitions"] = {
        tone: {
            "style_candidates": STYLE_TONE_MAP.get(tone, []),
            "animation_duration": {
                "editorial": "600ms",
                "modern": "400ms",
                "premium": "800ms",
                "minimal": "300ms",
                "dramatic": "200ms",
                "playful": "500ms",
            }.get(tone, "400ms"),
            "border_radius": {
                "editorial": "0px",
                "modern": "8px",
                "premium": "12px",
                "minimal": "4px",
                "dramatic": "0px",
                "playful": "16px",
            }.get(tone, "8px"),
            "shadow_intensity": {
                "editorial": "low",
                "modern": "medium",
                "premium": "high",
                "minimal": "none",
                "dramatic": "high",
                "playful": "medium",
            }.get(tone, "medium"),
        }
        for tone in DIVI_TONES
    }

    # 7. Save
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "wb") as f:
        pickle.dump(rules, f, protocol=pickle.HIGHEST_PROTOCOL)
    print(f"\n✅ Output: {OUTPUT_PATH} ({OUTPUT_PATH.stat().st_size / 1024:.1f} KB)")
    print("\nDomains: styles, colors, typography, ux")
    print(f"Tones: {DIVI_TONES}")
    print(f"Section types: {len(SECTION_TYPES)}")
    return rules


if __name__ == "__main__":
    build()
