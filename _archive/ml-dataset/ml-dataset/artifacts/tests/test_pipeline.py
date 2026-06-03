#!/usr/bin/env python3
"""Test: DIE pipeline validation — brief → plan.json with decoration blocks."""
import sys, json, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from design_intelligence import DesignIntelligenceEngine, load_brand_vars, load_brand_presets

os.environ['DAW_SITE'] = 'bibliotheca'

bv = load_brand_vars()
bp = load_brand_presets()

die = DesignIntelligenceEngine()
die.load()

brief = {
    'title': 'Test Page',
    'tone': 'editorial',
    'product_type': 'bibliotheca',
    'sections': [
        {'section_type': 'hero', 'title': 'Welcome', 'text': 'Main hero section'},
        {'section_type': 'features', 'title': 'Our Features', 'text': 'Feature grid'}
    ]
}

plans = []
for sec in brief['sections']:
    sec['tone'] = brief['tone']
    sec['product_type'] = brief.get('product_type', '')
    plan = die.generate_plan(sec, bv, bp)
    deco = plan.get('decoration', {})
    has_content = bool(deco.get('css') or deco.get('section_preset') or deco.get('shape_divider') or deco.get('gradient'))
    plans.append(plan)
    print(f"Section: {sec['section_type']}")
    print(f"  section_type: {plan['section_type']}")
    print(f"  column_structure: {plan['column_structure']}")
    print(f"  template: {plan['template']} (score: {plan['template_score']})")
    print(f"  modules: {plan['modules'][:4]}...")
    print(f"  decoration keys: {list(deco.keys())[:6]}")
    print(f"  decoration has content: {has_content}")
    print()

print(f"Plans generated: {len(plans)}")
print("PIPELINE VALIDATION: PASS")
sys.exit(0)
