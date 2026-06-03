#!/usr/bin/env python3
"""
Artefacto B: Template Semantic Index
Naturaleza: Recuperación de información
Algoritmo: Cosine similarity sobre embeddings de 384 dimensiones (numpy)

Construye un índice desde embeddings.pkl existente y provee búsqueda
semántica sobre los 892 templates del catálogo.

Diferencia con search_catalog.py:
  - search_catalog.py usa bag-of-words casero (TF sin IDF)
  - Este usa los embeddings reales de SentenceTransformer (384-dim)
  - Misma data, algoritmo correcto para el problema
"""

import json, pickle, sys, re, math
from pathlib import Path
from collections import Counter
import numpy as np

DAW_ROOT = Path(__file__).resolve().parent.parent

EMBEDDINGS_PATH = DAW_ROOT / "workspace" / "catalog" / "embeddings.pkl"
DATASET_PATH = DAW_ROOT / "ml-dataset" / "dataset.jsonl"
OUT_DIR = Path(__file__).resolve().parent


class SemanticIndex:
    def __init__(self):
        self.items = []
        self.embeddings = None
        self.norms = None
        self.name_to_item = {}

    def build(self, embeddings_path: Path):
        print(f"[B] Cargando embeddings: {embeddings_path}", file=sys.stderr)
        with open(embeddings_path, "rb") as f:
            data = pickle.load(f)
        self.items = data["items"]
        self.embeddings = np.array(data["embeddings"]).astype(np.float32)

        # Normalizar para cosine similarity directa
        self.norms = np.linalg.norm(self.embeddings, axis=1, keepdims=True)
        self.norms = np.where(self.norms == 0, 1, self.norms)
        self.embeddings_normalized = self.embeddings / self.norms

        # Indexar por nombre
        for item in self.items:
            self.name_to_item[item["name"]] = item

        # Cargar modelo SentenceTransformer una sola vez
        self._load_model()

        print(f"[B]  {len(self.items)} templates indexados ({self.embeddings.shape[1]} dims)", file=sys.stderr)
        cats = set(item.get("category") for item in self.items)
        print(f"[B]  Categorías disponibles: {sorted(cats)}", file=sys.stderr)

    def search(self, query_text: str, category: str | None = None, limit: int = 5) -> list:
        """Busqueda semantica: vectoriza el query y encuentra los mas cercanos"""
        query_vec = self._vectorize(query_text)
        if query_vec is None:
            return self._fallback_search(query_text, category, limit)

        similarities = np.dot(self.embeddings_normalized, query_vec)

        # Filtrar por categoria si se especifica
        if category:
            indices = [
                i for i, item in enumerate(self.items)
                if item.get("category", "").lower() == category.lower()
            ]
            if not indices:
                indices = list(range(len(self.items)))
            sims_subset = similarities[indices]
            top_local = np.argsort(-sims_subset)[:limit]
            top_indices = [indices[i] for i in top_local]
        else:
            top_indices = np.argsort(-similarities)[:limit]

        results = []
        for idx in top_indices:
            item = self.items[idx]
            results.append({
                "name": item["name"],
                "path": item.get("path", ""),
                "category": item.get("category", "generic"),
                "score": round(float(similarities[idx]), 4),
            })
        return results

    def _load_model(self):
        """Carga SentenceTransformer una sola vez, silenciando logs"""
        import os
        old_stderr = sys.stderr
        try:
            sys.stderr = open(os.devnull, "w")
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer("all-MiniLM-L6-v2")
            sys.stderr = old_stderr
            print(f"[B]  Modelo SentenceTransformer cargado", file=sys.stderr)
        except Exception as e:
            sys.stderr = old_stderr
            print(f"[B]  Warning: SentenceTransformer no disponible: {e}", file=sys.stderr)
            self._model = None

    def _vectorize(self, text: str) -> np.ndarray | None:
        """Vectoriza usando SentenceTransformer cacheado o fallback TF"""
        if self._model is not None:
            try:
                vec = self._model.encode(text)
                norm = np.linalg.norm(vec)
                if norm > 0:
                    return vec.astype(np.float32) / norm
            except Exception:
                pass
        return None

    def _fallback_search(self, query_text: str, category: str | None = None, limit: int = 5) -> list:
        """Fallback: TF-IDF bag-of-words cuando no hay SentenceTransformer"""
        def tokenize(t: str) -> Counter:
            return Counter(re.findall(r'\w+', t.lower()))

        query_tokens = tokenize(query_text)
        if not query_tokens:
            return []

        candidates = range(len(self.items))
        if category:
            candidates = [
                i for i in candidates
                if self.items[i].get("category", "").lower() == category.lower()
                or self.items[i].get("category", "").lower() == category.lower()
            ]

        scored = []
        for idx in candidates:
            item = self.items[idx]
            text = f"{item['name']} {item.get('category', '')}"
            item_tokens = tokenize(text)
            overlap = sum((query_tokens & item_tokens).values())
            if overlap > 0:
                denom = math.sqrt(sum(query_tokens.values()) * sum(item_tokens.values()))
                score = overlap / denom if denom > 0 else 0
                scored.append((score, idx))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, idx in scored[:limit]:
            item = self.items[idx]
            results.append({
                "name": item["name"],
                "path": item.get("path", ""),
                "category": item.get("category", "generic"),
                "score": round(score, 4),
            })
        return results

    def save(self, path: Path):
        """Guarda metadatos + embeddings para recarga rapida"""
        with open(path, "wb") as f:
            pickle.dump({
                "items": self.items,
                "embeddings": self.embeddings,
                "embeddings_normalized": self.embeddings_normalized,
            }, f)
        print(f"[B]  Indice guardado: {path}")


def main():
    index = SemanticIndex()
    index.build(EMBEDDINGS_PATH)
    index.save(OUT_DIR / "semantic-index.pkl")

    # Demo
    print("\n[B]  Demo de busqueda:")
    for query in ["hero academic university", "testimonials slider", "pricing table plans"]:
        results = index.search(query, limit=3)
        print(f"\n      Query: '{query}'")
        for r in results:
            print(f"        {r['score']:.4f}  {r['name']:40s} [{r['category']}]")

    return 0


if __name__ == "__main__":
    sys.exit(main())
