#!/usr/bin/env python3
"""
Artefacto B2: Slot Assigner (Hungarian algorithm)
Propósito: Asignación global óptima de templates a secciones usando
cobertura de slots. Reemplaza la búsqueda semántica por nombre con
optimización combinatoria sobre la estructura real de los templates.

Usa slots_offered extraídos en dataset.jsonl por extract.py
contra los slots necesarios de cada sección del brief.
"""

import json, re, pickle, os, sys, math
from pathlib import Path
from collections import defaultdict
import numpy as np

ARTIFACTS_DIR = Path(__file__).resolve().parent
DAW_ROOT = ARTIFACTS_DIR.parent.parent
DATASET_PATH = ARTIFACTS_DIR.parent / "dataset.jsonl"
CATALOG_INDEX_PATH = ARTIFACTS_DIR / "slot-catalog.pkl"

logger = print


def get_slots_needed_from_brief_section(sec: dict) -> dict:
    """Calcula cuántos slots de cada tipo necesita una sección del brief."""
    needed = {
        "titles": 0,
        "paragraphs": 0,
        "buttons": 0,
        "images": 0,
        "features": 0,
        "testimonials": 0,
        "stats": 0,
        "logos": 0,
        "items": 0
    }
    
    # Titles: eyebrow, title
    if sec.get("eyebrow"):
        needed["titles"] += 1
    if sec.get("title"):
        needed["titles"] += 1
        
    # Paragraphs: text, body
    if sec.get("text"):
        needed["paragraphs"] += 1
    if sec.get("body"):
        needed["paragraphs"] += 1
        
    # Buttons: btn_primary_text, btn_secondary_text
    if sec.get("btn_primary_text"):
        needed["buttons"] += 1
    if sec.get("btn_secondary_text"):
        needed["buttons"] += 1
        
    # Images: image, media_icon, media, avatar
    if sec.get("image") or sec.get("media_icon") or sec.get("media") or sec.get("avatar"):
        needed["images"] += 1
        
    # Repeat list types:
    if isinstance(sec.get("features"), list):
        needed["features"] += len(sec["features"])
    if isinstance(sec.get("testimonials"), list):
        needed["testimonials"] += len(sec["testimonials"])
    if isinstance(sec.get("stats"), list):
        needed["stats"] += len(sec["stats"])
    if isinstance(sec.get("logos"), list):
        needed["logos"] += len(sec["logos"])
    if isinstance(sec.get("items"), list):
        needed["items"] += len(sec["items"])
            
    return needed


class IDFWeights:
    """IDF weighting para los tipos de slot."""
    def __init__(self):
        self.df = {}
        self.idf = {}
        self.N = 0

    def build(self, catalog: dict):
        self.df = {k: 0 for k in ("titles", "paragraphs", "buttons", "images", "features", "testimonials", "stats", "logos", "items")}
        self.N = 0
        for cat, entries in catalog.items():
            for name, slots_offered, _, _ in entries:
                self.N += 1
                for s in self.df:
                    if slots_offered.get(s, 0) > 0:
                        self.df[s] += 1
        import math
        self.idf = {}
        for s, df in self.df.items():
            if df == 0:
                self.idf[s] = 1.0
            else:
                self.idf[s] = math.log(self.N / df) + 1.0
        self.max_idf = max(self.idf.values()) if self.idf else 1.0

    def weight(self, s: str) -> float:
        return self.idf.get(s, 1.0)


_slot_idf = IDFWeights()


def slot_coverage(slots_needed: dict, slots_offered: dict) -> float:
    """
    F1 score IDF-ponderado entre brief y template.
    Penaliza templates que tienen slots excedentes o faltantes.
    """
    precision_num = 0.0
    precision_den = 0.0
    recall_num = 0.0
    recall_den = 0.0
    
    for slot_type, weight in _slot_idf.idf.items():
        needed = slots_needed.get(slot_type, 0)
        offered = slots_offered.get(slot_type, 0)
        
        # Matched es lo máximo que pudimos usar de lo que se ofreció (limitado por lo pedido)
        matched = min(needed, offered)
        
        # Recall: ¿De lo que pedí, cuánto me dieron?
        recall_num += matched * weight
        recall_den += needed * weight
        
        # Precision: ¿De lo que ofreció el template, cuánto realmente usé?
        # Penaliza templates inflados
        precision_num += matched * weight
        precision_den += offered * weight
        
    recall = recall_num / recall_den if recall_den > 0 else 1.0
    precision = precision_num / precision_den if precision_den > 0 else 1.0
    
    if precision + recall == 0:
        return 0.0
        
    return 2 * (precision * recall) / (precision + recall)


