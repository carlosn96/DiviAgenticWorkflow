#!/usr/bin/env python3
"""
Artefacto C: Module Composition Knowledge Base
Naturaleza: Minería de patrones asociativos (market basket analysis)
Algoritmo: Pointwise Mutual Information (PMI)

PMI(A, B) = log(P(A∩B) / (P(A) × P(B)))

PMI > 1.0 = afinidad fuerte (aparecen juntos más de lo esperado)
PMI < 0.0 = se evitan (aparecen juntos menos de lo esperado)

Input: dataset.jsonl (877 registros con módulos por template)
Output: module-affinities.json (matriz de afinidad por section_type)
"""

import json, sys, math
from pathlib import Path
from collections import Counter, defaultdict
DAW_ROOT = Path(__file__).resolve().parent.parent

DATASET_PATH = DAW_ROOT / "dataset.jsonl"
OUTPUT_PATH = Path(__file__).resolve().parent / "module-affinities.json"

SKIP_TAGS = {'et_pb_section', 'et_pb_row', 'et_pb_row_inner', 'et_pb_column', 'et_pb_column_inner'}

# Load section types from section-patterns to use same categorization
PATTERNS_PATH = Path(__file__).resolve().parent / "section-patterns.json"


def load_section_types() -> dict:
    """Load section types from artifact A output"""
    if not PATTERNS_PATH.exists():
        return {}
    patterns = json.loads(PATTERNS_PATH.read_text("utf-8"))
    return patterns


def get_section_types_from_shortcodes(raw_shortcode: str, folder_name: str, json_path: str) -> str:
    """Reuse categorization from extract_patterns"""
    sys.path.insert(0, str(DAW_ROOT.parent / "workspace"))
    from extract_patterns import extract_divi_info, categorize_section
    info = extract_divi_info(raw_shortcode, folder_name, json_path)
    return categorize_section(folder_name, info)


def build_section_type_map() -> dict:
    """Build name -> section_type from raw shortcodes"""
    name_to_type = {}

    catalog_dir = DAW_ROOT.parent / "workspace" / "catalog" / "jsons"
    if not catalog_dir.exists():
        return name_to_type

    sys.path.insert(0, str(DAW_ROOT.parent / "workspace"))
    from extract_patterns import extract_divi_info, categorize_section

    for subdir in sorted(catalog_dir.iterdir()):
        if not subdir.is_dir():
            continue
        json_files = list(subdir.glob("*.json"))
        if not json_files:
            continue
        try:
            raw = json_files[0].read_text("utf-8")
            data = json.loads(raw)
            inner = data.get("data", {})
            shortcode = ""
            for val in inner.values():
                if isinstance(val, str):
                    shortcode += val
            if not shortcode.strip():
                continue
            info = extract_divi_info(shortcode, subdir.name, str(json_files[0]))
            section_type = categorize_section(subdir.name, info)
            name_to_type[subdir.name] = section_type
        except Exception:
            pass

    return name_to_type


def main():
    print("[C] Module Composition KB — calculando PMI...")

    # Cargar dataset
    records = []
    with open(DATASET_PATH, encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line))
    print(f"[C]  {len(records)} registros cargados")

    # Categorizar cada template
    name_to_type = build_section_type_map()
    print(f"[C]  {len(name_to_type)} templates categorizados")

    # Agrupar módulos por tipo de sección
    section_modules = defaultdict(list)  # section_type -> list of module sets

    skipped = 0
    for rec in records:
        name = rec["source"]
        section_type = name_to_type.get(name, "generic")

        # Extraer módulos (sin section/row/column)
        tree = rec.get("tree", rec.get("module_types", []))
        if "tree" in rec and rec["tree"]:
            modules = set()
            def walk(nodes):
                for n in nodes:
                    if n["tag"] not in SKIP_TAGS:
                        modules.add(n["tag"])
                    walk(n.get("children", []))
            walk(rec["tree"])
        elif "module_types" in rec:
            modules = set(m for m in rec["module_types"] if m not in SKIP_TAGS)
        else:
            skipped += 1
            continue

        if modules:
            section_modules[section_type].append(modules)

    print(f"[C]  {len(section_modules)} tipos de sección con módulos")
    if skipped:
        print(f"[C]  {skipped} registros sin datos de módulos")

    # Calcular PMI por tipo de sección
    result = {}

    for section_type, module_sets in sorted(section_modules.items()):
        total = len(module_sets)
        if total < 3:
            continue

        # Frecuencia individual de cada módulo
        module_counts = Counter()
        for ms in module_sets:
            module_counts.update(ms)

        # Frecuencia de co-ocurrencia de pares
        pair_counts = Counter()
        for ms in module_sets:
            mod_list = sorted(ms)
            for i in range(len(mod_list)):
                for j in range(i + 1, len(mod_list)):
                    pair = (mod_list[i], mod_list[j])
                    pair_counts[pair] += 1

        # Calcular PMI para cada par
        affinities = []
        by_module_compat = defaultdict(list)
        by_module_incompat = defaultdict(list)

        for (mod_a, mod_b), co_count in pair_counts.most_common(100):
            if co_count < 2:
                continue

            p_a = module_counts[mod_a] / total
            p_b = module_counts[mod_b] / total
            p_ab = co_count / total

            if p_a > 0 and p_b > 0 and p_ab > 0:
                pmi = math.log(p_ab / (p_a * p_b))

                affinities.append({
                    "pair": [mod_a, mod_b],
                    "pmi": round(pmi, 3),
                    "count": co_count,
                    "frequency": round(co_count / total, 3),
                })

                if pmi > 1.0:
                    by_module_compat[mod_a].append({"module": mod_b, "pmi": round(pmi, 3)})
                    by_module_compat[mod_b].append({"module": mod_a, "pmi": round(pmi, 3)})
                elif pmi < -0.5:
                    by_module_incompat[mod_a].append({"module": mod_b, "pmi": round(pmi, 3)})
                    by_module_incompat[mod_b].append({"module": mod_a, "pmi": round(pmi, 3)})

        top_modules = [
            {"module_tag": m, "count": c, "frequency": round(c / total, 3)}
            for m, c in module_counts.most_common(20)
        ]

        # Build by_module output (compat + incompat per module)
        by_module_out = {}
        for mod in list(by_module_compat.keys()) + list(by_module_incompat.keys()):
            if mod in SKIP_TAGS:
                continue
            compat = sorted(by_module_compat.get(mod, []), key=lambda x: x["pmi"], reverse=True)[:10]
            incompat = sorted(by_module_incompat.get(mod, []), key=lambda x: x["pmi"])[:5]
            by_module_out[mod] = {"compatible": compat, "incompatible": incompat}

        result[section_type] = {
            "total_samples": total,
            "top_modules": top_modules,
            "affinities": sorted(affinities, key=lambda x: x["pmi"], reverse=True)[:30],
            "by_module": by_module_out,
        }

    # Guardar
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n[C]  Escrito: {OUTPUT_PATH}")
    print(f"[C]  {len(result)} tipos de sección con afinidades")

    # Demo: mostrar top affinities por sección
    for st, data in sorted(result.items()):
        top3 = data["affinities"][:3]
        print(f"\n      {st}:")
        for a in top3:
            print(f"        PMI {a['pmi']:6.2f}  {a['pair'][0]:30s} + {a['pair'][1]:30s}  ({a['count']}x)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
