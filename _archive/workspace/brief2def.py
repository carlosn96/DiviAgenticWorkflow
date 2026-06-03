"""brief2def.py — Diseño real con alternancia visual.
Alterna fondos (dark/light), grids variados, presets distintos por tipo.
El diseño visual está en divitheme.json; brief2def solo elige qué usar y cómo
organizar contenido para crear ritmo visual.
"""
import json, sys, re
from pathlib import Path

DAW_ROOT = Path(__file__).resolve().parent.parent
DAW_SITE = "aeroluxe"
SITE = DAW_ROOT / "site" / DAW_SITE
BRIEF_PATH = Path(sys.argv[1])
DEF_PATH = Path(sys.argv[2])

with open(BRIEF_PATH, "rb") as f:
    brief = json.load(f)

# ── Paleta de secciones ─────────────────────────────────────────
# Cada tipo tiene: preset de seccion, preset de titulo, preset de body
SECTION_PROFILE = {
    "hero":       {"preset": "section:hero-dark",  "title_preset": "text:display-xl", "body_preset": "text:body-dark"},
    "trust-bar":  {"preset": "section:light",       "title_preset": None,              "body_preset": None},
    "features":   {"preset": "section:hero-dark",  "title_preset": "text:display-md", "body_preset": "text:body-dark"},
    "stats":      {"preset": "section:hero-dark",  "title_preset": "text:display-md", "body_preset": "text:body-dark"},
    "testimonials": {"preset": "section:light",    "title_preset": "text:heading-light","body_preset": "text:body-light"},
    "pricing":    {"preset": "section:light",       "title_preset": "text:heading-light","body_preset": "text:body-light"},
    "cta":        {"preset": "section:cta-epic",    "title_preset": "text:display-xl", "body_preset": "text:body-dark"},
    "content":    {"preset": "section:light",       "title_preset": "text:heading-light","body_preset": "text:body-light"},
}

def section_intro(eyebrow, title, section_type):
    rows = []
    if eyebrow:
        rows.append({
            "column_structure": "4_4",
            "modules": [{"type": "divi/text", "presets": ["text:eyebrow"], "content": f"<p>{eyebrow}</p>"}]
        })
    profile = SECTION_PROFILE.get(section_type, SECTION_PROFILE["content"])
    tp = profile.get("title_preset")
    if title:
        tag = "h1" if section_type == "hero" else "h2"
        rows.append({
            "column_structure": "4_4",
            "modules": [{"type": "divi/text", "presets": [tp], "content": f"<{tag}>{title}</{tag}>"}]
        })
    return rows

sections = []

