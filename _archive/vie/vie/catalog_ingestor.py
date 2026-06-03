"""CatalogIngestor — Lee 877 templates reales y extrae patrones de composicion.

Uso:
    from vie.catalog_ingestor import CatalogIngestor
    ingestor = CatalogIngestor("DAW_bundle/workspace/sections/catalog")
    patterns = ingestor.get_patterns("hero")
    # Retorna: [{"column_structure": "2_5,3_5", "modules": ["divi/heading","divi/text","divi/button"], "frequency": 12}, ...]
"""
import glob
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Optional


class CatalogIngestor:
    """Ingestor de catalogo de templates de seccion."""

    def __init__(self, catalog_dir: str = "DAW_bundle/workspace/sections/catalog"):
        self.catalog_dir = Path(catalog_dir)
        self._patterns: Dict[str, List[Dict]] = {}
        self._raw: List[Dict] = []
        self._load_all()

    def _load_all(self):
        """Carga todos los templates .section.json del catalogo."""
        pattern = str(self.catalog_dir / "*.section.json")
        files = glob.glob(pattern)
        for f in files:
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                    data["_filename"] = Path(f).name
                    self._raw.append(data)
            except Exception:
                continue

    def _extract_section_type(self, filename: str) -> str:
        """Infiere section_type desde el nombre del archivo."""
        lower = filename.lower()
        mappings = [
            ("hero", "hero"), ("header", "hero"), ("banner", "hero"),
            ("feature", "features"), ("service", "features"), ("benefit", "features"),
            ("about", "content"), ("story", "content"), ("mission", "content"),
            ("stat", "stats"), ("counter", "stats"), ("number", "stats"),
            ("testimonial", "testimonials"), ("review", "testimonials"), ("quote", "testimonials"),
            ("pricing", "pricing"), ("price", "pricing"), ("plan", "pricing"),
            ("gallery", "gallery"), ("portfolio", "gallery"), ("slider", "gallery"),
            ("contact", "contact"), ("form", "contact"), ("map", "contact"),
            ("cta", "cta"), ("call", "cta"), ("action", "cta"),
            ("team", "team"), ("staff", "team"), ("people", "team"),
            ("faq", "faq"), ("question", "faq"), ("accordion", "faq"),
            ("trust", "trust-bar"), ("logo", "trust-bar"), ("partner", "trust-bar"),
            ("process", "process"), ("step", "process"), ("timeline", "process"),
        ]
        for keyword, stype in mappings:
            if keyword in lower:
                return stype
        return "generic"

    def _extract_modules_from_row(self, row: Dict) -> List[str]:
        """Extrae lista de tipos de modulo de una fila."""
        modules = []
        columns = row.get("columns", [])
        if not columns and row.get("modules"):
            columns = [{"modules": row["modules"]}]
        for col in columns:
            for mod in col.get("modules", []):
                mod_type = mod.get("type", mod.get("_type", "divi/text"))
                modules.append(mod_type)
        return modules

    def _extract_layout_signature(self, row: Dict) -> Dict:
        """Extrae la firma de layout de una fila."""
        cols = row.get("columns", [])
        if not cols and row.get("modules"):
            cols = [{"type": "4_4", "modules": row["modules"]}]
        col_types = [c.get("type", "4_4") for c in cols]
        column_structure = ",".join(col_types) if len(col_types) > 1 else col_types[0] if col_types else "4_4"
        modules = self._extract_modules_from_row(row)
        return {
            "column_structure": column_structure,
            "modules": modules,
            "module_count": len(modules),
        }

    def get_patterns(self, section_type: str, n: int = 5) -> List[Dict]:
        """Retorna los N patrones de layout mas frecuentes para un section_type."""
        if section_type in self._patterns:
            return self._patterns[section_type][:n]

        signatures = []
        for template in self._raw:
            inferred = self._extract_section_type(template.get("_filename", ""))
            if inferred == section_type or section_type == "generic":
                rows = template.get("rows", [])
                for row in rows:
                    sig = self._extract_layout_signature(row)
                    signatures.append(sig)

        if not signatures:
            self._patterns[section_type] = []
            return []

        # Agrupar por firma (column_structure + primeros 3 modulos)
        def key(s):
            mods_tuple = tuple(s["modules"][:3])
            return (s["column_structure"], mods_tuple)

        grouped = defaultdict(list)
        for sig in signatures:
            grouped[key(sig)].append(sig)

        patterns = []
        for (cs, mods), items in grouped.items():
            all_modules = []
            for item in items:
                all_modules.extend(item["modules"])
            module_freq = Counter(all_modules)
            top_modules = [m for m, _ in module_freq.most_common(6)]
            patterns.append({
                "column_structure": cs,
                "modules": top_modules,
                "frequency": len(items),
                "avg_module_count": sum(i["module_count"] for i in items) / len(items),
            })

        patterns.sort(key=lambda x: x["frequency"], reverse=True)
        self._patterns[section_type] = patterns
        return patterns[:n]

    def get_layouts_for_page_type(self, page_type: str, section_type: str) -> List[Dict]:
        """Retorna layouts priorizados segun page_type + section_type."""
        all_patterns = self.get_patterns(section_type, n=10)

        # Prioridades por page_type
        preferred_structures = {
            "home": {
                "hero": ["2_5,3_5", "1_2,1_2", "4_4"],
                "features": ["1_3,1_3,1_3", "1_2,1_2", "1_4,1_4,1_4,1_4"],
                "stats": ["1_4,1_4,1_4,1_4", "1_3,1_3,1_3"],
                "testimonials": ["1_3,1_3,1_3", "1_2,1_2"],
                "pricing": ["1_3,1_3,1_3"],
                "cta": ["4_4", "1_2,1_2"],
            },
            "about": {
                "hero": ["4_4", "1_2,1_2"],
                "content": ["1_2,1_2", "3_5,2_5"],
                "features": ["1_2,1_2", "1_3,1_3,1_3"],
                "team": ["1_3,1_3,1_3", "1_4,1_4,1_4,1_4"],
                "stats": ["1_4,1_4,1_4,1_4"],
                "cta": ["4_4"],
            },
            "services": {
                "hero": ["1_2,1_2", "2_5,3_5"],
                "features": ["1_2,1_2", "1_3,1_3,1_3"],
                "pricing": ["1_3,1_3,1_3"],
                "testimonials": ["1_2,1_2", "1_3,1_3,1_3"],
                "cta": ["4_4", "1_2,1_2"],
            },
            "destinations": {
                "hero": ["4_4", "1_2,1_2"],
                "gallery": ["4_4", "1_3,1_3,1_3"],
                "features": ["1_3,1_3,1_3"],
                "testimonials": ["1_3,1_3,1_3"],
                "cta": ["4_4"],
            },
            "contact": {
                "hero": ["4_4"],
                "content": ["1_2,1_2"],
                "contact": ["1_2,1_2"],
                "cta": ["4_4"],
            },
        }

        preferred = preferred_structures.get(page_type, {}).get(section_type, [])
        if not preferred:
            return all_patterns[:3]

        # Ordenar: primero los que coinciden con preferred, luego el resto
        scored = []
        for p in all_patterns:
            cs = p["column_structure"]
            if cs in preferred:
                p["priority"] = len(preferred) - preferred.index(cs)  # Mayor prioridad = indice menor
            else:
                p["priority"] = 0
            scored.append(p)

        scored.sort(key=lambda x: (x["priority"], x["frequency"]), reverse=True)
        return scored[:3]
