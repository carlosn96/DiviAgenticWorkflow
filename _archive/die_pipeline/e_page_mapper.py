#!/usr/bin/env python3
"""
e_page_mapper.py — Page Mapper v3.0

Convierte brief + DIE plans en page-def usando los 877 compiled sections
como templates estructurales. Inyecta contenido via {{slot:*}} tokens,
genera filas de items dinámicamente, aplica decoration blocks (E),
módulos complementarios (C), brand presets, animation chains.

v3.0:
  - Post-inyección: elimina módulos con contenido default del template no reemplazado
  - Post-inyección: añade módulos para campos del brief sin {{slot:*}} correspondiente
  - Garantiza que TODO el contenido del brief aparezca en el plan
  - Sin basura de template original (blurbs hardcodeados, imágenes default)
"""

import json, os, re, copy, sys
from pathlib import Path

SLOT_RE = re.compile(r'\{\{slot:([^}]+)\}\}')

ARTIFACTS_DIR = Path(__file__).resolve().parent
DAW_ROOT = ARTIFACTS_DIR.parent.parent
COMPILED_DIR = DAW_ROOT / "workspace" / "sections" / "catalog"
SCHEMA_PATH = DAW_ROOT / "workspace" / "section-schema.json"
MODULES_DIR = DAW_ROOT / "workspace" / "data" / "modules"

BRIEF_TEXT_FIELDS = {"title", "text", "eyebrow", "body",
                     "btn_primary_text", "btn_secondary_text",
                     "decorative_text", "media_attribution"}

MODULE_TEXT_KEYS = {"title", "content", "button_text", "alt"}

# ── Image Resolution ──────────────────────────────────────────────────────────

POSSIBLE_PLACEHOLDER_PATHS = [
    "app/public/wp-content/uploads/placeholder.png",
    "wp-content/uploads/placeholder.png",
]

_PLACEHOLDER_SRC = None


def resolve_image_src(src, fallback_text="Aletheia Institute"):
    """Apply the image placeholder hierarchy.

    1. If src is a valid non-empty URL/path, return it.
    2. If a local placeholder.png exists, return its URL.
    3. Fall back to a generic online placeholder with brand colors and label.
    4. If all else fails, return empty string.
    """
    global _PLACEHOLDER_SRC
    if src and isinstance(src, str) and src.strip():
        stripped = src.strip()
        if stripped.startswith("http") or stripped.startswith("/"):
            return stripped
        return stripped

    if _PLACEHOLDER_SRC is None:
        for candidate in POSSIBLE_PLACEHOLDER_PATHS:
            if Path(candidate).exists():
                _PLACEHOLDER_SRC = f"/{candidate}" if not candidate.startswith("/") else candidate
                break
            alt_path = DAW_ROOT.parent / candidate if not Path(candidate).is_absolute() else Path(candidate)
            if alt_path.exists():
                _PLACEHOLDER_SRC = f"/{candidate}" if not candidate.startswith("/") else candidate
                break
            if _PLACEHOLDER_SRC is None:
                label = fallback_text.replace(" ", "+")[:40]
                accent_hex = "123E7A"
                text_hex = "F8FAF8"
                try:
                    daw_site = os.environ.get("DAW_SITE", "")
                    if not daw_site:
                        raise RuntimeError("DAW_SITE not set — cannot resolve placeholder colors")
                    brand_file = DAW_ROOT / "site" / daw_site / "brand" / "_design_vars.json"
                    if brand_file.exists():
                        import json as _json
                        bv = _json.loads(brand_file.read_text("utf-8"))
                        accent_hex = (bv.get("color_surface_deep", "123E7A")).lstrip("#")
                        text_hex = (bv.get("color_text_on_dark", "F8FAF8")).lstrip("#")
                except Exception:
                    pass
                _PLACEHOLDER_SRC = (
                    f"https://placehold.co/800x600/{accent_hex}/{text_hex}"
                    f"?text={label}"
                )

    return _PLACEHOLDER_SRC


# ── Helpers ──────────────────────────────────────────────────────────────────

def _load_schema():
    if SCHEMA_PATH.exists():
        return json.loads(SCHEMA_PATH.read_text("utf-8"))
    return {}

def _load_template(name):
    if not name:
        return None
    for ext in (".section.json", ".json"):
        p = COMPILED_DIR / f"{name}{ext}"
        if p.exists():
            return json.loads(p.read_text("utf-8"))
    return None