for sec in brief.get("sections", []):
    st = sec.get("section_type", "content")
    profile = SECTION_PROFILE.get(st, SECTION_PROFILE["content"])

    # ── Hero ───────────────────────────────────────────────────
    if st == "hero":
        modules = []
        eyb = sec.get("eyebrow", "")
        if eyb: modules.append({"type": "divi/text", "presets": ["text:eyebrow"], "content": f"<p>{eyb}</p>"})
        title = sec.get("title", "")
        if title: modules.append({"type": "divi/text", "presets": ["text:display-xl"], "content": f"<h1>{title}</h1>"})
        body = sec.get("text", "")
        if body: modules.append({"type": "divi/text", "presets": ["text:body-dark"], "content": f"<p>{body}</p>"})
        # Gold accent divider
        modules.append({"type": "divi/divider", "presets": ["divider:gold-line"]})
        bt = sec.get("btn_primary_text", "")
        if bt: modules.append({"type": "divi/button", "presets": ["module:btn-primary"],
            "button_text": bt, "button_url": sec.get("btn_primary_url", "#")})
        bt2 = sec.get("btn_secondary_text", "")
        if bt2: modules.append({"type": "divi/button", "presets": ["module:btn-gold-outline"],
            "button_text": bt2, "button_url": sec.get("btn_secondary_url", "#")})
        sections.append({
            "presets": [profile["preset"]],
            "rows": [{"column_structure": "4_4", "modules": modules}],
        })
        continue

    # ── Trust Bar ──────────────────────────────────────────────
    if st == "trust-bar":
        items = sec.get("items", [])
        modules = []
        for item in items:
            src = item.get("image", "")
            if src:
                modules.append({"type": "divi/image", "presets": ["module:glass-card-compact"],
                    "src": src, "alt": item.get("alt", "")})
        if modules:
            ct = ",".join(["1_4"] * len(modules))
            cols = [{"type": "1_4", "modules": [modules[i]]} for i in range(len(modules))]
            sections.append({
                "presets": [profile["preset"]],
                "spacing": {"desktop": {"value": {"padding": {"top": "60px", "bottom": "60px"}}}},
                "rows": [{"column_structure": ct, "columns": cols}],
                "animation": "fade-up",
            })
        continue

    # ── Features ───────────────────────────────────────────────
    if st == "features":
        items = sec.get("items", [])
        rows = section_intro(sec.get("eyebrow", ""), sec.get("title", ""), st)
        for i in range(0, len(items), 2):
            pair = items[i:i+2]
            cols = []
            for item in pair:
                cols.append({"type": "1_2", "modules": [
                    {"type": "divi/blurb", "presets": ["module:feature-card"],
                        "title": item.get("title", ""),
                        "content": f"<p>{item.get('text', '')}</p>" if item.get("text") else "",
                        "icon": item.get("icon", "&#xe03a;")}
                ]})
            rows.append({"column_structure": "1_2,1_2", "columns": cols})
        sections.append({
            "presets": [profile["preset"]],
            "rows": rows,
            "animation": "stagger-subtle",
        })
        continue

    # ── Stats ──────────────────────────────────────────────────
    if st == "stats":
        stats = sec.get("stats", [])
        rows = section_intro(sec.get("eyebrow", ""), sec.get("title", ""), st)
        col_count = len(stats)
        frac = ["1_5"] * 5
        ct = ",".join(frac[:col_count])
        cols = []
        for stat in stats:
            num_raw = stat.get("number", "0")
            num_str = re.sub(r'[^0-9.]', '', str(num_raw))
            sm = []
            sm.append({"type": "divi/text", "presets": ["text:stat-number"],
                "content": f"<p>{num_raw}</p>"})
            label = stat.get("label", "")
            if label:
                sm.append({"type": "divi/text", "presets": ["text:stat-label"],
                    "content": f"<p>{label}</p>"})
            cols.append({"type": frac[min(len(cols), 4)], "modules": sm})
        rows.append({"column_structure": ct, "columns": cols})
        sections.append({
            "presets": [profile["preset"]],
            "rows": rows,
            "spacing": {"desktop": {"value": {"padding": {"top": "120px", "bottom": "120px"}}}},
            "animation": "stagger-subtle",
        })
        continue

    # ── Testimonials ───────────────────────────────────────────
    if st == "testimonials":
        tms = sec.get("testimonials", [])
        rows = section_intro(sec.get("eyebrow", ""), sec.get("title", ""), st)
        frac = ["1_3"] * 3
        ct = ",".join(frac[:len(tms)])
        cols = []
        for t in tms:
            mods = [{"type": "divi/testimonial", "presets": ["module:testimonial-card"],
                "content": f"<p>{t.get('text', '')}</p>",
                "author": t.get("name", "")}]
            cols.append({"type": frac[min(len(cols), 2)], "modules": mods})
        rows.append({"column_structure": ct, "columns": cols})
        sections.append({
            "presets": [profile["preset"]],
            "rows": rows,
            "animation": "stagger-subtle",
        })
        continue

    # ── Pricing ────────────────────────────────────────────────
    if st == "pricing":
        pkgs = sec.get("packages", sec.get("pricing", []))
        rows = section_intro(sec.get("eyebrow", ""), sec.get("title", ""), st)
        frac = ["1_3"] * 3
        ct = ",".join(frac[:len(pkgs)])
        cols = []
        for pkg in pkgs:
            feats = "".join(f"<li>{f}</li>" for f in pkg.get("features", []))
            pcard = "module:pricing-card-featured" if pkg.get("highlight") or pkg.get("featured") else "module:pricing-card"
            mods = [{"type": "divi/pricing-table", "presets": [pcard],
                "title": pkg.get("name", ""), "price": pkg.get("price", ""),
                "content": f"<ul>{feats}</ul>" if feats else ""}]
            cols.append({"type": frac[min(len(cols), 2)], "modules": mods})
        rows.append({"column_structure": ct, "columns": cols})
        sections.append({
            "presets": [profile["preset"]],
            "rows": rows,
            "animation": "stagger-subtle",
        })
        continue

    # ── CTA ─────────────────────────────────────────────────────
    if st == "cta":
        modules = []
        eyb = sec.get("eyebrow", "")
        if eyb: modules.append({"type": "divi/text", "presets": ["text:eyebrow"], "content": f"<p>{eyb}</p>"})
        title = sec.get("title", "")
        if title: modules.append({"type": "divi/text", "presets": ["text:display-xl"], "content": f"<h2>{title}</h2>"})
        body = sec.get("text", "")
        if body: modules.append({"type": "divi/text", "presets": ["text:body-dark"], "content": f"<p>{body}</p>"})
        bt = sec.get("btn_primary_text", "")
        if bt: modules.append({"type": "divi/button", "presets": ["module:btn-primary"],
            "button_text": bt, "button_url": sec.get("btn_primary_url", "#")})
        sections.append({
            "presets": [profile["preset"]],
            "rows": [{"column_structure": "4_4", "modules": modules}],
            "animation": "fade-up",
        })
        continue

    # ── Content / fallback ─────────────────────────────────────
    modules = []
    eyb = sec.get("eyebrow", "")
    if eyb: modules.append({"type": "divi/text", "presets": ["text:eyebrow"], "content": f"<p>{eyb}</p>"})
    title = sec.get("title", "")
    bp = profile.get("title_preset")
    if title and bp:
        modules.append({"type": "divi/text", "presets": [bp], "content": f"<h2>{title}</h2>"})
    body = sec.get("text", "")
    bp2 = profile.get("body_preset")
    if body and bp2:
        modules.append({"type": "divi/text", "presets": [bp2], "content": f"<p>{body}</p>"})
    if modules:
        sections.append({
            "presets": [profile["preset"]],
            "rows": [{"column_structure": "4_4", "modules": modules}],
            "animation": "fade-up",
        })

result = {
    "title": brief.get("title", "Page"),
    "slug": brief.get("slug", re.sub(r'[^a-z0-9]+', '-', brief.get("title", "page").lower()).strip('-') or "page"),
    "sections": sections,
}

with open(DEF_PATH, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print(f"page-def: {DEF_PATH}")
print(f"sections: {len(sections)}")
