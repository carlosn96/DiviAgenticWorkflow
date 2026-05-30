#!/usr/bin/env python3
"""
Artefacto A: Section Pattern Library
Naturaleza: Estadística descriptiva
Algoritmo: Frecuencias + agregación por sección
Input: ml-dataset/dataset.jsonl (877 registros)
Output: artifacts/section-patterns.json

Para cada tipo de sección (hero, features, testimonials, etc.):
  - Frecuencia de estructuras de columna
  - Frecuencia de módulos usados
  - Secuencias típicas de módulos
  - Frecuencia de decoraciones (gradientes, divisores)
  - Padding/espaciado promedio
"""

import json, sys, re
from pathlib import Path
from collections import Counter, defaultdict

DAW_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DAW_ROOT / "workspace"))

DATASET_PATH = DAW_ROOT / "ml-dataset" / "dataset.jsonl"
CATALOG_DIR = DAW_ROOT / "workspace" / "catalog" / "jsons"

MODULE_CATEGORIES = {
    'et_pb_text': 'text', 'et_pb_heading': 'heading', 'et_pb_image': 'image',
    'et_pb_blurb': 'blurb', 'et_pb_button': 'button', 'et_pb_divider': 'divider',
    'et_pb_testimonial': 'testimonial', 'et_pb_slider': 'slider',
    'et_pb_number_counter': 'number-counter', 'et_pb_countdown_timer': 'countdown',
    'et_pb_pricing_tables': 'pricing', 'et_pb_pricing_table': 'pricing-table',
    'et_pb_accordion': 'accordion', 'et_pb_toggle': 'toggle', 'et_pb_tabs': 'tabs',
    'et_pb_video': 'video', 'et_pb_audio': 'audio', 'et_pb_map': 'map',
    'et_pb_signup': 'signup', 'et_pb_contact_form': 'contact-form',
    'et_pb_gallery': 'gallery', 'et_pb_portfolio': 'portfolio',
    'et_pb_blog': 'blog', 'et_pb_post_slider': 'post-slider',
    'et_pb_post_title': 'post-title', 'et_pb_team_member': 'team-member',
    'et_pb_social_media_follow': 'social-follow',
    'et_pb_social_media_follow_network': 'social-network',
    'et_pb_search': 'search', 'et_pb_code': 'code',
    'et_pb_fullwidth_slider': 'fullwidth-slider',
    'et_pb_fullwidth_header': 'fullwidth-header',
    'et_pb_circle_counter': 'circle-counter',
    'et_pb_filterable_portfolio': 'filterable-portfolio',
    'et_pb_shop': 'shop', 'et_pb_login': 'login', 'et_pb_menu': 'menu',
    'et_pb_icon': 'icon', 'et_pb_comments': 'comments', 'et_pb_sidebar': 'sidebar',
    'et_pb_fullwidth_menu': 'fullwidth-menu', 'et_pb_fullwidth_code': 'fullwidth-code',
    'et_pb_progress_bar': 'progress-bar',
    # Divi Plus modules
    'dipl_double_color_heading': 'double-heading', 'dipl_text_animator': 'text-animator',
    'dipl_button': 'dipl-button', 'dipl_button_item': 'dipl-button-item',
    'dipl_separator': 'separator', 'dipl_floating_image': 'floating-image',
    'dipl_floating_image_item': 'floating-image-item',
    'dipl_fancy_text': 'fancy-text', 'dipl_image_mask': 'image-mask',
    'dipl_image_mask_item': 'image-mask-item', 'dipl_tilt_image': 'tilt-image',
    'dipl_flipbox': 'flipbox', 'dipl_image_card': 'image-card',
    'dipl_timeline': 'timeline', 'dipl_timeline_item': 'timeline-item',
    'dipl_testimonial_slider': 'testimonial-slider',
    'dipl_content_toggle': 'content-toggle', 'dipl_pricing_table': 'dipl-pricing',
    'dipl_team_member': 'dipl-team', 'dipl_logo_slider': 'logo-slider',
    'dipl_breadcrumb': 'breadcrumb', 'dipl_modal_popup': 'modal-popup',
    'dipl_image_accordion': 'image-accordion',
    'dipl_image_hotspot': 'image-hotspot',
    'dipl_faq_schema': 'faq-schema',
    'dipl_woo_products_categories': 'woo-categories',
    'dipl_gravity_form_styler': 'gravity-form',
    'dipl_contact_form_7_styler': 'cf7-form',
    'dipl_caldera_form_styler': 'caldera-form',
    'dipl_wpforms_styler': 'wpforms',
}

SKIP = {'et_pb_section', 'et_pb_row', 'et_pb_row_inner', 'et_pb_column', 'et_pb_column_inner'}

COL_STRUCT_RE = re.compile(r'column_structure="([^"]+)"')
GRADIENT_RE = re.compile(r'use_background_color_gradient="on"')
DIVIDER_RE = re.compile(r'(?:top|bottom)_divider_style="[^"]+[^n][^o][^n][^e]"')
BG_IMAGE_RE = re.compile(r'background_image="https?://')
PADDING_RE = re.compile(r'custom_padding="([^"]+)"')


