import json
from typing import List, Dict, Any, Optional

class DiviObject:
    """Base class that allows arbitrary keyword arguments and serializes cleanly."""
    def __init__(self, **kwargs):
        self.attributes = kwargs

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict, removing None values."""
        return {k: v for k, v in self.attributes.items() if v is not None}

class Module(DiviObject):
    """
    Represents a Divi module (divi/text, divi/blurb, divi/image, etc).
    Accepts arbitrary kwargs like presets=[], decoration={}, headingFont={}, content="..."
    """
    def __init__(self, module_type: str, **kwargs):
        super().__init__(**kwargs)
        self.module_type = module_type

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d['module'] = self.module_type
        return d

class Row(DiviObject):
    """
    Represents a Divi row structure (e.g. '4_4', '1_2,1_2').
    Automatically manages columns based on the column_structure.
    """
    def __init__(self, columns: str = "4_4", **kwargs):
        super().__init__(**kwargs)
        self.column_structure = columns
        self.columns_data: List[Dict[str, Any]] = []
        
        # Initialize column types based on structure
        types = [t.strip() for t in columns.split(',')]
        for col_type in types:
            self.columns_data.append({
                "type": col_type,
                "modules": []
            })

    def add_module(self, col_index: int, module: Module):
        """Add a module to a specific column index (0-based)"""
        if 0 <= col_index < len(self.columns_data):
            self.columns_data[col_index]["modules"].append(module.to_dict())
        else:
            raise ValueError(f"Invalid column index {col_index} for structure {self.column_structure}")
        return self # For fluent chaining

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d['column_structure'] = self.column_structure
        d['columns'] = self.columns_data
        return d

class Section(DiviObject):
    """
    Represents a Divi section.
    Supports **kwargs for presets, decoration, background_image, bg_gradient, etc.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rows: List[Row] = []

    def add_row(self, row: Row):
        self.rows.append(row)
        return self

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d['rows'] = [r.to_dict() for r in self.rows]
        return d

class Page:
    """Represents the root page structure."""
    def __init__(self, name: str = "Página", description: str = ""):
        self.sections: List[Section] = []

    def add_section(self, section: Section):
        self.sections.append(section)
        return self

    def validate(self):
        """Valida que el schema esté completo y estructuralmente correcto antes de exportar."""
        if not self.sections:
            raise ValueError("❌ Validación fallida: La página no tiene ninguna sección (sections está vacío).")
        
        for s_idx, section in enumerate(self.sections):
            if not section.rows:
                raise ValueError(f"❌ Validación fallida: La sección {s_idx} no tiene filas (rows). Toda sección debe tener al menos un Row.")
            
            for r_idx, row in enumerate(section.rows):
                for c_idx, col in enumerate(row.columns_data):
                    # It's okay if a column is empty, but we can check if modules have types
                    for m_idx, mod in enumerate(col["modules"]):
                        if "module" not in mod or not mod["module"].startswith("divi/"):
                            raise ValueError(f"❌ Validación fallida: El módulo en sección {s_idx}, row {r_idx}, col {c_idx} es inválido o no usa el namespace 'divi/'.")
        
        print("✅ Validación estructural superada. El schema es consistente con el estándar DAW.")
        return True

    def export(self, filepath: str):
        self.validate()  # Ejecutar validación integrada antes de guardar
        data = {
            "sections": [s.to_dict() for s in self.sections]
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ Schema exportado exitosamente a {filepath}")
