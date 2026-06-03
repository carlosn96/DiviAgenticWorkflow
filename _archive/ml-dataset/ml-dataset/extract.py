#!/usr/bin/env python3
"""
extract.py — Extrae un dataset limpio desde los raw shortcodes Divi 4.
 
Lee catalog/jsons/ y produce:
  ml-dataset/dataset.jsonl       ← registro por línea (sin pérdida)
  ml-dataset/inventory.csv       ← resumen plano: tipos de módulo, colores, texto

Diferencias con compile_catalog.py:
  - NO resuelve colores a tokens de marca
  - NO reemplaza contenido por {{slot:*}}
  - NO limita a 20 tags mapeados — registra TODOS los tags reales
  - NO convierte a schema Divi 5 — preserva la data original + metadata extraída
"""

import json, re, csv, sys
from pathlib import Path
from collections import Counter
from html import unescape

DAW_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = DAW_ROOT / "workspace" / "catalog" / "jsons"
OUT_DIR = Path(__file__).resolve().parent

TAG_RE = re.compile(r'\[(\w+)([^\]]*)\](.*?)\[\/\1\]', re.DOTALL)
SELFCLOSE_RE = re.compile(r'\[(\w+)([^\]]*?)/\]')
ATTR_RE = re.compile(r"(\w+)\s*=\s*(?:\"([^\"]*)\"|'([^']*)'|([^\s]+))")

COLOR_RE = re.compile(
    r'#'
    r'([0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\b'
    r'|'
    r'rgba?\s*\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*(?:,\s*[\d.]+\s*)?\)'
)

SKIP_TAGS = {'et_pb_section', 'et_pb_row', 'et_pb_row_inner', 'et_pb_column', 'et_pb_column_inner'}


def parse_attrs(attr_str: str) -> dict:
    attrs = {}
    for m in ATTR_RE.finditer(attr_str):
        key = m.group(1)
        val = (m.group(2) or m.group(3) or m.group(4) or "").strip()
        attrs[key] = unescape(val)
    return attrs


def walk_shortcodes(text: str) -> list:
    nodes = []

    def _walk(t: str) -> list:
        children = []
        pos = 0
        while pos < len(t):
            pair = TAG_RE.search(t, pos)
            selfclose = SELFCLOSE_RE.search(t, pos)

            pair_start = pair.start() if pair else len(t) + 1
            sc_start = selfclose.start() if selfclose else len(t) + 1

            if pair_start < sc_start:
                tag, attr_str, content = pair.group(1), pair.group(2), pair.group(3)
                attrs = parse_attrs(attr_str)
                inner_children = _walk(content)
                node = {
                    "tag": tag,
                    "attrs": attrs,
                    "content_text": content.strip() if tag not in SKIP_TAGS else "",
                    "children": inner_children,
                }
                children.append(node)
                pos = pair.end()
            elif sc_start < pair_start:
                tag, attr_str = selfclose.group(1), selfclose.group(2)
                attrs = parse_attrs(attr_str)
                node = {
                    "tag": tag,
                    "attrs": attrs,
                    "content_text": "",
                    "children": [],
                }
                children.append(node)
                pos = selfclose.end()
            else:
                break
        return children

    return _walk(text)


def extract_colors(attrs: dict) -> list:
    found = []
    for k, v in attrs.items():
        for m in COLOR_RE.finditer(v):
            found.append({"attribute": k, "value": m.group(0)})
    return found


def walk_nodes(nodes: list, collector: list | None = None) -> list:
    if collector is None:
        collector = []
    for n in nodes:
        collector.append(n)
        walk_nodes(n.get("children", []), collector)
    return collector