def _walk(obj, fn):
    if isinstance(obj, str):
        return fn(obj)
    elif isinstance(obj, dict):
        return {k: _walk(v, fn) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_walk(i, fn) for i in obj]
    return obj

def _collect_strings(obj, keys=None):
    """Collect all string values in nested JSON, optionally filtering by keys."""
    strings = set()
    if isinstance(obj, str):
        strings.add(obj)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if keys is None or k in keys:
                if isinstance(v, str):
                    strings.add(v)
            strings.update(_collect_strings(v, keys))
    elif isinstance(obj, list):
        for i in obj:
            strings.update(_collect_strings(i, keys))
    return strings

def _find_slot_keys_in_template(template):
    """Return set of {{slot:key}} keys that exist in the template JSON."""
    raw = json.dumps(template)
    return set(SLOT_RE.findall(raw))


# ── Slot Injection ───────────────────────────────────────────────────────────

def _inject_slots(template, slot_map):
    """Replace all {{slot:key}} tokens with values from slot_map."""
    def _repl(val):
        def _sub(m):
            return str(slot_map.get(m.group(1), ""))
        return SLOT_RE.sub(_sub, val)
    return _walk(template, _repl)


# ── Clean Template Garbage ──────────────────────────────────────────────────

def _collect_brief_values(section_def, slot_map):
    """Collect all textual values from the brief section (including slot_map, arrays)."""
    values = set()
    for v in slot_map.values():
        if v:
            values.add(v.strip())
    for k in BRIEF_TEXT_FIELDS:
        v = section_def.get(k)
        if v and isinstance(v, str):
            values.add(v.strip())
    for k in ("features", "testimonials", "stats", "logos", "items"):
        items = section_def.get(k, [])
        for item in items:
            if isinstance(item, dict):
                for iv in item.values():
                    if isinstance(iv, str) and iv.strip():
                        values.add(iv.strip())
    return values


def _all_module_texts_belong(mod, brief_values):
    """Check if ALL non-empty text content in a module matches the brief.

    A module is kept only if every text key (title, content, button_text, alt)
    either is empty or matches a brief value. Partial matches (e.g. correct
    title but hardcoded template content) cause the module to be removed.
    """
    from difflib import SequenceMatcher
    for key in MODULE_TEXT_KEYS:
        val = mod.get(key, "")
        if not isinstance(val, str) or not val.strip():
            continue
        val_stripped = val.strip()
        if val_stripped in brief_values:
            continue
        # Check fuzzy match (90%+ similarity)
        matched = False
        for brief_val in brief_values:
            if len(val_stripped) > 15 and len(brief_val) > 15:
                ratio = SequenceMatcher(None, val_stripped.lower(), brief_val.lower()).ratio()
                if ratio >= 0.85:
                    matched = True
                    break
        if not matched:
            return False
    return True


def _clean_template_garbage(section, brief_values):
    """Remove modules whose textual content is not from the brief.

    A module survives only if ALL its MODULE_TEXT_KEYS values match
    brief content (exact or fuzzy >= 85%). Structural modules with no
    text content at all are kept.

    Container modules (row-inner) are recursively cleaned:
    their child modules are checked individually, not just the container itself.
    Empty containers (all children removed) are also removed.
    """
    CONTAINER_TYPES = {"divi/row-inner", "divi/row"}

    def _clean_modules(modules):
        kept = []
        # Modules that should be preserved for structural/decorative reasons
        DECORATIVE_TYPES = {"divi/image", "divi/divider", "divi/icon", "divi/number-counter", "divi/code", "divi/button", "divi/social-media-follow"}
        
        for mod in modules:
            mod_type = mod.get("type", "")
            # Recurse into container modules
            if mod_type in CONTAINER_TYPES and "columns" in mod:
                mod["columns"] = _clean_columns(mod.get("columns", []))
                # Remove container if all its columns are now empty
                has_modules = any(
                    cm.get("modules", []) for cm in mod.get("columns", [])
                )
                if has_modules:
                    kept.append(mod)
                continue
            
            # Preserve structural modules
            if mod_type in DECORATIVE_TYPES:
                kept.append(mod)
                continue

            mod_texts = _collect_strings(mod, keys=MODULE_TEXT_KEYS)
            mod_texts.discard("")
            if not mod_texts:
                kept.append(mod)
                continue
            if _all_module_texts_belong(mod, brief_values):
                kept.append(mod)
        return kept

    def _clean_columns(columns):
        cleaned = []
        for col in columns:
            mods = col.get("modules", [])
            col["modules"] = _clean_modules(mods) if mods else []
            cleaned.append(col)
        return cleaned

    cleaned_rows = []
    for row in section.get("rows", []):
        cleaned_cols = _clean_columns(row.get("columns", []))
        if cleaned_cols:
            row["columns"] = cleaned_cols
            cleaned_rows.append(row)
    section["rows"] = cleaned_rows
    return section


