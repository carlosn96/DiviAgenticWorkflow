#!/usr/bin/env python3
"""
DIE: Design Intelligence Engine (v3.0)
=======================================
Orquestador unificado que importa A+B+C+D+E como módulos para producir
plan.json completo listo para build_page.php --deploy.

Uso:
  python design_intelligence.py --brief-file=brief.json 2>&1

Output: plan.json con structure + decoration blocks.

Sin archivos intermedios. Sin orchestrate_page.php.
Sin compose_page.php. Sin post_compose.php.
"""

import json, sys, os, random, re
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

ARTIFACTS_DIR = Path(__file__).resolve().parent
DAW_ROOT = ARTIFACTS_DIR.parent.parent

SECTION_PATTERNS_PATH = ARTIFACTS_DIR / "section-patterns.json"
AFFINITIES_PATH = ARTIFACTS_DIR / "module-affinities.json"
CLASSIFIER_PATH = ARTIFACTS_DIR / "content-classifier.pkl"
SEMANTIC_INDEX_PATH = ARTIFACTS_DIR / "semantic-index.pkl"

# Column structure compatibility
COLUMN_MODULE_COMPAT = {
    "4_4": ["text", "heading", "button", "image", "video", "map", "code", "divider", "signup"],
    "1_2,1_2": ["text", "heading", "blurb", "button", "image", "testimonial", "team_member", "icon"],
    "1_3,1_3,1_3": ["blurb", "testimonial", "pricing_table", "team_member", "image", "number_counter"],
    "1_4,1_4,1_4,1_4": ["blurb", "image", "logo", "icon", "number_counter"],
    "1_3,2_3": ["text", "heading", "image", "video", "blurb", "button"],
    "2_5,3_5": ["text", "heading", "image", "blurb"],
    "3_5,2_5": ["image", "text", "heading", "button"],
    "1_4,1_2,1_4": ["blurb", "image", "testimonial", "icon"],
    "1_5,3_5,1_5": ["blurb", "image", "testimonial"],
    "3_4,1_4": ["text", "heading", "button", "cta"],
}


def load_brand_vars():
    """Carga _design_vars.json desde la marca activa."""
    daw_site = os.environ.get("DAW_SITE", "bibliotheca")
    brand_path = DAW_ROOT / "site" / daw_site / "brand" / "_design_vars.json"
    if brand_path.exists():
        return json.loads(brand_path.read_text("utf-8"))
    # Try DAW_bundle/site/ path
    brand_path2 = DAW_ROOT / "DAW_bundle" / "site" / daw_site / "brand" / "_design_vars.json"
    if brand_path2.exists():
        return json.loads(brand_path2.read_text("utf-8"))
    return {}


def load_brand_presets():
    """Carga _design_presets.json desde la marca activa."""
    daw_site = os.environ.get("DAW_SITE", "bibliotheca")
    presets_path = DAW_ROOT / "site" / daw_site / "brand" / "_design_presets.json"
    if presets_path.exists():
        return json.loads(presets_path.read_text("utf-8"))
    presets_path2 = DAW_ROOT / "DAW_bundle" / "site" / daw_site / "brand" / "_design_presets.json"
    if presets_path2.exists():
        return json.loads(presets_path2.read_text("utf-8"))
    return {}


