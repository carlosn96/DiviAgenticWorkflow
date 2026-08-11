"""
Split combined page exports into individual page definitions with section files.

Reads from: site/<DAW_SITE>/page-defs/temp/<slug>.json
Writes to:  site/<DAW_SITE>/page-defs/<slug>/
              manifest.json
              sections/<section-key>.json
              sections/css/<section-key>.css
"""

import json, os, re, sys

SITE_DIR = os.path.join(os.path.dirname(__file__), "..", "site")
DAW_SITE = os.environ.get("DAW_SITE", "lopezvelarde")
TEMP_DIR = os.path.join(SITE_DIR, DAW_SITE, "page-defs", "temp")
OUT_DIR = os.path.join(SITE_DIR, DAW_SITE, "page-defs")


def slugify(name):
    name = name.lower().strip()
    name = re.sub(r"[^\w\s-]", "", name)
    name = re.sub(r"[\s_]+", "-", name)
    name = re.sub(r"-+", "-", name)
    return name


def section_key(section, idx, existing_keys=None):
    if existing_keys is None:
        existing_keys = set()
    label = (
        section.get("meta", {})
        .get("adminLabel", {})
        .get("desktop", {})
        .get("value", "")
    )
    if label:
        base = slugify(label)
    else:
        mc = section.get("module_class", "")
        if mc:
            base = slugify(mc.split()[0])
        else:
            base = f"section-{idx}"

    # Ensure uniqueness
    key = base
    suffix = 1
    while key in existing_keys:
        key = f"{base}-{suffix}"
        suffix += 1
    existing_keys.add(key)
    return key


def split_page(filepath):
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    title = data.get("title", "Untitled")
    slug = data.get("slug", "untitled")
    sections = data.get("sections", [])

    page_dir = os.path.join(OUT_DIR, slug)
    sections_dir = os.path.join(page_dir, "sections")
    css_dir = os.path.join(sections_dir, "css")
    os.makedirs(css_dir, exist_ok=True)

    section_refs = []
    used_keys = set()
    for idx, section in enumerate(sections):
        key = section_key(section, idx, used_keys)
        section_file = f"sections/{key}.json"

        # Remove existing files first to avoid stale data
        sf_path = os.path.join(page_dir, section_file)
        if os.path.exists(sf_path):
            os.remove(sf_path)
        cf_path = os.path.join(css_dir, f"{key}.css")
        if os.path.exists(cf_path):
            os.remove(cf_path)
        section_refs.append(section_file)

        # Write section JSON
        with open(os.path.join(page_dir, section_file), "w", encoding="utf-8") as sf:
            json.dump(section, sf, indent=2, ensure_ascii=False)

        # Write empty CSS file (CSS lives in brand.css unless section-specific)
        css_path = os.path.join(css_dir, f"{key}.css")
        if not os.path.exists(css_path):
            with open(css_path, "w", encoding="utf-8") as cf:
                cf.write(f"/* {key} section styles */\n")

    # Write manifest
    manifest = {
        "_manifest": "v1",
        "title": title,
        "slug": slug,
        "sections": section_refs,
    }
    with open(os.path.join(page_dir, "manifest.json"), "w", encoding="utf-8") as mf:
        json.dump(manifest, mf, indent=2, ensure_ascii=False)

    print(f"  {slug}: {len(sections)} sections -> {page_dir}")
    return True


def main():
    if not os.path.isdir(TEMP_DIR):
        print(f"Temp dir not found: {TEMP_DIR}")
        sys.exit(1)

    files = sorted([f for f in os.listdir(TEMP_DIR) if f.endswith(".json")])
    print(f"Found {len(files)} page exports in {TEMP_DIR}")

    for fname in files:
        filepath = os.path.join(TEMP_DIR, fname)
        print(f"\nProcessing: {fname}")
        try:
            split_page(filepath)
        except Exception as e:
            print(f"  ERROR: {e}")

    print("\nDone.")


if __name__ == "__main__":
    main()