# ── Fill Missing Fields ─────────────────────────────────────────────────────

_MODULE_BUILDERS = {
    "title":       {"type": "divi/heading", "level": "h2"},
    "eyebrow":     {"type": "divi/text"},
    "text":        {"type": "divi/text"},
    "body":        {"type": "divi/text"},
    "btn_primary_text":   {"type": "divi/button"},
    "btn_secondary_text": {"type": "divi/button"},
    "btn_primary_url":    {"type": "divi/button"},
    "btn_secondary_url":  {"type": "divi/button"},
    "decorative_text":    {"type": "divi/text"},
    "image":       {"type": "divi/image"},
}

_SLOT_TO_MOD_FIELD = {
    "title": "content",
    "eyebrow": "content",
    "text": "content",
    "body": "content",
    "btn_primary_text": "button_text",
    "btn_secondary_text": "button_text",
    "btn_primary_url": "button_url",
    "btn_secondary_url": "button_url",
    "decorative_text": "content",
    "image": "src",
}


def _value_already_in_section(section, value):
    """Check if a text value already appears in any module of the section.

    Recurses into container modules (row-inner) to find nested content.
    """
    if not value or not isinstance(value, str):
        return False
    value_stripped = value.strip()
    if not value_stripped:
        return False

    CONTAINER_TYPES = {"divi/row-inner", "divi/row"}

    def _check_modules(modules):
        for mod in modules:
            mod_type = mod.get("type", "")
            if mod_type in CONTAINER_TYPES and "columns" in mod:
                for child_col in mod.get("columns", []):
                    if _check_modules(child_col.get("modules", [])):
                        return True
            for key in MODULE_TEXT_KEYS:
                existing = mod.get(key, "")
                if isinstance(existing, str) and value_stripped in existing:
                    return True
        return False

    for row in section.get("rows", []):
        for col in row.get("columns", []):
            if _check_modules(col.get("modules", [])):
                return True
    return False


_VALID_COLUMN_TYPES = {"4_4", "1_2", "1_3", "1_4", "2_3", "3_4", "1_1"}


def _fill_missing_fields(section, section_def, slot_map, template_slot_keys):
    """Add modules for brief fields that have no {{slot:*}} in the template.

    Modules are appended (not prepended) to maintain eyebrow → title → text → button order.
    If no suitable column exists, a new 4_4 row is created.
    """
    builder_base = _MODULE_BUILDERS
    slot_to_field = _SLOT_TO_MOD_FIELD

    # Build ordered list of fields to preserve visual hierarchy
    ordered_keys = [k for k in ["eyebrow", "title", "text", "body",
                                 "decorative_text", "image",
                                 "btn_primary_text", "btn_primary_url",
                                 "btn_secondary_text", "btn_secondary_url"]
                    if k in slot_map]

    for key in ordered_keys:
        val = slot_map[key]
        if not val:
            continue
        if key in template_slot_keys:
            continue
        if _value_already_in_section(section, str(val)):
            continue
        builder = builder_base.get(key)
        if not builder:
            continue
        mod = dict(builder)
        field = slot_to_field.get(key)
        if field:
            mod[field] = str(val)

        rows = section.get("rows", [])
        placed = False
        for row in rows:
            cols = row.get("columns", [])
            for col in cols:
                col_type = col.get("type", "")
                if col_type in _VALID_COLUMN_TYPES:
                    col.setdefault("modules", [])
                    col["modules"].append(mod)
                    placed = True
                    break
            if placed:
                break
        if not placed:
            rows.append({
                "column_structure": "4_4",
                "columns": [{"type": "4_4", "modules": [mod]}]
            })

    return section


# ── Placeholder Cleanup ─────────────────────────────────────────────────────

