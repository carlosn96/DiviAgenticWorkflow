"""
Inspect et_divi WordPress option and produce a structured JSON inventory.
Can run both locally (via wp.bat) and remotely (via wp-remote.ps1).

Usage:
    python inspect_et_divi.py --local                     # local WP
    python inspect_et_divi.py --remote                    # remote WP via wp-remote.ps1
    python inspect_et_divi.py --local --remote             # both, merged output
    python inspect_et_divi.py --file <path>                # from saved JSON file
"""

import json
import subprocess
import sys
import os
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT_DIR = os.path.join(ROOT, "DAW_bundle", "site", "lopezvelarde", "brand")
OUT_FILE = os.path.join(OUT_DIR, "et_divi-inventory.json")

SECTION_KEYS = {
    "fonts": [
        "heading_font", "heading_font_weight", "heading_font_size", "heading_font_style",
        "body_font", "body_font_weight", "body_font_size", "body_font_height", "body_font_style",
        "divi_google_fonts_inline",
    ],
    "colors": [
        "accent_color", "secondary_accent_color", "font_color", "header_color",
        "link_color", "sidebar_link_color",
    ],
    "buttons": [],
    "nav": [],
    "footer": [],
    "performance": [
        "divi_dynamic_module_framework", "divi_dynamic_icons", "divi_critical_css",
        "divi_defer_block_css", "divi_enable_jquery_body", "divi_disable_emojis",
    ],
}

SECTION_PREFIXES = {
    "buttons": "all_buttons_",
    "nav": ("nav_", "menu_", "primary_", "secondary_", "slide_", "fullscreen_",
            "fixed_", "mobile_", "vertical_", "dropdown_", "top_"),
    "footer": ("footer_", "custom_footer_"),
}


def classify_key(key):
    for section, prefixes in SECTION_PREFIXES.items():
        if isinstance(prefixes, str):
            if key.startswith(prefixes):
                return section
        else:
            for p in prefixes:
                if key.startswith(p):
                    return section
    return None


def extract_option(wp_cmd):
    """Run wp-cli command and parse the et_divi option."""
    try:
        result = subprocess.run(
            [*wp_cmd, "option", "get", "et_divi", "--format=json"],
            capture_output=True, text=True, timeout=30,
            shell=True if os.name == "nt" and wp_cmd[0].endswith(".bat") else False
        )
        if result.returncode != 0:
            print(f"Error: {result.stderr}", file=sys.stderr)
            return None
        data = json.loads(result.stdout)
        return data
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return None


def organize(data):
    """Organize raw et_divi option into sections."""
    organized = {"fonts": {}, "colors": {}, "buttons": {}, "nav": {},
                 "footer": {}, "performance": {}, "global_colors": [],
                 "other": {}}

    if not data:
        return organized

    # Explicit keys first
    for key in SECTION_KEYS["fonts"]:
        if key in data:
            organized["fonts"][key] = data[key]

    for key in SECTION_KEYS["colors"]:
        if key in data:
            organized["colors"][key] = data[key]

    for key in SECTION_KEYS["performance"]:
        if key in data:
            organized["performance"][key] = data[key]

    # Global colors
    gcs = data.get("global_colors", [])
    if isinstance(gcs, list):
        organized["global_colors"] = gcs

    # Classify remaining keys
    classified = set()
    for key in SECTION_PREFIXES["buttons"]:
        r = SECTION_PREFIXES["buttons"]
        if key.startswith(r):
            organized["buttons"][key] = data[key]
            classified.add(key)

    for key in data:
        if key in classified:
            continue
        section = classify_key(key)
        if section == "buttons":
            organized["buttons"][key] = data[key]
            classified.add(key)
        elif section == "nav":
            organized["nav"][key] = data[key]
            classified.add(key)
        elif section == "footer":
            organized["footer"][key] = data[key]
            classified.add(key)

    # Leftovers
    for key in data:
        if key not in classified and key not in SECTION_KEYS["fonts"] \
                and key not in SECTION_KEYS["colors"] \
                and key not in SECTION_KEYS["performance"] \
                and key != "global_colors":
            organized["other"][key] = data[key]

    return organized


def build_inventory(data, source_label):
    org = organize(data)
    return {
        "source": source_label,
        "date": str(date.today()),
        "total_keys": len(data) if data else 0,
        "sections": org,
        "_raw": data,
    }


def load_remote():
    ps = "powershell.exe"
    script = os.path.join(ROOT, "remote-scripts", "wp-remote.ps1")
    wp_cmd = [ps, "-ExecutionPolicy", "Bypass", "-File", script]
    return extract_option(wp_cmd)


def load_local():
    wp_cmd = [os.path.join(ROOT, "wp.bat")]
    return extract_option(wp_cmd)


def load_file(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if "_raw" in data:
        return data["_raw"]
    return data


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Inspect et_divi option")
    parser.add_argument("--local", action="store_true", help="Read from local WP")
    parser.add_argument("--remote", action="store_true", help="Read from remote WP via wp-remote.ps1")
    parser.add_argument("--file", help="Read from saved JSON file")
    parser.add_argument("--out", default=OUT_FILE, help=f"Output path (default: {OUT_FILE})")
    args = parser.parse_args()

    inventories = []

    if args.local:
        print("Reading local et_divi...", end=" ", flush=True)
        local_data = load_local()
        if local_data:
            inventories.append(build_inventory(local_data, "local"))
            print(f"{len(local_data)} keys")
        else:
            print("FAILED")

    if args.remote:
        print("Reading remote et_divi...", end=" ", flush=True)
        remote_data = load_remote()
        if remote_data:
            inventories.append(build_inventory(remote_data, "remote"))
            print(f"{len(remote_data)} keys")
        else:
            print("FAILED")

    if args.file:
        print(f"Reading from {args.file}...", end=" ", flush=True)
        file_data = load_file(args.file)
        if file_data:
            inventories.append(build_inventory(file_data, os.path.basename(args.file)))
            print(f"{len(file_data)} keys")
        else:
            print("FAILED")

    if not inventories:
        parser.print_help()
        sys.exit(1)

    # If only one source, output single object; if multiple, output array
    if len(inventories) == 1:
        output = inventories[0]
    else:
        output = inventories

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nWritten to: {args.out}")


if __name__ == "__main__":
    main()
