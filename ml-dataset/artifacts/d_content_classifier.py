#!/usr/bin/env python3
"""
Artefacto D: Content-Semantic Module Matcher
Naturaleza: Clasificación de texto corto
Algoritmo: TF-IDF + Naive Bayes Multinomial

Input: embeddings.pkl (nombres de template como X, categorías como y)
       module-affinities.json (módulos recomendados por categoría)
Output: content-classifier.pkl (pipeline sklearn serializado)

Uso:
  from d_content_classifier import ContentClassifier
  clf = ContentClassifier.load()
  result = clf.predict("docentes y personal académico")
  → {"section_type": "team", "confidence": 0.87,
     "recommended_modules": ["et_pb_team_member", "et_pb_image", ...]}
"""

import json, pickle, sys, re, warnings
from pathlib import Path

import numpy as np
DAW_ROOT = Path(__file__).resolve().parent.parent

EMBEDDINGS_PATH = DAW_ROOT / "workspace" / "catalog" / "embeddings.pkl"
AFFINITIES_PATH = Path(__file__).resolve().parent / "module-affinities.json"
OUTPUT_PATH = Path(__file__).resolve().parent / "content-classifier.pkl"


class ContentClassifier:
    def __init__(self):
        self.pipeline = None
        self.label_encoder = None
        self.section_modules = {}  # section_type -> top module tags

    def train(self, embeddings_path: Path, affinities_path: Path):
        """Train classifier from embeddings data + keyword augmentation + module affinities"""
        import sklearn.feature_extraction.text as text
        import sklearn.naive_bayes as nb
        import sklearn.preprocessing as pp
        from sklearn.pipeline import Pipeline

        # Cargar datos de entrenamiento
        print(f"[D] Cargando datos desde: {embeddings_path}")
        with open(embeddings_path, "rb") as f:
            data = pickle.load(f)

        items = data["items"]
        texts = []
        labels = []

        # Keywords de cada categoria (desde extract_patterns.py)
        CATEGORY_KEYWORDS = {
            "hero": ["hero", "banner", "landing", "cover", "intro", "header", "welcome", "coming soon", "principal"],
            "about": ["about", "story", "who we are", "our mission", "our story", "history", "nosotros", "quienes"],
            "features": ["feature", "service", "what we do", "why choose", "offerings", "capabilities", "expertise", "servicios", "caracteristicas", "programas", "oferta"],
            "testimonials": ["testimonial", "review", "client", "feedback", "people say", "customer", "testimonio", "opiniones", "reseñas"],
            "cta": ["call to action", "get started", "sign up", "join", "register", "book", "cta", "registro", "inscripcion"],
            "pricing": ["pricing", "plan", "package", "subscription", "membership", "tier", "precios", "precio", "costo", "becas"],
            "team": ["team", "member", "people", "staff", "expert", "trainer", "founder", "docentes", "personal", "equipo", "profesores"],
            "contact": ["contact", "get in touch", "reach", "location", "direccion", "ubicacion", "contacto"],
            "gallery": ["gallery", "portfolio", "project", "showcase", "collection", "galeria", "fotos", "imagenes", "campus"],
            "blog": ["blog", "news", "article", "post", "update", "noticias", "articulo"],
            "faq": ["faq", "question", "answer", "duda", "pregunta", "frecuente", "preguntas"],
            "stats": ["counter", "stat", "number", "achievement", "milestone", "estadisticas", "numeros", "cifras"],
            "countdown": ["countdown", "coming soon", "sale", "offer", "limited", "cuenta regresiva", "lanzamiento"],
            "logos": ["logo", "brand", "partner", "cliente", "marca", "patrocinadores"],
            "timeline": ["timeline", "process", "journey", "roadmap", "history", "linea de tiempo", "proceso", "historia"],
            "footer": ["footer", "bottom", "pie de pagina"],
            "product": ["product", "shop", "store", "item", "catalogo", "tienda", "productos"],
            "generic": ["section", "layout", "block", "custom", "default"],
        }

        for item in items:
            name = item.get("name", "")
            category = item.get("category", "generic")
            if not name or not category:
                continue
            texts.append(name)
            labels.append(category)
            # Augment: tambien entrenar con keywords de la categoria
            keywords = CATEGORY_KEYWORDS.get(category, [])
            for kw in keywords:
                texts.append(kw)
                labels.append(category)
            # Augment: combinar nombre con keywords
            for kw in keywords[:3]:
                texts.append(f"{name} {kw}")
                labels.append(category)

        if not texts:
            print("[D]  ERROR: No hay datos de entrenamiento", file=sys.stderr)
            return False

        # Normalizar etiquetas
        self.label_encoder = pp.LabelEncoder()
        y = self.label_encoder.fit_transform(labels)

        # Entrenar pipeline TF-IDF + Naive Bayes
        print(f"[D]  Entrenando con {len(texts)} muestras, {len(self.label_encoder.classes_)} clases")
        print(f"[D]  Clases: {list(self.label_encoder.classes_)}")

        self.pipeline = Pipeline([
            ("tfidf", text.TfidfVectorizer(
                max_features=500,
                ngram_range=(1, 2),
                analyzer="word",
                token_pattern=r"(?u)\b\w+\b",
                lowercase=True,
            )),
            ("clf", nb.MultinomialNB(alpha=0.1)),
        ])

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.pipeline.fit(texts, y)

        # Precisión en entrenamiento
        y_pred = self.pipeline.predict(texts)
        accuracy = np.mean(y_pred == y)
        print(f"[D]  Precisión en training: {accuracy:.3f}")

        # Cargar módulos recomendados por categoría desde artefacto C
        self._load_module_recommendations(affinities_path)

        return True

    def _load_module_recommendations(self, affinities_path: Path):
        """Cargar módulos recomendados por sección desde artefacto C"""
        if not affinities_path.exists():
            print(f"[D]  Warning: {affinities_path} no encontrado", file=sys.stderr)
            return

        with open(affinities_path, encoding="utf-8") as f:
            affinities = json.load(f)

        for section_type, data in affinities.items():
            top_modules = data.get("top_modules", [])[:10]
            self.section_modules[section_type] = [
                m["module_tag"] for m in top_modules
                if not m["module_tag"].startswith("et_pb_section")
                and not m["module_tag"].startswith("et_pb_row")
                and not m["module_tag"].startswith("et_pb_column")
            ]

        print(f"[D]  {len(self.section_modules)} tipos con módulos recomendados cargados")

    def predict(self, text: str) -> dict:
        """Predict section type and recommended modules from text description"""
        if self.pipeline is None:
            return {"section_type": "generic", "confidence": 0.0, "recommended_modules": []}

        # Predecir
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            probs = self.pipeline.predict_proba([text])[0]
            pred_idx = np.argmax(probs)
            confidence = float(probs[pred_idx])

        section_type = self.label_encoder.inverse_transform([pred_idx])[0]

        # Obtener módulos recomendados
        recommended = self.section_modules.get(section_type, [])

        return {
            "section_type": section_type,
            "confidence": round(confidence, 4),
            "recommended_modules": recommended,
        }

    def save(self, path: Path):
        """Save classifier to disk"""
        with open(path, "wb") as f:
            pickle.dump({
                "pipeline": self.pipeline,
                "label_encoder": self.label_encoder,
                "section_modules": self.section_modules,
            }, f)
        print(f"[D]  Modelo guardado: {path}")

    @staticmethod
    def load(path: Path = OUTPUT_PATH):
        """Load classifier from disk"""
        clf = ContentClassifier()
        if not path.exists():
            print(f"[D]  Error: modelo no encontrado en {path}", file=sys.stderr)
            return clf
        with open(path, "rb") as f:
            data = pickle.load(f)
        clf.pipeline = data["pipeline"]
        clf.label_encoder = data["label_encoder"]
        clf.section_modules = data["section_modules"]
        print(f"[D]  Modelo cargado: {path}", file=sys.stderr)
        return clf


def main():
    # Verificar dependencias
    try:
        import sklearn
    except ImportError:
        print("[D]  ERROR: sklearn no instalado. Ejecutar: pip install scikit-learn", file=sys.stderr)
        return 1

    clf = ContentClassifier()
    if not clf.train(EMBEDDINGS_PATH, AFFINITIES_PATH):
        return 1

    clf.save(OUTPUT_PATH)

    # Demo
    print("\n[D]  Demo de predicción:")
    test_queries = [
        "docentes y personal académico",
        "testimonios de alumnos",
        "programas de becas y financiamiento",
        "hero academic university",
        "pricing table monthly annual",
        "contacto y ubicación",
        "galeria de fotos del campus",
        "preguntas frecuentes",
    ]
    for q in test_queries:
        result = clf.predict(q)
        mods = ", ".join(result["recommended_modules"][:5])
        print(f"\n      '{q}'")
        print(f"      -> {result['section_type']} (conf: {result['confidence']:.3f})")
        print(f"      -> mods: {mods}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