def _clean_placeholders(section):
    cleaned_rows = []
    for row in section.get("rows", []):
        cleaned_cols = []
        for col in row.get("columns", []):
            mods = [m for m in col.get("modules", [])
                    if m.get("type") != "divi/placeholder"]
            if mods:
                col["modules"] = mods
                cleaned_cols.append(col)
        if cleaned_cols:
            row["columns"] = cleaned_cols
            cleaned_rows.append(row)
    section["rows"] = cleaned_rows
    return section


def _module_count(section):
    count = 0
    for row in section.get("rows", []):
        for col in row.get("columns", []):
            for m in col.get("modules", []):
                if m.get("type") != "divi/placeholder":
                    count += 1
    return count


# ── Slot Map ─────────────────────────────────────────────────────────────────

def _build_slot_map(section_def, schema):
    st = section_def.get("section_type", "generic")
    entry = schema.get(st, {})
    sfields = entry.get("section_fields", [])
    fallback = ["title", "text", "eyebrow", "body",
                "btn_primary_text", "btn_primary_url",
                "btn_secondary_text", "btn_secondary_url",
                "decorative_text", "decorative_icon", "decorative_attribution",
                "media_icon", "media_attribution"]

    slots = {}
    fields = sfields or fallback
    for key in fields:
        val = section_def.get(key, section_def.get("slots", {}).get(key, ""))
        if val:
            slots[key] = str(val)

    for key in section_def:
        if key not in ("section_type", "tone", "product_type", "slots",
                       "features", "testimonials", "stats", "logos", "items"):
            if not isinstance(section_def[key], (list, dict)):
                slots[key] = str(section_def[key])

    item_fields = entry.get("item_fields", {})
    for array_name, fields in item_fields.items():
        items = section_def.get(array_name, section_def.get("slots", {}).get(array_name, []))
        if not items:
            continue
        for i, item in enumerate(items):
            if isinstance(item, dict):
                for field in fields:
                    val = item.get(field, "")
                    if val:
                        slots[f"{array_name}[{i}].{field}"] = str(val)

    return slots


# ── Item Rows ────────────────────────────────────────────────────────────────

ITEM_TEMPLATES = {
    "features": {
        "col_structure": "1_3,1_3,1_3",
        "mod_type": "divi/blurb",
        "presets": ["module:feature-card", "transform:hover-lift"],
        "mapping": {"title": "title", "icon": "icon", "text": "content"},
    },
    "testimonials": {
        "col_structure": "1_2,1_2",
        "mod_type": "divi/testimonial",
        "presets": ["module:testimonial-card", "transform:hover-glow"],
        "mapping": {"text": "content", "name": "author", "role": "jobTitle"},
    },
    "stats": {
        "col_structure": "1_4,1_4,1_4,1_4",
        "mod_type": "divi/number-counter",
        "presets": ["module:stat-item", "transform:hover-scale"],
        "mapping": {"number": "number", "title": "title", "label": "title"},
    },
    "logos": {
        "col_structure": "1_4,1_4,1_4,1_4",
        "mod_type": "divi/image",
        "presets": ["module:image-shadow", "transform:hover-scale"],
        "mapping": {"icon": "src", "name": "alt", "url": "link_url"},
    },
    "items": {
        "col_structure": "1_3,1_3,1_3",
        "mod_type": "divi/blurb",
        "presets": ["module:feature-card", "transform:hover-lift"],
        "mapping": {"title": "title", "icon": "icon", "text": "content"},
    },
}

def _build_item_rows(section_def, section_type=None):
    rows = []
    for array_name, tmpl in ITEM_TEMPLATES.items():
        items = section_def.get(array_name, section_def.get("slots", {}).get(array_name, []))
        if not items:
            continue

        col_parts = tmpl["col_structure"].split(",")
        ncols = len(col_parts)
        modules = []
        for item in items[:8]:
            mod = {"type": tmpl["mod_type"], "presets": list(tmpl["presets"])}
            for src_field, dst_field in tmpl["mapping"].items():
                val = item.get(src_field, "")
                if val:
                    if dst_field == "content":
                        if section_type == "timeline" and src_field == "text":
                            year = item.get("year", "")
                            if year:
                                mod["content"] = f"<h3>{year}</h3><p>{val}</p>"
                            else:
                                mod["content"] = f"<p>{val}</p>"
                        else:
                            mod["content"] = f"<p>{val}</p>"
                    elif dst_field in ("icon", "imageIcon"):
                        mod["icon"] = val
                    elif dst_field == "src":
                        mod[dst_field] = resolve_image_src(val, item.get("name", item.get("title", "Logo")))
                    else:
                        mod[dst_field] = val
            modules.append(mod)

        if not modules:
            continue

        if len(modules) > 8:
            print(f"[MAPPER] Warning: {array_name} has {len(modules)} items, "
                  f"capping at 8", file=sys.stderr)

        for i in range(0, len(modules), ncols):
            chunk = modules[i:i + ncols]
            row_cols = []
            for j, cp in enumerate(col_parts):
                if j < len(chunk):
                    row_cols.append({"type": cp, "modules": [chunk[j]]})
            if row_cols:
                rows.append({
                    "column_structure": tmpl["col_structure"],
                    "columns": row_cols,
                })

    return rows


