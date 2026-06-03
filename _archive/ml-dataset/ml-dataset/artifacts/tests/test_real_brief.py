#!/usr/bin/env python3
"""Test DIE with a real generated brief (YAML → JSON pipeline)."""
import sys, json, re, os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from design_intelligence import DesignIntelligenceEngine, load_brand_vars, load_brand_presets

os.environ['DAW_SITE'] = 'bibliotheca'

yaml_path = Path(__file__).resolve().parent.parent.parent.parent / 'site' / 'bibliotheca' / 'briefs' / 'home.yml'

# Fix YAML: quote values starting with &# to avoid YAML anchor confusion
raw = yaml_path.read_text('utf-8')
fixed = re.sub(r': (\&\#[xe0f0]\w+;)', r': "\1"', raw)

import yaml
brief = yaml.safe_load(fixed)

print(f'Brief: {brief["title"]} ({len(brief["sections"])} sections)', file=sys.stderr)

bv = load_brand_vars()
bp = load_brand_presets()

die = DesignIntelligenceEngine()
die.load()

tone = brief.get('tone', 'editorial')
product_type = 'bibliotheca'

plans = []
for sec in brief.get('sections', []):
    section_def = {k: v for k, v in sec.items() if not isinstance(v, list)}
    section_def['slots'] = {k: v for k, v in sec.items() if isinstance(v, list)}
    section_def['tone'] = tone
    section_def['product_type'] = product_type

    plan = die.generate_plan(section_def, bv, bp)
    plans.append(plan)

    deco = plan.get('decoration', {})
    has_deco = bool(deco.get('section_preset') or deco.get('gradient'))
    print(f'  [{plan["section_type"]}] col={plan["column_structure"]} '
          f'deco={has_deco} preset={deco.get("section_preset","")}',
          file=sys.stderr)

output = json.dumps(plans, indent=2, ensure_ascii=False)
out_path = Path(__file__).resolve().parent.parent.parent.parent / 'site' / 'bibliotheca' / 'plans' / 'home.json'
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(output, encoding='utf-8')
print(f'Written: {out_path}', file=sys.stderr)
print(output)
sys.exit(0)
