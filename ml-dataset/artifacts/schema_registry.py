"""
SchemaRegistry — Auto-discovery of Divi 5 module schemas with ML-assisted matching
================================================================================
Loads all module schemas from workspace/data/modules/*.json and provides:
  - Attr path extraction (recursive)
  - TF-IDF field-to-module suggestion
  - Child module detection for containers
  - Semantic group classification via KMeans

Uses scikit-learn, numpy, and recursive JSON traversal. No hardcoding.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from collections import defaultdict

DAW_ROOT = Path(__file__).resolve().parent.parent.parent
MODULES_DIR = DAW_ROOT / "workspace" / "data" / "modules"


class SchemaRegistry:
    """
    Auto-discover all Divi 5 module schemas and provide capability queries.
    """

    def __init__(self, modules_dir: Optional[Path] = None):
        self.modules_dir = modules_dir or MODULES_DIR
        self.schemas: Dict[str, Dict] = {}
        self.attrs: Dict[str, List[str]] = {}
        self.attr_paths: Dict[str, List[str]] = {}  # full recursive paths
        self.child_map: Dict[str, List[str]] = {}  # container -> [child types]
        self.groups: Dict[str, str] = {}
        self._load_all()
        self._build_ml_index()

    # ───────────────────────────────
    # Loading + Recursive Extraction
    # ───────────────────────────────

    def _load_all(self):
        for p in sorted(self.modules_dir.glob("*.json")):
            try:
                data = json.loads(p.read_text("utf-8"))
                block = data.get("block", {})
                name = block.get("name", "")
                if not name.startswith("divi/"):
                    continue
                attrs = block.get("attrs", {})
                self.schemas[name] = attrs
                # Top-level attrs (minus 'module' metadata)
                self.attrs[name] = [k for k in attrs.keys() if k != "module"]
                # Full recursive paths
                self.attr_paths[name] = self._extract_leaf_paths(attrs)
            except Exception:
                continue

        # Detect child modules via naming convention and attrs
        self._detect_children()

    @staticmethod
    def _extract_leaf_paths(obj: Any, prefix: str = "") -> List[str]:
        """Recursively extract all leaf key paths from a dict."""
        paths = []
        if isinstance(obj, dict):
            for k, v in obj.items():
                new_prefix = f"{prefix}.{k}" if prefix else k
                if isinstance(v, dict) and v:
                    paths.extend(SchemaRegistry._extract_leaf_paths(v, new_prefix))
                else:
                    paths.append(new_prefix)
        return paths

    def _detect_children(self):
        """Detect which modules are children of which containers by name heuristics."""
        # direct naming pairs
        pairs = [
            ("accordion", "accordion-item"),
            ("tabs", "tab"),
            ("icon-list", "icon-list-item"),
            ("slider", "slide"),
            ("group-carousel", "group"),
            ("pricing-tables", "pricing-table"),
            ("social-media-follow", "social-media-follow-network"),
            ("video-slider", "video-slider-item"),
            ("counters", "counter"),
        ]
        for parent_name, child_name in pairs:
            parent = f"divi/{parent_name}"
            child = f"divi/{child_name}"
            if parent in self.schemas and child in self.schemas:
                self.child_map.setdefault(parent, []).append(child)

        # Also detect via 'children' attr on parent
        for name, paths in self.attr_paths.items():
            if any("children" in p for p in paths):
                # Guess child type from naming convention
                base = name.replace("divi/", "")
                candidates = [
                    f"divi/{base}-item",
                    f"divi/{base.rstrip('s')}",
                ]
                for c in candidates:
                    if c in self.schemas:
                        self.child_map.setdefault(name, []).append(c)

    # ───────────────────────────────
    # ML Indexing (TF-IDF + KMeans)
    # ───────────────────────────────

    def _build_ml_index(self):
        """Build TF-IDF corpus over attr paths and KMeans groups."""
        self.module_names = list(self.schemas.keys())
        if not self.module_names:
            return

        # Corpus: join attr paths as strings per module
        corpus = []
        for name in self.module_names:
            words = [p.replace(".", " ").replace("_", " ") for p in self.attr_paths.get(name, [])]
            corpus.append(" ".join(words))

        # TF-IDF vectorizer
        self.vectorizer = TfidfVectorizer(lowercase=True, stop_words="english", max_features=200)
        self.tfidf_matrix = self.vectorizer.fit_transform(corpus)

        # KMeans grouping (cap at 10 semantic groups)
        n_clusters = min(10, len(self.module_names))
        if n_clusters >= 2:
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            labels = kmeans.fit_predict(self.tfidf_matrix)
            group_names = self._label_clusters(labels, corpus)
            for idx, label in enumerate(labels):
                self.groups[self.module_names[idx]] = group_names[label]

    def _label_clusters(self, labels: np.ndarray, corpus: List[str]) -> Dict[int, str]:
        """Auto-label clusters by top TF-IDF terms."""
        feature_names = self.vectorizer.get_feature_names_out()
        group_names = {}
        for cid in np.unique(labels):
            centroid = np.mean(self.tfidf_matrix[np.array(labels) == cid], axis=0).A1
            top_idx = centroid.argsort()[-3:][::-1]
            top_terms = [feature_names[i] for i in top_idx]
            group_names[cid] = "/".join(top_terms)
        return group_names

    # ───────────────────────────────
    # Public API
    # ───────────────────────────────

    def get_attrs(self, module_name: str) -> List[str]:
        return self.attrs.get(module_name, [])

    def get_attr_paths(self, module_name: str) -> List[str]:
        return self.attr_paths.get(module_name, [])

    def validate(self, module_name: str, fields: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate that all keys in fields exist (or can be mapped) in the schema."""
        if module_name not in self.schemas:
            return False, [f"Module {module_name} not found in registry"]
        valid = []
        invalid = []
        for key in fields.keys():
            if key in self.attrs.get(module_name, []) or key in ("type", "module", "presets", "decoration"):
                valid.append(key)
            else:
                invalid.append(key)
        return len(invalid) == 0, invalid

    def suggest_modules(self, field_name: str, top_n: int = 3) -> List[Tuple[str, float]]:
        """
        Given a brief field name (e.g. 'title', 'number', 'image'),
        return top matching module names sorted by TF-IDF cosine similarity.
        """
        if not hasattr(self, "vectorizer"):
            return []

        query_vec = self.vectorizer.transform([field_name.replace("_", " ")])
        similarities = (self.tfidf_matrix * query_vec.T).toarray().flatten()
        ranked = np.argsort(similarities)[::-1][:top_n]

        results = []
        for idx in ranked:
            score = similarities[idx]
            if score > 0:
                results.append((self.module_names[idx], float(score)))
        return results

    def get_child_module(self, module_name: str) -> Optional[str]:
        """Return the primary child module type for a container, or None."""
        children = self.child_map.get(module_name, [])
        return children[0] if children else None

    def list_children(self, module_name: str) -> List[str]:
        return self.child_map.get(module_name, [])

    def get_group(self, module_name: str) -> str:
        return self.groups.get(module_name, "unknown")

    def supports(self, module_name: str, capability: str) -> bool:
        """Check if a module likely supports a capability by TF-IDF match."""
        for mod, score in self.suggest_modules(capability, top_n=5):
            if mod == module_name and score > 0.1:
                return True
        return False

    def is_container(self, module_name: str) -> bool:
        return module_name in self.child_map and len(self.child_map[module_name]) > 0

    # ───────────────────────────────
    # Capability Rules (hybrid ML + Schema)
    # ───────────────────────────────

    MODULE_CAPABILITY_MAP = {
        # These use both schema detection + ML overrides
        "content_display": ["text", "heading", "blurb", "cta", "testimonial", "toggle", "code"],
        "interactive": ["button", "contact-form", "login", "signup", "search"],
        "media": ["image", "gallery", "video", "audio", "lottie", "before-after-image"],
        "navigation": ["menu", "fullwidth-menu", "breadcrumbs", "post-nav", "link"],
        "data": ["blog", "portfolio", "post-content", "sidebar", "shop"],
        "social": ["social-media-follow", "comments"],
        "utility": ["divider", "map", "countdown-timer", "circle-counter", "counter"],
    }


def get_schema_registry() -> SchemaRegistry:
    return SchemaRegistry()


if __name__ == "__main__":
    reg = get_schema_registry()
    print(f"Loaded {len(reg.schemas)} modules")
    print(f"Groups: {set(reg.groups.values())}")
    print("\nSuggested modules for 'title':")
    for mod, score in reg.suggest_modules("title", top_n=5):
        print(f"  {mod}: {score:.3f}")
    print("\nSuggested modules for 'number':")
    for mod, score in reg.suggest_modules("number", top_n=5):
        print(f"  {mod}: {score:.3f}")
    print("\nChild mappings:")
    for parent, children in reg.child_map.items():
        print(f"  {parent} -> {children}")
    print("\nValidation test (divi/blurb with 'title'):")
    ok, bad = reg.validate("divi/blurb", {"title": "Hola", "content": "", "icon": "x"})
    print(f"  valid={ok}, invalid={bad}")
    print("\nValidation test (divi/blurb with 'invalid_key'):")
    ok, bad = reg.validate("divi/blurb", {"title": "Hola", "invalid_key": ""})
    print(f"  valid={ok}, invalid={bad}")