# ── Animations ───────────────────────────────────────────────────────────────

SECTION_ANIMATION_MAP = {
    "hero":               {"style": "slide", "direction": "bottom", "duration": "800ms", "startingOpacity": "0%", "speedCurve": "ease-out"},
    "hero-centered":      {"style": "fade",  "duration": "1000ms", "speedCurve": "ease-out"},
    "hero-image":         {"style": "fade",  "duration": "1000ms", "startingOpacity": "0%", "speedCurve": "ease-out"},
    "features":           {"style": "slide", "direction": "bottom", "duration": "480ms", "intensity": {"slide": "10%"}, "speedCurve": "ease-out"},
    "content":            {"style": "fade",  "duration": "600ms", "speedCurve": "ease-out"},
    "content-list":       {"style": "slide", "direction": "bottom", "duration": "480ms", "speedCurve": "ease-out"},
    "stats":              {"style": "fade",  "duration": "800ms", "startingOpacity": "0%", "speedCurve": "ease-out"},
    "testimonials":       {"style": "fade",  "duration": "800ms", "speedCurve": "ease-out"},
    "logos":              {"style": "fade",  "duration": "600ms", "startingOpacity": "0%", "speedCurve": "ease-out"},
    "cta":                {"style": "zoom",  "duration": "800ms", "startingOpacity": "0%", "speedCurve": "ease-out"},
    "faq":                {"style": "fade",  "duration": "600ms", "speedCurve": "ease-out"},
    "gallery":            {"style": "slide", "direction": "bottom", "duration": "600ms", "speedCurve": "ease-out"},
    "contact":            {"style": "fade",  "duration": "600ms", "speedCurve": "ease-out"},
    "team":               {"style": "slide", "direction": "bottom", "duration": "480ms", "speedCurve": "ease-out"},
    "timeline":           {"style": "slide", "direction": "bottom", "duration": "800ms", "startingOpacity": "0%", "speedCurve": "ease-out"},
    "generic":            {"style": "fade",  "duration": "600ms", "speedCurve": "ease-out"},
}


def _dedup_section_content(section):
    """Remove duplicate modules from the same column that share identical text content.

    When a template has a hardcoded heading AND a slot-injected module ends up
    with the same content, the duplicate (second occurrence) is removed.
    Works recursively inside container modules (row-inner).
    """
    CONTAINER_TYPES = {"divi/row-inner", "divi/row"}

    def _text_signature(mod):
        parts = []
        for key in sorted(MODULE_TEXT_KEYS):
            val = mod.get(key, "")
            if isinstance(val, str):
                parts.append(val.strip().lower())
        return "|".join(parts)

    def _dedup_modules(modules):
        seen = set()
        kept = []
        for mod in modules:
            mod_type = mod.get("type", "")
            if mod_type in CONTAINER_TYPES and "columns" in mod:
                mod["columns"] = _dedup_columns(mod.get("columns", []))
                kept.append(mod)
                continue
            sig = _text_signature(mod)
            if sig and sig in seen:
                continue
            if sig:
                seen.add(sig)
            kept.append(mod)
        return kept

    def _dedup_columns(columns):
        for col in columns:
            mods = col.get("modules", [])
            if mods:
                col["modules"] = _dedup_modules(mods)
        return columns

    for row in section.get("rows", []):
        row["columns"] = _dedup_columns(row.get("columns", []))
    return section


