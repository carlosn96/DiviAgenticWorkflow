#!/usr/bin/env python3
"""
Extract slot schemas from all section templates (base + variants).
Outputs a JSON map used by generate_brief.py to tell the AI what slots each template expects.
"""

import json
import os
import re
from glob import glob

SECTIONS_DIR = os.path.join(os.path.dirname(__file__), '..', 'sections')
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), '..', 'section-schema.json')

SLOT_RE = re.compile(r'\{\{slot:([^}]+)\}\}')
REPEAT_SOURCE_RE = re.compile(r'"source"\s*:\s*"([^"]+)"')
DESIGN_TOKEN_RE = re.compile(r'\{\{design:([^}:]+):([^}]+)\}\}')

def extract_slots(obj, path=''):  
    slots = set()
    repeat_sources = set()
    design_tokens = set()

    def _walk(o, ctx):
        if isinstance(o, str):
            for m in SLOT_RE.finditer(o):
                slots.add(m.group(1))
            for m in DESIGN_TOKEN_RE.finditer(o):
                design_tokens.add(f"{m.group(1)}:{m.group(2)}")
        elif isinstance(o, dict):
            for k, v in o.items():
                _walk(v, f"{ctx}.{k}")
        elif isinstance(o, list):
            for i, v in enumerate(o):
                _walk(v, f"{ctx}[{i}]")

    _walk(obj, path)
    return sorted(slots), sorted(design_tokens)

def extract_repeat_source(obj):
    sources = set()
    if isinstance(obj, dict):
        if '_repeat' in obj and isinstance(obj['_repeat'], dict):
            src = obj['_repeat'].get('source', '')
            if src:
                sources.add(src)
        for v in obj.values():
            sources |= extract_repeat_source(v)
    elif isinstance(obj, list):
        for v in obj:
            sources |= extract_repeat_source(v)
    return sources

def map_section_type(template_name):
    """Map template directory name to section_type used in briefs"""
    mapping = {
        'hero-split': 'hero',
        'hero-centered': 'hero-centered',
        'features-3col': 'features',
        'content-split': 'content',
        'content-split-icon-list': 'content-list',
        'cta-centered': 'cta',
        'testimonials-3col': 'testimonials',
        'stats-4col': 'stats',
        'logos-4col': 'logos',
    }
    return mapping.get(template_name, template_name)

def main():
    schema = {}

    for base_path in sorted(glob(os.path.join(SECTIONS_DIR, '*', '_base.section.json'))):
        template_dir = os.path.basename(os.path.dirname(base_path))
        section_type = map_section_type(template_dir)

        with open(base_path, 'r') as f:
            data = json.load(f)

        slots, tokens = extract_slots(data)
        sources = extract_repeat_source(data)
        presets = data.get('presets', [])

        entry = {
            'section_type': section_type,
            'template': template_dir,
            'slots': slots,
            'repeat_sources': sorted(sources),
            'presets': presets,
            'design_tokens': tokens,
            'variants': {},
        }

        # Load variants
        for variant_path in sorted(glob(os.path.join(SECTIONS_DIR, template_dir, '*.variant.json'))):
            variant_name = os.path.splitext(os.path.basename(variant_path))[0]
            with open(variant_path, 'r') as f:
                vdata = json.load(f)
            vslots, vtokens = extract_slots(vdata)
            vsources = extract_repeat_source(vdata)
            entry['variants'][variant_name] = {
                'slots': vslots,
                'repeat_sources': sorted(vsources),
                'design_tokens': vtokens,
            }

        schema[section_type] = entry

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)

    print(f"[SCHEMA] {len(schema)} section types extracted -> {OUTPUT_PATH}")
    for st, entry in schema.items():
        base_slots = ', '.join(entry['slots'][:6])
        variants = ', '.join(entry['variants'].keys()) or '(none)'
        print(f"  {st:20s} -> {entry['template']:25s} slots: {base_slots}")
        print(f"  {'':20s}   variants: {variants}")

if __name__ == '__main__':
    main()
