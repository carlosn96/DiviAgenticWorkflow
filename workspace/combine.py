#!/usr/bin/env python
"""
combine.py — Combine manifest + section JSONs into a single page-def.

Usage:
    python combine.py manifest.json > output.json
    python combine.py manifest.json --out output.json

Manifest format:
    {
        "_manifest": "v1",
        "title": "Page Title",
        "slug": "page-slug",
        "sections": ["sections/hero.json", "sections/services.json"]
    }

Each section file contains one section definition (a JSON object).
Section paths are resolved relative to the manifest file's directory.
"""

import json
import os
import sys
import argparse


def combine(manifest_path: str) -> dict:
    manifest_dir = os.path.dirname(os.path.abspath(manifest_path))

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    title = manifest.get("title", "Page")
    slug = manifest.get("slug", "page")
    description = manifest.get("description", "")
    section_paths = manifest.get("sections", [])

    sections = []
    for rel_path in section_paths:
        abs_path = os.path.join(manifest_dir, rel_path)
        if not os.path.exists(abs_path):
            print(f"Warning: section file not found: {abs_path}", file=sys.stderr)
            continue
        with open(abs_path, "r", encoding="utf-8") as f:
            section = json.load(f)
        sections.append(section)

    result = {
        "title": title,
        "slug": slug,
    }
    if description:
        result["description"] = description
    result["sections"] = sections

    return result


def main():
    parser = argparse.ArgumentParser(description="Combine manifest + section JSONs")
    parser.add_argument("manifest", help="Path to the manifest JSON file")
    parser.add_argument("--out", "-o", help="Output file path (default: stdout)")
    args = parser.parse_args()

    result = combine(args.manifest)
    output = json.dumps(result, indent=2, ensure_ascii=False)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(output)
            f.write("\n")
    else:
        sys.stdout.write(output)
        sys.stdout.write("\n")


if __name__ == "__main__":
    main()
