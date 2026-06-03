"""VIE CLI — same args as legacy visual_impact_engine.py."""
import argparse
import json
import sys
from pathlib import Path

# Allow `python vie/cli.py` to find the vie package without PYTHONPATH.
_PKG_PARENT = Path(__file__).resolve().parent.parent
if str(_PKG_PARENT) not in sys.path:
    sys.path.insert(0, str(_PKG_PARENT))

from vie.engine import VisualImpactEngine


def main():
    parser = argparse.ArgumentParser(description="VIE — Page-def generator")
    parser.add_argument("--brief-file", required=True, help="Path to brief JSON")
    parser.add_argument("--design-system", required=True, help="Path to design system JSON")
    parser.add_argument("--catalog", default=None, help="Path to divi_catalog.json (optional)")
    parser.add_argument("--dataset", default=None, help="Path to diviplus_dataset.json (optional)")
    parser.add_argument("--output", required=True, help="Output path for page-def JSON")
    parser.add_argument("--evaluate", action="store_true", help="Print impact score")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducible variation")
    args = parser.parse_args()

    with open(args.brief_file, 'r', encoding='utf-8') as f:
        brief = json.load(f)
    with open(args.design_system, 'r', encoding='utf-8') as f:
        design_system = json.load(f)

    catalog_path = Path(args.catalog) if args.catalog else None
    dataset_path = Path(args.dataset) if args.dataset else None
    engine = VisualImpactEngine(design_system, catalog_path, dataset_path, seed=args.seed)
    page_def = engine.translate_brief(brief)

    if args.evaluate:
        scores = engine.evaluate_page_impact(page_def)
        print(f"[VIE v3.0] Impact Score: {scores['total']}/{scores['max_possible']} ({scores['impact_percentage']:.1f}%)")
        for section, score in scores["per_section"].items():
            print(f"  - {section}: {score} pts")

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(page_def, f, indent=2, ensure_ascii=False)
    print(f"[VIE v3.0] Generated: {args.output}")


if __name__ == "__main__":
    main()