class DesignIntelligenceEngine:
    """Orquestador A+B+C+D+E. Importa todos los artefactos como módulos."""

    def __init__(self):
        self.patterns = {}
        self.affinities = {}
        self.classifier = None
        self.semantic_items = []
        self.semantic_embeddings = None
        self.semantic_index = None
        self.deco_engine = None
        self._loaded = False

    def load(self):
        """Carga A+B+C+D+E"""
        print("[DIE] Cargando artefactos...", file=sys.stderr)

        # A: Section Patterns
        if SECTION_PATTERNS_PATH.exists():
            self.patterns = json.loads(SECTION_PATTERNS_PATH.read_text("utf-8"))
            print(f"[DIE]  A: {len(self.patterns)} section types", file=sys.stderr)
        else:
            print(f"[DIE]  A: NO ENCONTRADO", file=sys.stderr)

        # C: Module Affinities
        if AFFINITIES_PATH.exists():
            self.affinities = json.loads(AFFINITIES_PATH.read_text("utf-8"))
            print(f"[DIE]  C: {len(self.affinities)} affinity types", file=sys.stderr)
        else:
            print(f"[DIE]  C: NO ENCONTRADO", file=sys.stderr)

        # D: Content Classifier
        if CLASSIFIER_PATH.exists():
            sys.path.insert(0, str(ARTIFACTS_DIR))
            from d_content_classifier import ContentClassifier
            self.classifier = ContentClassifier.load(CLASSIFIER_PATH)
            print(f"[DIE]  D: classifier loaded", file=sys.stderr)
        else:
            print(f"[DIE]  D: NO ENCONTRADO", file=sys.stderr)

        # B: Semantic Index
        if SEMANTIC_INDEX_PATH.exists():
            import pickle
            with open(SEMANTIC_INDEX_PATH, "rb") as f:
                si_data = pickle.load(f)
            self.semantic_items = si_data["items"]
            self.semantic_embeddings = si_data.get("embeddings_normalized",
                                                     si_data.get("embeddings"))
            print(f"[DIE]  B: {len(self.semantic_items)} templates indexed", file=sys.stderr)
            sys.path.insert(0, str(ARTIFACTS_DIR))
            from b_semantic_index import SemanticIndex
            self.semantic_index = SemanticIndex()
            self.semantic_index.items = self.semantic_items
            self.semantic_index.embeddings_normalized = self.semantic_embeddings
            self.semantic_index._load_model()
            print(f"[DIE]  B: model loaded", file=sys.stderr)
        else:
            print(f"[DIE]  B: NO ENCONTRADO", file=sys.stderr)

        # E: Decoration Engine
        sys.path.insert(0, str(ARTIFACTS_DIR))
        from e_decorator import DecorationEngine
        self.deco_engine = DecorationEngine()
        if self.deco_engine.rules_path.exists() and self.deco_engine.clusters_path.exists():
            self.deco_engine.load()
            print(f"[DIE]  E: decoration engine loaded", file=sys.stderr)
        else:
            print(f"[DIE]  E: NO ENCONTRADO — run e_decorator.py --build first", file=sys.stderr)

        self._loaded = True

    def generate_plan(self, section_def: dict, brand_vars=None, brand_presets=None) -> dict:
        """Generate a complete design plan with structure + decoration."""
        if not self._loaded:
            self.load()

        title = section_def.get("title", "")
        section_type = section_def.get("section_type", "")
        tone = section_def.get("tone", "editorial")
        product_type = section_def.get("product_type", "")
        text = section_def.get("text", "")
        slots = section_def.get("slots", {})
        query_text = f"{title} {text}".strip() or title

        plan = {
            "page_def_version": "2.0",
            "section_type": "generic",
            "confidence": 0.0,
            "template": None,
            "template_path": None,
            "template_score": 0.0,
            "column_structure": "4_4",
            "modules": [],
            "slots": slots,
            "decoration": {},
            "presets": [],
        }

        # ── Paso 1: Clasificar semánticamente (D) ──
        if self.classifier and query_text and (not section_type or section_type == "generic"):
            try:
                result = self.classifier.predict(query_text)
                plan["section_type"] = result["section_type"]
                plan["confidence"] = result["confidence"]
                plan["modules"] = result["recommended_modules"]
                section_type = result["section_type"]
            except Exception as e:
                print(f"[DIE]  D error: {e}", file=sys.stderr)
        elif section_type:
            plan["section_type"] = section_type
            plan["confidence"] = 1.0
            if self.classifier and query_text:
                try:
                    result = self.classifier.predict(query_text)
                    plan["confidence"] = result["confidence"]
                    plan["modules"] = result["recommended_modules"]
                except Exception:
                    pass

        # ── Paso 2: Template semánticamente similar (B) ──
        best_template = None
        best_score = 0.0
        if self.semantic_index:
            try:
                results = self.semantic_index.search(query_text, category=section_type, limit=1)
                if results:
                    best_template = results[0]
                    best_score = results[0]["score"]
            except Exception as e:
                print(f"[DIE]  B error: {e}", file=sys.stderr)
                try:
                    matching = []
                    for i, item in enumerate(self.semantic_items):
                        cat = item.get("category", "")
                        if cat == section_type or section_type == "generic":
                            matching.append((i, item, 1.0))
                    query_words = set(query_text.lower().split())
                    for idx, item, _ in matching:
                        name = item.get("name", "").lower()
                        name_words = set(name.split())
                        overlap = len(query_words & name_words)
                        score = overlap / max(len(name_words), len(query_words)) if (overlap > 0 and len(name_words) > 0) else 0.0
                        if score > best_score:
                            best_score = score
                            best_template = item
                    if not best_template and matching:
                        best_template = matching[0][1]
                        best_score = 0.01
                except Exception:
                    pass

        if best_template:
            plan["template"] = best_template["name"]
            plan["template_path"] = best_template.get("path", "")
            plan["template_score"] = round(best_score, 4)

        # ── Paso 3: Estructura de columna (A) ──
        section_patterns = self.patterns.get(section_type, {})
        if section_patterns:
            col_structures = section_patterns.get("column_structures", [])
            if col_structures:
                total_weight = sum(c.get("frequency", c.get("count", 1)) for c in col_structures)
                r = random.random() * total_weight
                cumulative = 0.0
                for cs in col_structures:
                    cumulative += cs.get("frequency", cs.get("count", 1))
                    if r <= cumulative:
                        plan["column_structure"] = cs["structure"]
                        break
                if not plan["column_structure"]:
                    plan["column_structure"] = col_structures[0]["structure"]

        # ── Paso 4: Módulos complementarios (C) ──
        if not plan["modules"] and section_patterns:
            common_modules = section_patterns.get("common_modules", [])
            plan["modules"] = [m["module_tag"] for m in common_modules[:6]]

        affinity_data = self.affinities.get(section_type, {})
        if affinity_data:
            top_pairs = affinity_data.get("top_pairs", [])
            for pair in top_pairs[:3]:
                mods = pair.get("modules", [])
                for m in mods:
                    if m not in plan["modules"]:
                        plan["modules"].append(m)

        # ── Paso 5: Decoration blocks (E) ──
        if self.deco_engine and self.deco_engine.is_ready():
            try:
                decoration = self.deco_engine.get_decoration(
                    section_type=section_type,
                    tone=tone,
                    product_type=product_type,
                    brand_vars=brand_vars or {},
                    brand_presets=brand_presets or {},
                )
                plan["decoration"] = decoration
                if "section_preset" in decoration:
                    plan["presets"].append(decoration["section_preset"])
            except Exception as e:
                print(f"[DIE]  E error: {e}", file=sys.stderr)
                plan["decoration"] = {}
        else:
            print(f"[DIE]  E: not ready, skipping decoration", file=sys.stderr)
            plan["decoration"] = {}

        return plan


