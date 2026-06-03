#!/usr/bin/env python3
"""
DIE v4.0 — Design Intelligence Engine con Director + Quality Gate

Orquestador que usa design_director.py (stacking ensemble) para tomar
TODAS las decisiones de diseño, validar el resultado con el quality gate,
y producir plan.json listo para build_page.php --deploy.

Uso:
  python design_intelligence.py --brief-file=brief.json --output=plan.json

Contrato DAW intacto. Solo cambia el motor interno.
"""

import json, sys, os, copy
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ARTIFACTS_DIR = Path(__file__).resolve().parent
DAW_ROOT = ARTIFACTS_DIR.parent.parent

SCHEMA_PATH = DAW_ROOT / "workspace" / "section-schema.json"

QUALITY_THRESHOLD = 0.65


def load_env():
    if "DAW_SITE" in os.environ and os.environ["DAW_SITE"]:
        return os.environ["DAW_SITE"]
    env_path = DAW_ROOT.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text("utf-8").splitlines():
            line = line.strip()
            if line.startswith("DAW_SITE="):
                val = line.split("=", 1)[1].strip().strip("\"'")
                if val:
                    os.environ["DAW_SITE"] = val
                    return val
    return None


def load_brand_vars():
    daw_site = load_env()
    if not daw_site:
        return None
    for base in [DAW_ROOT, DAW_ROOT / "DAW_bundle"]:
        p = base / "site" / daw_site / "brand" / "_design_vars.json"
        if p.exists():
            return json.loads(p.read_text("utf-8"))
    return {}


def load_brand_presets():
    daw_site = load_env()
    if not daw_site:
        return None
    for base in [DAW_ROOT, DAW_ROOT / "DAW_bundle"]:
        p = base / "site" / daw_site / "brand" / "_design_presets.json"
        if p.exists():
            return json.loads(p.read_text("utf-8"))
    return {}


def load_design_system():
    daw_site = load_env()
    if not daw_site:
        return None
    for base in [DAW_ROOT, DAW_ROOT / "DAW_bundle"]:
        p = base / "site" / daw_site / "design-system" / "divitheme.json"
        if p.exists():
            return json.loads(p.read_text("utf-8"))
    return {}