def _add_animations(section, base_delay=0, section_type="generic"):
    idx = 0
    anim_config = SECTION_ANIMATION_MAP.get(section_type, SECTION_ANIMATION_MAP["generic"])

    # Leer animation_profile del decoration de sección (seteado por design_director.py)
    # para determinar delay_step dinámico basado en estilo
    sec_deco = section.get("decoration", {})
    anim_profile = sec_deco.get("_animation_profile", {})
    delay_step = anim_profile.get("delay_step_ms", 150)

    for row in section.get("rows", []):
        for col in row.get("columns", []):
            for mod in col.get("modules", []):
                if mod.get("type") == "divi/placeholder":
                    continue
                delay = delay_step * idx
                deco = mod.get("decoration", {})
                existing_anim = deco.get("animation")
                if existing_anim:
                    idx += 1
                    continue
                anim_value = dict(anim_config)
                anim_value["delay"] = f"{delay}ms"
                deco["animation"] = {
                    "desktop": {"value": anim_value}
                }
                mod["decoration"] = deco
                idx += 1


SECTION_SCROLL_MAP = {
    "hero":               "scroll:parallax-up",
    "hero-centered":      "scroll:parallax-up",
    "hero-image":         "scroll:parallax-up",
    "features":           "scroll:scale-in",
    "testimonials":       "scroll:reveal",
    "stats":              "scroll:fade-in",
    "cta":                "scroll:scale-in",
    "contact":            "scroll:fade-in",
    "faq":                "scroll:fade-in",
    "content":            "scroll:fade-in",
    "content-list":       "scroll:fade-in",
    "logos":              "scroll:fade-in",
    "gallery":            "scroll:scale-in",
    "team":               "scroll:fade-in",
    "timeline":           "scroll:reveal",
}

_LOADED_PRESETS_CACHE = {}


def _load_all_presets():
    if _LOADED_PRESETS_CACHE:
        return _LOADED_PRESETS_CACHE
    daw_site = os.environ.get('DAW_SITE', '').strip()
    if not daw_site:
        raise RuntimeError(
            "[ERROR] DAW_SITE no está definido. "
            "Debes configurar una marca antes de ejecutar e_page_mapper.py.\n"
            "  Edita .env en la raíz del proyecto y añade: DAW_SITE=nombre-de-tu-marca"
        )
    presets_path = DAW_ROOT / "site" / daw_site / "brand" / "_design_presets.json"
    if not presets_path.exists():
        return {}
    try:
        _LOADED_PRESETS_CACHE.update(json.loads(presets_path.read_text("utf-8")))
    except Exception:
        pass
    return _LOADED_PRESETS_CACHE


def _load_scroll_presets():
    return _load_all_presets().get("scroll", {})


# ── Main Section Builder ─────────────────────────────────────────────────────

def _apply_typography_to_module(mod, scale, role="body"):
    """Apply typography scale tokens to a module's font settings."""
    if not scale:
        return
    body_sizes = scale.get("body", {}).get("sizes", {})
    display_sizes = scale.get("display", {}).get("sizes", {})

    # Determine role from module type
    mod_type = mod.get("type", "")
    if mod_type == "divi/text":
        content = mod.get("content", "")
        if content and any(tag in content for tag in ("<h1>", "<h2>", "<display")):
            role = "display"
    elif mod_type == "divi/heading":
        role = "display"

    sizes = display_sizes if role == "display" else body_sizes
    if not sizes:
        return

    deco = mod.setdefault("decoration", {})
    body_font = deco.setdefault("bodyFont", {})
    bf_desktop = body_font.setdefault("desktop", {})
    bf_value = bf_desktop.setdefault("value", {})

    # Set font size based on role—use first available size key
    size_key = list(sizes.keys())[0] if sizes else "body"
    if role == "display":
        size_key = "display-xl" if "display-xl" in sizes else "h1"
    elif role == "eyebrow":
        size_key = "eyebrow"

    size_val = sizes.get(size_key)
    if size_val:
        bf_value["fontFamily"] = scale.get("display" if role == "display" else "body", {}).get("fontFamily")
        if "size" not in bf_value:
            bf_value["size"] = size_val
        if role == "eyebrow":
            eb = scale.get("eyebrow", {})
            if eb.get("letterSpacing") and "letterSpacing" not in bf_value:
                bf_value["letterSpacing"] = eb["letterSpacing"]
            if eb.get("textTransform") and "textTransform" not in bf_value:
                bf_value["textTransform"] = eb["textTransform"]

    head_font = deco.setdefault("headingFont", {})
    hf_desktop = head_font.setdefault("desktop", {})
    hf_value = hf_desktop.setdefault("value", {})
    if role == "display" and "fontFamily" not in hf_value:
        hf_value["fontFamily"] = scale.get("display", {}).get("fontFamily")