class SlotAssigner:
    """Asigna templates a secciones usando Hungarian sobre slot coverage."""

    def __init__(self):
        self.catalog = {}  # category -> [(template_name, slots_offered_dict, module_types, columns_count)]
        self.template_cache = {}  # template_name -> template dict
        self._loaded = False
        self.categories = set()

    def build(self, dataset_path: Path = DATASET_PATH):
        """Lee el dataset.jsonl y construye el catálogo de slots."""
        logger(f"[B2] Cargando dataset desde {dataset_path}...", file=sys.stderr)
        if not dataset_path.exists():
            logger(f"[B2] Error: No se encontró {dataset_path}", file=sys.stderr)
            return

        # Intentar cargar mapa de categorías desde embeddings.pkl para consistencia
        embeddings_path = DAW_ROOT / "workspace" / "catalog" / "embeddings.pkl"
        name_to_cat = {}
        if embeddings_path.exists():
            try:
                with open(embeddings_path, "rb") as f:
                    emb_data = pickle.load(f)
                    for item in emb_data.get("items", []):
                        name_to_cat[item["name"]] = item.get("category", "generic")
            except Exception as e:
                logger(f"[B2] Warning al cargar embeddings.pkl: {e}", file=sys.stderr)

        def get_fallback_category(name: str) -> str:
            name_lower = name.lower()
            if "hero" in name_lower or "banner" in name_lower:
                return "hero"
            elif "about" in name_lower:
                return "about"
            elif "feature" in name_lower or "service" in name_lower:
                return "features"
            elif "testimonial" in name_lower or "review" in name_lower:
                return "testimonials"
            elif "pricing" in name_lower or "price" in name_lower:
                return "pricing"
            elif "contact" in name_lower or "get in touch" in name_lower:
                return "contact"
            elif "cta" in name_lower or "call to action" in name_lower:
                return "cta"
            elif "gallery" in name_lower or "portfolio" in name_lower:
                return "gallery"
            elif "stat" in name_lower or "counter" in name_lower:
                return "stats"
            elif "logo" in name_lower or "brand" in name_lower:
                return "logos"
            elif "team" in name_lower:
                return "team"
            elif "faq" in name_lower:
                return "faq"
            elif "footer" in name_lower:
                return "footer"
            return "generic"

        cat_map = defaultdict(list)
        count = 0
        
        with open(dataset_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    item = json.loads(line)
                    name = item.get("source")
                    if not name:
                        continue
                    
                    # Determinar categoría
                    cat = name_to_cat.get(name, get_fallback_category(name))
                    slots_offered = item.get("slots_offered", {})
                    module_types = item.get("module_types", [])
                    columns_count = item.get("columns_count", 1)
                    
                    cat_map[cat].append((name, slots_offered, module_types, columns_count))
                    self.template_cache[name] = item
                    self.categories.add(cat)
                    count += 1
                except Exception as e:
                    logger(f"[B2] Error procesando línea: {e}", file=sys.stderr)

        self.catalog = dict(cat_map)
        self._loaded = True
        _slot_idf.build(self.catalog)
        
        logger(f"[B2] {count} templates indexados en {len(self.catalog)} categorías", file=sys.stderr)
        logger(f"[B2] Pesos IDF calculados:", file=sys.stderr)
        for s, w in _slot_idf.idf.items():
            logger(f"  - {s}: {w:.4f}", file=sys.stderr)

    def save(self, path: Path = CATALOG_INDEX_PATH):
        """Guarda el catálogo como pickle."""
        data = {
            "catalog": self.catalog,
            "categories": sorted(self.categories),
            "template_cache_keys": list(self.template_cache.keys()),
            "slot_idf_df": dict(_slot_idf.df),
            "slot_idf_N": _slot_idf.N,
        }
        with open(path, "wb") as f:
            pickle.dump(data, f)
        logger(f"[B2] Catálogo guardado en: {path}", file=sys.stderr)

    def load(self, path: Path = CATALOG_INDEX_PATH):
        """Carga catálogo desde pickle."""
        if not path.exists():
            logger(f"[B2] No encontrado: {path}. Construyendo...", file=sys.stderr)
            self.build()
            return
        try:
            with open(path, "rb") as f:
                data = pickle.load(f)
            self.catalog = data["catalog"]
            self.categories = set(data["categories"])
            self._loaded = True
            _slot_idf.df = data.get("slot_idf_df", {})
            _slot_idf.N = data.get("slot_idf_N", sum(len(v) for v in self.catalog.values()))
            
            import math
            _slot_idf.idf = {}
            for s, df in _slot_idf.df.items():
                if df == 0:
                    _slot_idf.idf[s] = 1.0
                else:
                    _slot_idf.idf[s] = math.log(_slot_idf.N / df) + 1.0
            _slot_idf.max_idf = max(_slot_idf.idf.values()) if _slot_idf.idf else 1.0
            
            logger(f"[B2] Catálogo cargado: {sum(len(v) for v in self.catalog.values())} templates en {len(self.catalog)} categorías", file=sys.stderr)
        except Exception as e:
            logger(f"[B2] Error al cargar catálogo de slots: {e}. Reconstruyendo...", file=sys.stderr)
            self.build()

    def assign(self, sections: list, schema: dict) -> list:
        """
        Asigna templates a secciones vía Hungarian.

        Args:
            sections: list de dicts de sección del brief
            schema: section-schema.json dict

        Returns:
            list de (section_index, template_name, score) del mismo largo que sections.
        """
        if not self._loaded:
            self.load()

        M = len(sections)
        if M == 0:
            return []

        # Convertir secciones a slots_needed y calcular columnas esperadas
        brief_sigs = []
        section_types = []
        expected_columns_by_section = []
        for sec in sections:
            sig = get_slots_needed_from_brief_section(sec)
            brief_sigs.append(sig)
            
            st = sec.get("section_type", "generic")
            section_types.append(st)

            # Tie-breaking esperado: número de columnas que mejor calzan
            item_counts = [sig[k] for k in ("features", "testimonials", "stats", "logos", "items")]
            max_items = max(item_counts) if item_counts else 0
            if max_items > 0:
                expected = max_items
            elif st in ("hero", "content", "content-list"):
                expected = 2  # split layout
            else:
                expected = 1  # cta, hero-centered, etc.
            expected_columns_by_section.append(expected)

        def map_section_type_to_category(st: str) -> str:
            """Map brief section types to canonical catalog categories."""
            st_lower = st.lower()
            if st_lower in ("hero", "hero-centered", "hero-split", "banner"):
                return "hero"
            if st_lower in ("features", "content-list", "services", "items"):
                return "features"
            if st_lower in ("testimonials", "reviews"):
                return "testimonials"
            if st_lower in ("stats", "counters", "metrics"):
                return "stats"
            if st_lower in ("logos", "brands", "trust-bar"):
                return "logos"
            if st_lower in ("cta", "call-to-action", "newsletter"):
                return "cta"
            if st_lower in ("content", "about", "about-us"):
                return "about"
            if st_lower in ("team", "team-members"):
                return "team"
            if st_lower in ("pricing", "plans"):
                return "pricing"
            if st_lower in ("gallery", "portfolio"):
                return "gallery"
            if st_lower in ("contact", "contact-form", "get-in-touch"):
                return "contact"
            if st_lower in ("faq", "faqs"):
                return "faq"
            return "generic"

        # Obtener candidatos por sección
        candidates_by_section = []
        for i, st in enumerate(section_types):
            cat = map_section_type_to_category(st)
            pool = self.catalog.get(cat, [])
            if not pool:
                # fallback: todos los templates
                pool = [(n, s, m, c) for cat in self.catalog.values() for n, s, m, c in cat]
            
            scored = []
            expected_col = expected_columns_by_section[i]
            for name, tslots, mods, tcol in pool:
                cov = slot_coverage(brief_sigs[i], tslots)
                if cov > 0:
                    # Tie-breaking: +0.02 si el conteo de columnas coincide
                    if expected_col == tcol:
                        cov += 0.02
                    scored.append((cov, name, tslots, mods, tcol))
            
            scored.sort(key=lambda x: -x[0])
            candidates_by_section.append(scored[:50])  # top 50 candidatos

        # Construir matriz de costos para el algoritmo Húngaro (minimización)
        max_candidates = max(len(c) for c in candidates_by_section)
        if max_candidates < M:
            max_candidates = M

        cost_matrix = np.ones((M, max_candidates)) * 1.0
        for i, candidates in enumerate(candidates_by_section):
            for j in range(min(len(candidates), max_candidates)):
                # costo = 1 - f1 (minimizar costo = maximizar F1)
                cost_matrix[i, j] = 1.0 - candidates[j][0]
            # Rellenar el resto con costo alto
            for j in range(len(candidates), max_candidates):
                cost_matrix[i, j] = 1.0

        # Algoritmo Húngaro (Munkres)
        from scipy.optimize import linear_sum_assignment
        row_ind, col_ind = linear_sum_assignment(cost_matrix)

        result = []
        for i in range(M):
            if i in row_ind:
                idx_in_assignment = list(row_ind).index(i)
                j = col_ind[idx_in_assignment]
                if j < len(candidates_by_section[i]):
                    cov, name, tslots, mods, tcol = candidates_by_section[i][j]
                    # Deshacer el bono de empate del reporte para reportar F1 real
                    reported_score = max(0.0, cov - 0.02) if expected_columns_by_section[i] == tcol else cov
                    result.append((i, name, round(reported_score, 4)))
                else:
                    result.append((i, None, 0.0))
            else:
                result.append((i, None, 0.0))

        return result


def main():
    assigner = SlotAssigner()
    assigner.build()
    assigner.save()
    logger(f"[B2] Build completo. {sum(len(v) for v in assigner.catalog.values())} templates totales",
           file=sys.stderr)

    # Demo
    demo_sections = [
        {"section_type": "hero", "title": "Bienvenidos", "text": "Descripcion",
         "btn_primary_text": "Click", "btn_primary_url": "/go"},
        {"section_type": "features", "title": "Servicios",
         "features": [{"title": "A", "icon": "&#xe065;", "text": "Desc A"},
                      {"title": "B", "icon": "&#xe0bf;", "text": "Desc B"}]},
        {"section_type": "cta", "title": "Contacto", "text": "Llamanos",
         "btn_primary_text": "Ir", "btn_primary_url": "/ir"},
    ]
    results = assigner.assign(demo_sections, {})
    print("Demo assignment:")
    for i, name, score in results:
        print(f"  [{i}] {demo_sections[i]['section_type']}: {name} (cov={score})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