def main():
    import argparse
    parser = argparse.ArgumentParser(description="DIE v3.0 — Design Intelligence Engine")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--section", help="JSON section definition as string")
    group.add_argument("--section-file", help="Path to JSON file with section definition")
    group.add_argument("--brief-file", help="Path to JSON brief file (tone + product_type + sections)")
    parser.add_argument("--output", help="Output path for plan.json / plans.json")
    parser.add_argument("--no-brand", action="store_true", help="Skip brand vars loading")
    args = parser.parse_args()

    brand_vars = {} if args.no_brand else load_brand_vars()
    brand_presets = {} if args.no_brand else load_brand_presets()
    if brand_vars:
        print(f"[DIE] Brand: {brand_vars.get('brand_name', 'unknown')}", file=sys.stderr)

    die = DesignIntelligenceEngine()

    if args.brief_file:
        brief = json.loads(Path(args.brief_file).read_text("utf-8"))
        tone = brief.get("tone", "editorial")
        product_type = brief.get("product_type", brand_vars.get("brand_name", ""))
        sections = brief.get("sections", [])
        plans = []
        for sec in sections:
            sec["tone"] = tone
            sec["product_type"] = product_type
            plan = die.generate_plan(sec, brand_vars, brand_presets)
            plans.append(plan)
        output = json.dumps(plans, indent=2, ensure_ascii=False)
        print(output)
        if args.output:
            Path(args.output).write_text(output, encoding="utf-8")
            print(f"[DIE] Plans written: {args.output} ({len(plans)} sections)", file=sys.stderr)
    else:
        if args.section_file:
            section_def = json.loads(Path(args.section_file).read_text("utf-8"))
        else:
            section_def = json.loads(args.section)
        section_def["product_type"] = section_def.get("product_type", brand_vars.get("brand_name", ""))
        plan = die.generate_plan(section_def, brand_vars, brand_presets)
        output = json.dumps(plan, indent=2, ensure_ascii=False)
        print(output)
        if args.output:
            Path(args.output).write_text(output, encoding="utf-8")
            print(f"[DIE] Plan written: {args.output}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