def _apply_typography_to_section(section, typo_scale):
    """Apply typography scale to all text modules in a section."""
    if not typo_scale:
        return
    for row in section.get("rows", []):
        for col in row.get("columns", []):
            for mod in col.get("modules", []):
                mod_type = mod.get("type", "")
                content = mod.get("content", "")
                if mod_type == "divi/text":
                    if content and ("<h" in content or "<display" in content):
                        _apply_typography_to_module(mod, typo_scale, "display")
                    elif mod.get("eyebrow") or content.startswith("<"):
                        _apply_typography_to_module(mod, typo_scale, "eyebrow")
                    else:
                        _apply_typography_to_module(mod, typo_scale, "body")
                elif mod_type == "divi/heading":
                    _apply_typography_to_module(mod, typo_scale, "display")
                elif mod_type == "divi/button":
                    _apply_typography_to_module(mod, typo_scale, "body")
                elif mod_type == "divi/blurb":
                    _apply_typography_to_module(mod, typo_scale, "body")
                elif mod_type == "divi/testimonial":
                    _apply_typography_to_module(mod, typo_scale, "body")


def process_section(section_def, decoration=None, section_index=0,
                    template_name=None, schema=None, variant_name=None,
                    typo_scale=None, plan_presets=None,
                    style_module_presets=None):
    schema = schema or _load_schema()
    st = section_def.get("section_type", "generic")
    entry = schema.get(st, {})

    slot_map = _build_slot_map(section_def, schema)

    template = _load_template(template_name)
    if not template:
        template = {"rows": []}

    template_slot_keys = _find_slot_keys_in_template(template)

    section = _inject_slots(copy.deepcopy(template), slot_map)

    section = _clean_placeholders(section)

    brief_values = _collect_brief_values(section_def, slot_map)
    section = _clean_template_garbage(section, brief_values)

    section = _fill_missing_fields(section, section_def, slot_map, template_slot_keys)

    section = _dedup_section_content(section)

    item_rows = _build_item_rows(section_def, section_type=st)
    if item_rows:
        section["rows"].extend(item_rows)

    # Preset from DIE plan (includes page composition rhythm)
    if plan_presets:
        section["presets"] = section.get("presets", []) + plan_presets
    else:
        presets = entry.get("presets", [])
        if not presets and st in SECTION_PRESET_FALLBACK:
            presets = [SECTION_PRESET_FALLBACK[st]]
        if presets:
            existing = section.get("presets", [])
            section["presets"] = existing + presets[:1]

    # Style-driven module presets (from design_inspiration)
    if style_module_presets:
        for row in section.get("rows", []):
            for col in row.get("columns", []):
                for mod in col.get("modules", []):
                    mt = mod.get("type", "")
                    if mt in style_module_presets:
                        extra_presets = style_module_presets[mt]
                        existing = mod.get("presets")
                        if existing is None:
                            existing = []
                        mod["presets"] = existing + [
                            p for p in extra_presets if p not in existing
                        ]

    if decoration and isinstance(decoration, dict):
        existing_deco = section.get("decoration", {})
        merged = {**decoration}
        merged.update(existing_deco)
        if merged:
            section["decoration"] = merged

    sec_deco = section.setdefault("decoration", {})
    existing_scroll = sec_deco.get("scroll", {})

    # Check for style-driven scroll intensity
    style_intensity = None
    if isinstance(existing_scroll, dict):
        sv = existing_scroll.get("desktop", {}).get("value", {})
        style_intensity = sv.get("_intensity")

    if style_intensity:
        # Map style intensity to scroll preset
        scroll_intensity_map = {
            "heavy": "scroll:parallax-up",
            "medium": "scroll:fade-in",
            "light": "scroll:fade-in",
        }
        scroll_name = scroll_intensity_map.get(style_intensity)
    else:
        scroll_name = SECTION_SCROLL_MAP.get(st)

    if scroll_name and (not existing_scroll or style_intensity):
        scroll_presets = _load_scroll_presets()
        _, scroll_key = scroll_name.split(":", 1)
        scroll_data = scroll_presets.get(scroll_key, {})
        if scroll_data:
            if style_intensity:
                # Remove _intensity marker, apply actual preset
                sec_deco.pop("scroll", None)
            sec_deco.update(copy.deepcopy(scroll_data.get("decoration", {})))

    _add_animations(section, section_index * 600, st)

    # Apply typography scale
    if typo_scale:
        _apply_typography_to_section(section, typo_scale)

    # Strip internal hints from decoration (not for final output)
    sec_deco = section.get("decoration", {})
    for internal_key in ("_animation_profile",):
        sec_deco.pop(internal_key, None)

    return section