def extract_column_structures(raw_shortcode: str) -> list:
    return COL_STRUCT_RE.findall(raw_shortcode)


def has_gradient(raw: str) -> bool:
    return bool(GRADIENT_RE.search(raw))


def has_divider(raw: str) -> bool:
    return bool(DIVIDER_RE.search(raw))


def has_bg_image(raw: str) -> bool:
    return bool(BG_IMAGE_RE.search(raw))


def extract_paddings(raw: str) -> list:
    return PADDING_RE.findall(raw)


def main():
    print("[A] Section Pattern Library — extrayendo patrones...")

    records = []
    with open(DATASET_PATH, encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line))
    print(f"[A]  {len(records)} registros cargados")

    # Categorizar cada template
    by_category = defaultdict(list)
    cat_counts = Counter()
    raw_dir_map = {}

    for rec in records:
        folder_name = rec["source"]
        json_path = Path(rec["path"])
        raw_shortcode = rec.get("raw_shortcode", "")

        # Re-leer el shortcode completo para análisis (el dataset trunca a 5000)
        try:
            raw_data = json.loads(json_path.read_text("utf-8"))
            inner = raw_data.get("data", {})
            full_shortcode = ""
            for val in inner.values():
                if isinstance(val, str):
                    full_shortcode += val
        except Exception:
            full_shortcode = raw_shortcode

        info = extract_divi_info(full_shortcode, folder_name, str(json_path))
        section_type = categorize_section(folder_name, info)

        content_modules = [m["category"] for m in info.get("modules", [])
                           if m["tag"] not in SKIP]
        module_sequence = tuple(
            m["tag"] for m in info.get("modules", [])
            if m["tag"] not in SKIP
        )

        col_structs = extract_column_structures(full_shortcode)
        paddings = extract_paddings(full_shortcode)

        entry = {
            "source": folder_name,
            "section_type": section_type,
            "modules_raw": content_modules,
            "module_tags": [m["tag"] for m in info.get("modules", [])
                            if m["tag"] not in SKIP],
            "module_sequence": list(module_sequence),
            "column_structures": col_structs,
            "has_gradient": has_gradient(full_shortcode),
            "has_divider": has_divider(full_shortcode),
            "has_bg_image": has_bg_image(full_shortcode),
            "section_count": info.get("section_count", 0),
            "row_count": info.get("row_count", 0),
            "module_count": info.get("module_count", 0),
            "paddings": paddings,
        }
        by_category[section_type].append(entry)
        cat_counts[section_type] += 1

    print(f"\n[A]  Distribución por tipo de sección:")
    for cat, count in cat_counts.most_common():
        print(f"      {cat:20s} {count:4d} ({count/len(records)*100:5.1f}%)")

    # Construir patrones por categoría
    patterns = {}
    for section_type, entries in sorted(by_category.items()):
        total = len(entries)
        if total < 3:
            continue

        col_struct_counter = Counter()
        module_seq_counter = Counter()
        module_type_counter = Counter()
        gradient_count = 0
        divider_count = 0
        bg_image_count = 0
        row_counts = []
        module_counts = []

        for e in entries:
            col_struct_counter.update(e["column_structures"])
            module_seq_counter[tuple(e["module_sequence"])] += 1
            module_type_counter.update(e["module_tags"])
            if e["has_gradient"]:
                gradient_count += 1
            if e["has_divider"]:
                divider_count += 1
            if e["has_bg_image"]:
                bg_image_count += 1
            row_counts.append(e["row_count"])
            module_counts.append(e["module_count"])

        top_structures = [
            {"structure": s, "frequency": round(c / total, 3), "count": c}
            for s, c in col_struct_counter.most_common(8)
        ]
        top_modules = [
            {"module_tag": m, "frequency": round(c / total, 3), "count": c}
            for m, c in module_type_counter.most_common(15)
        ]
        top_sequences = [
            {"sequence": list(seq), "frequency": round(c / total, 3), "count": c}
            for seq, c in module_seq_counter.most_common(10)
        ]

        patterns[section_type] = {
            "total_samples": total,
            "column_structures": top_structures,
            "common_modules": top_modules,
            "common_sequences": top_sequences,
            "decorations": {
                "gradient_frequency": round(gradient_count / total, 3),
                "divider_frequency": round(divider_count / total, 3),
                "bg_image_frequency": round(bg_image_count / total, 3),
            },
            "avg_row_count": round(sum(row_counts) / total, 1),
            "avg_module_count": round(sum(module_counts) / total, 1),
        }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(patterns, f, indent=2, ensure_ascii=False)

    print(f"\n[A]  Escrito: {OUTPUT_PATH}")
    print(f"[A]  {len(patterns)} tipos de sección con patrones")
    return 0


if __name__ == "__main__":
    sys.exit(main())
