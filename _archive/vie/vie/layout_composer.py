"""LayoutComposer — Selecciona layouts asimetricos por page_type, section_type y variant_hint.

Integra UXProBridge para usar variant_hint y CatalogIngestor para inspirarse en templates reales.
"""
from typing import Any, Dict, List, Optional

from vie.catalog_ingestor import CatalogIngestor


class LayoutComposer:
    """Compone filas (rows) con column_structure y modulos distribuidos."""

    # Layouts por page_type + section_type
    _LAYOUTS = {
        "landing": {
            "hero": {"column_structure": "2_5,3_5", "module_distribution": [0, 1]},
            "trust-bar": {"column_structure": "1_5,1_5,1_5,1_5,1_5", "module_distribution": [0, 1, 2, 3, 4]},
            "features": {"column_structure": "1_3,1_3,1_3", "module_distribution": [0, 1, 2]},
            "stats": {"column_structure": "1_4,1_4,1_4,1_4", "module_distribution": [0, 1, 2, 3]},
            "testimonials": {"column_structure": "1_3,1_3,1_3", "module_distribution": [0, 1, 2]},
            "cta": {"column_structure": "4_4", "module_distribution": [0]},
        },
        "home": {
            "hero": {"column_structure": "2_5,3_5", "module_distribution": [0, 1]},
            "features": {"column_structure": "1_3,1_3,1_3", "module_distribution": [0, 1, 2]},
            "stats": {"column_structure": "1_4,1_4,1_4,1_4", "module_distribution": [0, 1, 2, 3]},
            "testimonials": {"column_structure": "1_3,1_3,1_3", "module_distribution": [0, 1, 2]},
            "pricing": {"column_structure": "1_3,1_3,1_3", "module_distribution": [0, 1, 2]},
            "cta": {"column_structure": "4_4", "module_distribution": [0]},
        },
        "portfolio": {
            "hero": {"column_structure": "2_5,3_5", "module_distribution": [0, 1]},
            "gallery": {"column_structure": "1_2,1_2", "module_distribution": [0, 1]},
            "stats": {"column_structure": "1_4,1_4,1_4,1_4", "module_distribution": [0, 1, 2, 3]},
            "testimonials": {"column_structure": "1_3,1_3,1_3", "module_distribution": [0, 1, 2]},
            "cta": {"column_structure": "4_4", "module_distribution": [0]},
        },
        "pricing": {
            "hero": {"column_structure": "4_4", "module_distribution": [0]},
            "pricing": {"column_structure": "1_3,1_3,1_3", "module_distribution": [0, 1, 2]},
            "faq": {"column_structure": "1_2,1_2", "module_distribution": [0, 1]},
            "testimonials": {"column_structure": "1_2,1_2", "module_distribution": [0, 1]},
            "cta": {"column_structure": "4_4", "module_distribution": [0]},
        },
        "about": {
            "hero": {"column_structure": "4_4", "module_distribution": [0]},
            "trust-bar": {"column_structure": "1_5,1_5,1_5,1_5,1_5", "module_distribution": [0, 1, 2, 3, 4]},
            "content": {"column_structure": "1_2,1_2", "module_distribution": [0, 1]},
            "features": {"column_structure": "1_2,1_2", "module_distribution": [0, 1]},
            "team": {"column_structure": "1_3,1_3,1_3", "module_distribution": [0, 1, 2]},
            "stats": {"column_structure": "1_4,1_4,1_4,1_4", "module_distribution": [0, 1, 2, 3]},
            "cta": {"column_structure": "4_4", "module_distribution": [0]},
        },
        "services": {
            "hero": {"column_structure": "1_2,1_2", "module_distribution": [0, 1]},
            "features": {"column_structure": "1_2,1_2", "module_distribution": [0, 1]},
            "process": {"column_structure": "1_4,1_4,1_4,1_4", "module_distribution": [0, 1, 2, 3]},
            "pricing": {"column_structure": "1_3,1_3,1_3", "module_distribution": [0, 1, 2]},
            "testimonials": {"column_structure": "1_2,1_2", "module_distribution": [0, 1]},
            "cta": {"column_structure": "4_4", "module_distribution": [0]},
        },
        "contact": {
            "hero": {"column_structure": "4_4", "module_distribution": [0]},
            "content": {"column_structure": "1_2,1_2", "module_distribution": [0, 1]},
            "contact": {"column_structure": "1_2,1_2", "module_distribution": [0, 1]},
            "cta": {"column_structure": "4_4", "module_distribution": [0]},
        },
        "destinations": {
            "hero": {"column_structure": "4_4", "module_distribution": [0]},
            "slider": {"column_structure": "4_4", "module_distribution": [0]},
            "features": {"column_structure": "1_3,1_3,1_3", "module_distribution": [0, 1, 2]},
            "testimonials": {"column_structure": "1_3,1_3,1_3", "module_distribution": [0, 1, 2]},
            "cta": {"column_structure": "4_4", "module_distribution": [0]},
        },
    }

    def __init__(self, catalog_ingestor: Optional[CatalogIngestor] = None):
        self.catalog = catalog_ingestor or CatalogIngestor()

    def compose_rows(self, section_type: str, page_type: str, modules: List[Dict],
                     variant_hint: str = "", profile: Any = None) -> List[Dict]:
        """Compone filas con column_structure y distribuye modulos en columnas."""
        page_layouts = self._LAYOUTS.get(page_type, self._LAYOUTS["home"])
        layout_def = page_layouts.get(section_type, {"column_structure": "4_4", "module_distribution": [0]})

        cs = layout_def["column_structure"]
        col_types = cs.split(",")
        n_cols = len(col_types)

        # Si tenemos pocos modulos y muchas columnas, ajustar
        if len(modules) < n_cols and section_type in ("features", "stats", "testimonials", "pricing", "team"):
            # Agrupar modulos por columna
            cols_modules = [[] for _ in range(n_cols)]
            for i, mod in enumerate(modules):
                target_col = i % n_cols
                cols_modules[target_col].append(mod)
        elif section_type in ("hero", "content", "contact"):
            # Hero/content: primera columna = texto, segunda = imagen/form
            cols_modules = [[] for _ in range(n_cols)]
            text_mods = [m for m in modules if m.get("_semantic_style") in ("eyebrow", "heading", "body", "button", "primary", "secondary")]
            media_mods = [m for m in modules if m.get("_semantic_style") in ("image", "video", "gallery", "slider", "map", "form")]
            other_mods = [m for m in modules if m.get("_semantic_style") not in ("eyebrow", "heading", "body", "button", "primary", "secondary", "image", "video", "gallery", "slider", "map", "form")]

            if n_cols == 2:
                cols_modules[0] = text_mods + other_mods
                cols_modules[1] = media_mods
            elif n_cols == 1:
                cols_modules[0] = modules
            else:
                # 3_5,2_5 hero: primera columna texto, segunda imagen
                cols_modules[0] = text_mods + other_mods
                cols_modules[1] = media_mods
        else:
            # Default: distribuir equitativamente
            cols_modules = [[] for _ in range(n_cols)]
            for i, mod in enumerate(modules):
                target_col = i % n_cols
                cols_modules[target_col].append(mod)

        # Construir rows
        columns = []
        for i, col_type in enumerate(col_types):
            col = {
                "type": col_type,
                "modules": cols_modules[i] if i < len(cols_modules) else [],
            }
            columns.append(col)

        return [{
            "type": "divi/row",
            "module": "divi/row",
            "column_structure": cs,
            "columns": columns,
        }]

    def get_layout_signature(self, page_type: str, section_type: str) -> str:
        """Retorna la firma del layout para logging/testing."""
        page_layouts = self._LAYOUTS.get(page_type, {})
        layout_def = page_layouts.get(section_type, {"column_structure": "4_4"})
        return layout_def["column_structure"]