SECTION_PRESET_FALLBACK = {
    "hero": "section:hero-dark",
    "hero-centered": "section:hero-dark",
    "features": "section:light",
    "content": "section:light",
    "content-list": "section:light",
    "stats": "section:trust-bar",
    "testimonials": "section:light",
    "logos": "section:light",
    "cta": "section:cta-epic",
    "generic": "section:light",
}


# ── Page Builder ─────────────────────────────────────────────────────────────

DIVIDER_PAIRS = {
    "hero": {"position": "bottom", "divider": "curve-bottom"},
    "hero-centered": {"position": "bottom", "divider": "curve-bottom"},
    "hero-image": {"position": "bottom", "divider": "curve-bottom"},
}

PRE_CTA_DIVIDER = {"position": "top", "divider": "curve-top"}


def _apply_shape_divider(section, position, divider_name):
    all_presets = _load_all_presets()
    divider_presets = all_presets.get("divider", {})
    divider_data = divider_presets.get(divider_name, {})
    if not divider_data:
        return
    sec_deco = section.setdefault("decoration", {})
    sd_key = "shapeDivider"
    if position == "bottom":
        existing = sec_deco.get(sd_key, {}).get("bottom")
    else:
        existing = sec_deco.get(sd_key, {}).get("top")
    if existing:
        return
    src = copy.deepcopy(divider_data.get("decoration", {}).get(sd_key, {}))
    if src:
        if sd_key not in sec_deco:
            sec_deco[sd_key] = {}
        sec_deco[sd_key].update(src)


_HOVER_PRESETS = {
    "transform:hover-lift", "transform:hover-scale",
    "transform:hover-glow", "transform:hover-slide-up",
    "transform:hover-expand",
}


def _add_ux_micro_interactions(section):
    for row in section.get("rows", []):
        for col in row.get("columns", []):
            for mod in col.get("modules", []):
                mod_type = mod.get("type", "")
                if mod_type == "divi/placeholder":
                    continue
                has_hover = any(p in _HOVER_PRESETS for p in mod.get("presets", []))
                if not has_hover and mod_type in ("divi/button", "divi/image"):
                    has_hover = True
                if has_hover:
                    mod["className"] = mod.get("className", "") + " cursor-pointer"
                    if not mod.get("decoration"):
                        mod["decoration"] = {}
                    decorate = mod.setdefault("decoration", {})
                    et = decorate.setdefault("transition", {})
                    et["desktop"] = et.get("desktop", {"value": {}})
                    ev = et["desktop"]["value"]
                    if "transition" not in ev:
                        ev["transition"] = "all 300ms ease-out"


def build_page_def(brief, plans, brand_vars=None, brand_presets=None):
    schema = _load_schema()
    sections = []
    section_types = []

    for i, sec_def in enumerate(brief.get("sections", [])):
        plan = plans[i] if i < len(plans) else {}
        st = sec_def.get("section_type", "generic")
        section_types.append(st)
        variant_name = plan.get("variant") if plan else None
        typo_scale = plan.get("_typography_scale") if plan else None
        plan_presets = plan.get("presets", []) if plan else None

        style_module_presets = plan.get("_style_module_presets", {}) if plan else {}
        section = process_section(
            section_def=sec_def,
            decoration=plan.get("decoration", {}),
            section_index=i,
            template_name=plan.get("template"),
            schema=schema,
            variant_name=variant_name,
            typo_scale=typo_scale,
            plan_presets=plan_presets,
            style_module_presets=style_module_presets,
        )
        sections.append(section)

    for i in range(len(sections)):
        st = section_types[i]
        pair = DIVIDER_PAIRS.get(st)
        if pair and i < len(sections) - 1:
            _apply_shape_divider(sections[i], pair["position"], pair["divider"])
        next_st = section_types[i + 1] if i + 1 < len(section_types) else None
        if next_st == "cta":
            _apply_shape_divider(sections[i + 1], PRE_CTA_DIVIDER["position"], PRE_CTA_DIVIDER["divider"])

    for section in sections:
        _add_ux_micro_interactions(section)

    return {
        "title": brief.get("title", ""),
        "slug": brief.get("slug", "page"),
        "description": brief.get("description", ""),
        "sections": sections,
    }