def process_raw_file(json_path: Path) -> dict | None:
    folder_name = json_path.parent.name
    try:
        raw = json_path.read_text("utf-8")
        data = json.loads(raw)
    except (json.JSONDecodeError, OSError) as e:
        print(f"[SKIP] JSON error {json_path.name}: {e}", file=sys.stderr)
        return None

    inner = data.get("data", {})
    shortcode_text = ""
    for val in inner.values():
        if isinstance(val, str):
            shortcode_text += val
    if not shortcode_text.strip():
        return None

    tree = walk_shortcodes(shortcode_text)

    flat = walk_nodes(tree)
    all_colors = []
    all_texts = []
    all_module_types = []
    
    slots_offered = {
        "titles": 0,
        "paragraphs": 0,
        "buttons": 0,
        "images": 0,
        "features": 0,
        "testimonials": 0,
        "stats": 0,
        "logos": 0,
        "items": 0
    }

    # Slot categorization: tags grouped by semantic slot type
    TAG_SLOTS = {
        "buttons": {
            "et_pb_button", "dipl_button_item", "dipl_button",
            "et_pb_cta", "et_pb_signup",
        },
        "images": {
            "et_pb_image", "dipl_image_mask", "dipl_floating_image",
            "dipl_featured_image", "et_pb_video_slider_item",
        },
        "logos": {
            # Logos use image tags but with logo-related semantic context
            # Detected via folder name OR image attrs containing logo/brand/client
        },
        "features": {
            "et_pb_blurb", "et_pb_team_member", "et_pb_toggle",
            "et_pb_accordion_item", "dipl_faq", "dipl_faq_item",
        },
        "testimonials": {
            "et_pb_testimonial", "dipl_testimonial", "dipl_testimonial_slider",
            "dipl_testimonial_slider_item",
        },
        "stats": {
            "et_pb_number_counter", "et_pb_circle_counter",
            "et_pb_counter", "dipl_counter", "dipl_bar_counter",
        },
        "titles": {
            "dipl_double_color_heading", "dipl_text_animator",
            "dipl_text_highlighter", "dipl_advanced_heading",
            "dipl_fancy_heading",
        },
        "items": {
            "dipl_timeline_item", "dipl_floating_image_item",
            "dipl_hover_box", "dipl_content_toggle",
            "et_pb_pricing_table", "et_pb_portfolio",
        },
    }

    _logo_keywords = {"logo", "brand", "partner", "sponsor", "client", "patrocinador", "cliente", "marca"}

    for node in flat:
        tag = node["tag"]
        attrs = node.get("attrs", {})
        all_colors.extend(extract_colors(attrs))
        txt = node.get("content_text", "")
        
        cleaned = ""
        if txt:
            cleaned = re.sub(r'<[^>]+>', ' ', txt)
            cleaned = re.sub(r'\[.*?\]', ' ', cleaned)
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()
            if cleaned:
                all_texts.append({"tag": tag, "text": cleaned[:500]})
                
        all_module_types.append(tag)
        
        # Categorize into slots — check named slot sets first
        assigned = False
        for slot_name, slot_tags in TAG_SLOTS.items():
            if not slot_tags:
                continue
            if tag in slot_tags:
                slots_offered[slot_name] += 1
                assigned = True
                break
        
        if assigned:
            continue

        # Image-or-logo: check folder name and image src attributes
        if tag in ("et_pb_image", "dipl_image_mask", "dipl_floating_image", "dipl_featured_image"):
            is_logo = False
            folder_lower = folder_name.lower()
            if any(kw in folder_lower for kw in _logo_keywords):
                is_logo = True
            else:
                img_attrs = json.dumps(attrs).lower()
                if any(kw in img_attrs for kw in _logo_keywords):
                    is_logo = True
            if is_logo:
                slots_offered["logos"] += 1
            else:
                slots_offered["images"] += 1
            continue

        # et_pb_text: title if short or has heading tags, else paragraph
        if tag == "et_pb_text":
            if cleaned:
                if ("<h1" in txt.lower() or "<h2" in txt.lower() or
                    "<h3" in txt.lower() or "<h4" in txt.lower() or
                    len(cleaned) < 80):
                    slots_offered["titles"] += 1
                else:
                    slots_offered["paragraphs"] += 1
            continue
        
        # Unmatched modules that contain repeatable items → items slot
        if tag.endswith("_item") or tag.endswith("_slider") or "pricing" in tag:
            slots_offered["items"] += 1
            continue

    # Count total columns in template structure
    columns_count = len([n for n in flat if n["tag"] in ("et_pb_column", "et_pb_column_inner")])

    return {
        "source": folder_name,
        "path": str(json_path.resolve()),
        "raw_shortcode": shortcode_text[:5000],
        "module_types": sorted(set(all_module_types)),
        "module_count": len([t for t in all_module_types if t not in SKIP_TAGS]),
        "slots_offered": slots_offered,
        "columns_count": columns_count,
        "colors": all_colors[:100],
        "content_texts": all_texts[:50],
        "tag_count": len(flat),
        "tree": tree,
    }


def main():
    if not RAW_DIR.is_dir():
        print(f"ERROR: {RAW_DIR} no existe", file=sys.stderr)
        sys.exit(1)

    out_dir = OUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = out_dir / "dataset.jsonl"
    csv_path = out_dir / "inventory.csv"

    subdirs = sorted([d for d in RAW_DIR.iterdir() if d.is_dir()])
    print(f"[EXTRACT] Leyendo {len(subdirs)} templates desde {RAW_DIR}")

    records = []
    module_counter = Counter()
    tag_counter = Counter()
    errors = 0

    for subdir in subdirs:
        json_files = list(subdir.glob("*.json"))
        if not json_files:
            continue
        rec = process_raw_file(json_files[0])
        if rec is None:
            errors += 1
            continue
        records.append(rec)
        for mt in rec["module_types"]:
            module_counter[mt] += 1
        tag_counter[rec["module_count"]] += 1

        if len(records) % 200 == 0:
            print(f"[EXTRACT]  {len(records)} procesados...")

    print(f"[EXTRACT] Total: {len(records)} registros, {errors} errores")
    print(f"[EXTRACT] Tipos de módulo únicos: {len(module_counter)}")

    with open(jsonl_path, "w", encoding="utf-8") as f:
        for rec in records:
            record_out = {k: v for k, v in rec.items() if k != "tree"}
            f.write(json.dumps(record_out, ensure_ascii=False) + "\n")

    with open(jsonl_path.parent / "dataset-full.jsonl", "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["module_tag", "count"])
        for tag, count in module_counter.most_common():
            w.writerow([tag, count])

    print(f"[EXTRACT] Escrito:")
    print(f"           {jsonl_path} ({len(records)} registros, sin árbol)")
    print(f"           {jsonl_path.parent / 'dataset-full.jsonl'} ({len(records)} registros, con árbol)")
    print(f"           {csv_path} ({len(module_counter)} tipos de módulo)")
    print(f"[EXTRACT] Tipos de módulo encontrados:")
    for tag, count in module_counter.most_common(30):
        print(f"           {tag:40s} {count:4d}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