def main():
    import argparse
    parser = argparse.ArgumentParser(description="DIE v4.0 — Design Intelligence Engine")
    parser.add_argument("--brief-file", required=True, help="Path to brief JSON file")
    parser.add_argument("--output", help="Output path for plan.json")
    parser.add_argument("--no-brand", action="store_true", help="Skip brand vars")
    parser.add_argument("--skip-quality-gate", action="store_true",
                        help="Skip validation and deploy anyway")
    args = parser.parse_args()

    brand_vars = {} if args.no_brand else load_brand_vars()
    brand_presets = {} if args.no_brand else load_brand_presets()
    design_system = {} if args.no_brand else load_design_system()
    if brand_vars is None:
        print("[DIE] ERROR: DAW_SITE no definido.", file=sys.stderr)
        sys.exit(1)
    if brand_vars:
        print(f"[DIE] Brand: {brand_vars.get('brand_name', 'unknown')}", file=sys.stderr)
    if design_system:
        strategy = design_system.get('strategy', 'generic')
        total_presets = sum(len(v) for v in design_system.get('presets', {}).values())
        print(f"[DIE] Design system: strategy={strategy} presets={total_presets}", file=sys.stderr)

    # ── Load Director ───────────────────────────────────────────────────
    from design_director import DesignDirector
    director = DesignDirector()
    director.load()
    print(f"[DIE] Director ready.", file=sys.stderr)

    # ── Load brief ──────────────────────────────────────────────────────
    brief = json.loads(Path(args.brief_file).read_text("utf-8"))
    tone = brief.get("tone", "editorial")
    product_type = brief.get("product_type") or brand_vars.get("brand_name", "")
    sections = brief.get("sections", [])
    print(f"[DIE] Brief: {len(sections)} sections, tone={tone}", file=sys.stderr)

    # ── Phase 0: Compose page visual rhythm ────────────────────────────
    page_composition = director.compose_page(brief, sections, product_type)
    rhythm_pattern = page_composition.get("rhythm", {})
    variant_map = page_composition.get("variant_map", {})
    atmosphere_key = page_composition.get("atmosphere_key", "clean")
    print(f"[DIE] Page composition: tone={tone} atmosphere={atmosphere_key} "
          f"variants={len(variant_map)}", file=sys.stderr)

    # ── Phase 1: Generate section plans via Director ────────────────────
    plans = []
    for i, sec in enumerate(sections):
        sec["tone"] = tone
        sec["product_type"] = product_type
        context = {
            "brand_vars": brand_vars,
            "brand_presets": brand_presets,
            "adjacent_section_type": sections[i-1].get("section_type")
            if i > 0 else None,
            "page_composition": page_composition,
            "section_index": i,
            "product_type": product_type,
        }
        plan = director.generate_section_plan(sec, context)
        plans.append(plan)
        tmpl = plan.get("template", "none") or "none"
        score = plan.get("template_score", 0)
        variant = plan.get("variant", "none")
        preset = plan.get("presets", ["none"])[0]
        vtag = f" variant={variant}" if variant != "none" else ""
        print(f"[DIE]  [{i}] {sec.get('section_type','?'):15s} template={tmpl} score={score:.4f} preset={preset}{vtag}",
              file=sys.stderr)

    # Merge design system presets (enriched) with brand presets (user overrides)
    ds_presets = design_system.get('presets', {})
    merged_presets = copy.deepcopy(ds_presets)
    for cat, items in brand_presets.items():
        if cat in merged_presets:
            merged_presets[cat] = {**merged_presets[cat], **items}
        else:
            merged_presets[cat] = items

    # ── Phase 2: Map plans to page-def via mapper ─────────────────────────
    sys.path.insert(0, str(ARTIFACTS_DIR))
    from e_page_mapper import build_page_def
    page_def = build_page_def(brief, plans, brand_vars, merged_presets)
    print(f"[DIE] Page-def built: {len(page_def.get('sections', []))} sections",
          file=sys.stderr)

    # ── Phase 3.5: Clean preset conflicts ────────────────────────────────
    # If glass-card + feature-card coexist, drop the generic one
    PRESET_PRIORITY = {
        'module': ['glass-card', 'feature-card', 'card'],
        'transform': ['hover-glow', 'hover-lift', 'hover-scale', 'hover-expand'],
        'text': ['hero-title', 'display-xl', 'display-md', 'headline', 'lead'],
    }
    for sec in page_def.get('sections', []):
        for row in sec.get('rows', []):
            for col in row.get('columns', []):
                for mod in col.get('modules', []):
                    presets = mod.get('presets', [])
                    if not presets:
                        continue
                    cleaned = list(presets)
                    for category, priority_list in PRESET_PRIORITY.items():
                        found = [p for p in cleaned if p.startswith(f"{category}:")]
                        if len(found) > 1:
                            # Keep the highest priority (lowest index in list)
                            best = None
                            best_idx = 999
                            for p in found:
                                name = p.split(':', 1)[1]
                                if name in priority_list:
                                    idx = priority_list.index(name)
                                    if idx < best_idx:
                                        best_idx = idx
                                        best = p
                            if best:
                                for p in found:
                                    if p != best and p in cleaned:
                                        cleaned.remove(p)
                    mod['presets'] = cleaned

    # ── Phase 3: Quality Gate ────────────────────────────────────────────
    if not args.skip_quality_gate:
        # Auto-fix empty modules before scoring
        fixed = director._fix_empty_modules(page_def.get("sections", []), brief)
        if fixed:
            print(f"[DIE] Auto-fixed {fixed} empty module(s) from brief content",
                  file=sys.stderr)

        score, issues, details = director.validate_visual_cohesion(page_def)
        print(f"[DIE] Quality Gate score: {score:.3f} / 1.0", file=sys.stderr)
        for iss in issues[:5]:
            print(f"[DIE]   Issue: {iss}", file=sys.stderr)

        if score < QUALITY_THRESHOLD:
            print(f"[DIE] Score {score:.3f} < threshold {QUALITY_THRESHOLD}. "
                  f"Applying margin to spacing...", file=sys.stderr)
            for i, sec in enumerate(page_def.get("sections", [])):
                pad = director.decide_spacing(
                    sections[i] if i < len(sections) else sec,
                    sections[i].get("section_type", "generic")
                    if i < len(sections) else "generic",
                    None)
                deco = sec.get("decoration", {})
                if "spacing" not in deco:
                    deco["spacing"] = {}
                deco["spacing"]["desktop"] = {
                    "value": {
                        "padding": {"top": f"{pad}px", "bottom": f"{pad}px"}
                    }
                }
                sec["decoration"] = deco

            score2, issues2, _ = director.validate_visual_cohesion(page_def)
            print(f"[DIE] Post-fix score: {score2:.3f}", file=sys.stderr)
            if score2 < QUALITY_THRESHOLD:
                print(f"[DIE] WARNING: Score {score2:.3f} still below threshold. "
                      f"Deploying with issues.", file=sys.stderr)

    # ── Output ───────────────────────────────────────────────────────────
    output = json.dumps(page_def, indent=2, ensure_ascii=False)
    print(output)
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"[DIE] Page-def written: {args.output} "
              f"({len(page_def.get('sections', []))} sections)", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
