#!/usr/bin/env python3
"""
DIE: Design Intelligence Engine

Orquestador que encadena los 4 artefactos inteligentes para producir
un plan de diseno accionable (plan.json) a partir de una seccion del brief.

Uso:
  python design_intelligence.py --section='{"title":"hero","tone":"editorial","text":"..."}' 2>&1

Output: plan.json  (consumido por orchestrate_page.php)
  {
    "section_type": "hero",
    "confidence": 0.94,
    "template": "Hero University",
    "template_path": "...",
    "template_score": 0.91,
    "column_structure": "4_4",
    "modules": ["heading", "text", "button", "image"],
    "variant": "editorial-grid",
    "has_gradient": true
  }
"""

import json, sys, os, random
from pathlib import Path

# Workaround for Windows console encoding
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
EMBEDDINGS_PATH = DAW_ROOT / "workspace" / "catalog" / "embeddings.pkl"

# Tone to variant mapping (from orchestrate_page.php)
TONE_VARIANTS = {
    "editorial": {
        "hero": "editorial-grid", "hero-split": "editorial-grid",
        "content-split": "editorial-grid", "content-split-icon-list": "editorial-list",
    },
    "modern": {
        "hero-centered": "liquid-glass", "features-3col": "monochrome-brutalist",
    },
    "premium": {
        "hero-centered": "liquid-glass", "cta-centered": "glass-cta",
    },
    "minimal": {},
    "dramatic": {},
    "playful": {},
}

# Column structure compatibility: which module types work with which structures
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


class DesignIntelligenceEngine:
    def __init__(self):
        self.patterns = {}
        self.affinities = {}
        self.classifier = None
        self.semantic_index = None
        self._loaded = False

    def load(self):
        """Load all artifacts"""
        print("[DIE] Cargando artefactos...", file=sys.stderr)

        # A: Section Patterns
        if SECTION_PATTERNS_PATH.exists():
            self.patterns = json.loads(SECTION_PATTERNS_PATH.read_text("utf-8"))
            print(f"[DIE]  A: {len(self.patterns)} tipos de seccion", file=sys.stderr)
        else:
            print(f"[DIE]  A: NO ENCONTRADO {SECTION_PATTERNS_PATH}", file=sys.stderr)

        # C: Module Affinities
        if AFFINITIES_PATH.exists():
            self.affinities = json.loads(AFFINITIES_PATH.read_text("utf-8"))
            print(f"[DIE]  C: {len(self.affinities)} tipos con afinidades", file=sys.stderr)
        else:
            print(f"[DIE]  C: NO ENCONTRADO {AFFINITIES_PATH}", file=sys.stderr)

        # D: Classifier
        if CLASSIFIER_PATH.exists():
            sys.path.insert(0, str(ARTIFACTS_DIR))
            from d_content_classifier import ContentClassifier
            self.classifier = ContentClassifier.load(CLASSIFIER_PATH)
            print(f"[DIE]  D: clasificador cargado", file=sys.stderr)
        else:
            print(f"[DIE]  D: NO ENCONTRADO {CLASSIFIER_PATH}", file=sys.stderr)

        # B: Semantic Index
        if SEMANTIC_INDEX_PATH.exists():
            import pickle
            with open(SEMANTIC_INDEX_PATH, "rb") as f:
                si_data = pickle.load(f)
            self.semantic_items = si_data["items"]
            self.semantic_embeddings = si_data.get("embeddings_normalized",
                                                     si_data.get("embeddings"))
            print(f"[DIE]  B: {len(self.semantic_items)} templates indexados", file=sys.stderr)
        elif EMBEDDINGS_PATH.exists():
            sys.path.insert(0, str(ARTIFACTS_DIR))
            from b_semantic_index import SemanticIndex
            self.semantic_index_obj = SemanticIndex()
            self.semantic_index_obj.build(EMBEDDINGS_PATH)
            print(f"[DIE]  B: indice construido desde embeddings.pkl", file=sys.stderr)
        else:
            print(f"[DIE]  B: NO ENCONTRADO", file=sys.stderr)

        self._loaded = True

    def generate_plan(self, section_def: dict) -> dict:
        """Generate a complete design plan for one section"""
        if not self._loaded:
            self.load()

        title = section_def.get("title", "")
        section_type = section_def.get("section_type", "")
        tone = section_def.get("tone", "editorial")
        text = section_def.get("text", "")
        query_text = f"{title} {text}".strip() or title

        plan = {
            "section_type": "generic",
            "confidence": 0.0,
            "template": None,
            "template_path": None,
            "template_score": 0.0,
            "column_structure": "4_4",
            "modules": [],
            "variant": "",
            "has_gradient": False,
            "has_divider": False,
        }

        # Paso 1: Clasificar semánticamente (Artefacto D)
        # Trust designer-provided section_type; use D classifier as fallback
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
            # Get module recommendations even when type is from brief
            if self.classifier and query_text:
                try:
                    result = self.classifier.predict(query_text)
                    plan["confidence"] = result["confidence"]
                    plan["modules"] = result["recommended_modules"]
                except Exception:
                    pass

        # Paso 2: Buscar template semánticamente similar (Artefacto B)
        best_template = None
        best_score = 0.0
        if hasattr(self, "semantic_items") and self.semantic_items:
            try:
                sys.path.insert(0, str(ARTIFACTS_DIR))
                from b_semantic_index import SemanticIndex
                si = SemanticIndex()
                si.items = self.semantic_items
                si.embeddings_normalized = self.semantic_embeddings
                si._load_model()
                results = si.search(query_text, category=section_type, limit=1)
                if results:
                    best_template = results[0]
                    best_score = results[0]["score"]
            except Exception as e:
                print(f"[DIE]  B error using SemanticIndex: {e}", file=sys.stderr)
                # Fallback to simple overlap if something fails
                try:
                    import numpy as np
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

        # Paso 3: Elegir estructura de columna (Artefacto A)
        section_patterns = self.patterns.get(section_type, {})
        if section_patterns:
            col_structures = section_patterns.get("column_structures", [])
            if col_structures:
                # Weighted random selection
                total_weight = sum(c["frequency"] for c in col_structures)
                r = random.random() * total_weight
                cumulative = 0.0
                for cs in col_structures:
                    cumulative += cs.get("frequency", cs.get("count", 1))
                    if r <= cumulative:
                        plan["column_structure"] = cs["structure"]
                        break
                if not plan["column_structure"]:
                    plan["column_structure"] = col_structures[0]["structure"]

            # Decorations
            deco = section_patterns.get("decorations", {})
            plan["has_gradient"] = random.random() < deco.get("gradient_frequency", 0.0)
            plan["has_divider"] = random.random() < deco.get("divider_frequency", 0.0)

        # Paso 4: Variant por tone
        variant_map = TONE_VARIANTS.get(tone, {})
        plan["variant"] = variant_map.get(section_type, variant_map.get(
            plan.get("template", ""), ""))

        # Paso 5: Si no hay template del índice B, sugerir desde patrones A
        if not plan["template"] and section_patterns:
            common_modules = section_patterns.get("common_modules", [])
            if not plan["modules"]:
                plan["modules"] = [m["module_tag"] for m in common_modules[:6]]

        return plan


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Design Intelligence Engine")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--section", help="JSON section definition as string")
    group.add_argument("--section-file", help="Path to JSON file with section definition")
    group.add_argument("--brief-file", help="Path to JSON file with full brief (tone + sections array)")
    parser.add_argument("--output", help="Output path for plan.json (single) or plans.json (batch)")
    args = parser.parse_args()

    die = DesignIntelligenceEngine()

    if args.brief_file:
        # Batch mode: process all sections in one brief
        brief = json.loads(Path(args.brief_file).read_text("utf-8"))
        tone = brief.get("tone", "editorial")
        sections = brief.get("sections", [])
        plans = []
        for sec in sections:
            sec["tone"] = tone
            plan = die.generate_plan(sec)
            plans.append(plan)
        output = json.dumps(plans, indent=2, ensure_ascii=False)
        print(output)
        if args.output:
            Path(args.output).write_text(output, encoding="utf-8")
            print(f"[DIE] Planes escritos: {args.output} ({len(plans)} secciones)", file=sys.stderr)
    else:
        if args.section_file:
            section_def = json.loads(Path(args.section_file).read_text("utf-8"))
        else:
            section_def = json.loads(args.section)

        plan = die.generate_plan(section_def)
        output = json.dumps(plan, indent=2, ensure_ascii=False)
        print(output)
        if args.output:
            Path(args.output).write_text(output, encoding="utf-8")
            print(f"[DIE] Plan escrito: {args.output}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
