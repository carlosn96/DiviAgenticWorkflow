# Configuración y Ajuste de Artefactos ML

Guía práctica para modificar parámetros, reentrenar y mejorar los resultados del DIE.

---

## D — Content Classifier (Naive Bayes + TF-IDF)

Script: `artifacts/d_content_classifier.py`  
Salida: `artifacts/content-classifier.pkl`

### Parámetros clave (línea del `Pipeline`)

| Parámetro | Default | Efecto | Cuándo tocarlo |
|-----------|---------|--------|----------------|
| `max_features=500` | 500 | Número de palabras en el vocabulario TF-IDF. Más = más detalle semántico, pero más ruido y mayor tamaño del modelo. | Subir a 1000-2000 si hay errores de clasificación entre tipos similares (p.ej. `features` vs `hero`). Bajar a 300 si el dataset crece mucho (>2000 registros) para mantener velocidad. |
| `alpha=0.1` | 0.1 | Suavizado de Laplace del Naive Bayes. Más alto = más generalización (menos overfitting). Más bajo = más confianza en frecuencias observadas. | Subir a 0.5-1.0 si hay tipos con pocas muestras (cta: 20, pricing: 12, faq: 12) — evita que una palabra nueva dispare probabilidad a 0. Bajar a 0.01 si las 10,851 muestras actuales son representativas. |
| `ngram_range=(1,2)` | (1,2) | Unigramas + bigramas. `(1,1)` = solo palabras sueltas, `(1,3)` = incluye trigramas. | Cambiar a `(1,1)` si el dataset es pequeño. Cambiar a `(1,3)` para capturar frases (p.ej. "call to action"). |

### Reentrenar

```bash
python ml-dataset/artifacts/d_content_classifier.py
```

Genera `content-classifier.pkl` nuevo. No necesita inputs externos (lee `dataset.jsonl` directamente).

### Diagnosticar calidad

```python
import joblib, json
from pathlib import Path
clf = joblib.load(Path("ml-dataset/artifacts/content-classifier.pkl"))
print("Accuracy:", clf.named_steps["clf"].best_score_)  # si usas GridSearch

# Ver clases disponibles
print(clf.named_steps["clf"].classes_)

# Probar una frase
X_test = ["equipo de ventas con fotos y descripciones"]
pred = clf.predict(X_test)
proba = clf.predict_proba(X_test).max()
print(f"Predicción: {pred[0]} (confianza: {proba:.4f})")
```

### Mejorar accuracy para tipos con pocas muestras

1. **Aumentar `alpha`** (ver tabla arriba) — es el cambio más simple.
2. **Aumentar `max_features`** para que el vocabulario capture términos relevantes de esos tipos.
3. **Aumentar muestras**: agregar más registros de ese tipo al `dataset.jsonl` (extraer templates del catálogo con `python ml-dataset/prepare_dataset.py`).
4. **Ponderación de clases**: agregar `class_weight='balanced'` al `MultinomialNB()` en el script.

---

## B — Semantic Index (FAISS + SentenceTransformer)

Script: `artifacts/b_semantic_index.py`  
Salida: `artifacts/semantic-index.pkl`

### Parámetros clave

| Parámetro | Default | Efecto | Cuándo tocarlo |
|-----------|---------|--------|----------------|
| `model_name` | `all-MiniLM-L6-v2` | Modelo de embeddings (384-dim). `all-mpnet-base-v2` (768-dim) da mejor calidad pero +4x tiempo/latencia. | Cambiar si la búsqueda semántica no capta sinónimos o contexto. |
| `limit=3` | 3 | Número de templates a retornar por sección. Más = más opciones de variación. Menos = más determinista. | Subir a 5-8 si el pipeline PHP ya filtra por `section_type`. Bajar a 1-2 si se prefiere máxima precisión. |
| `metric` | `IP` | `IP` = producto punto (cosine similarity). `L2` = distancia euclídea. | `IP` es estándar para texto. `L2` funciona mejor si los embeddings están normalizados. |

### Reentrenar

```bash
python ml-dataset/artifacts/b_semantic_index.py
```

Requiere: `ml-dataset/dataset.jsonl` (877 registros) + `workspace/catalog/embeddings.pkl`.

### Ajustar threshold de score mínimo

En `design_intelligence.py`, línea donde se consume B:

```python
if row["score"] > 0.25:  # ← ajustar este umbral
```

- **0.25**: muy permisivo (pocos fallos, pero variado)
- **0.40**: razonable (solo resultados con buena correspondencia semántica)
- **0.60**: restrictivo (pocos resultados, pero muy precisos)

### Mejorar calidad de búsqueda

1. **Cambiar modelo**: `all-mpnet-base-v2` es el más preciso de sentence-transformers.
2. **Agregar más templates**: cuantos más embeddings, mejor cubrimiento semántico. Ejecutar `a_section_patterns.py` después de añadir templates.
3. **Re-indexar periódicamente**: ejecutar `b_semantic_index.py` cada vez que se agreguen templates al catálogo.

---

## C — Module Affinities (PMI Matrix)

Script: `artifacts/c_module_affinities.py`  
Salida: `artifacts/module-affinities.json`

### Parámetros clave

| Parámetro | Default | Efecto | Cuándo tocarlo |
|-----------|---------|--------|----------------|
| `PMI > 1.0` | 1.0 | Umbral de Pointwise Mutual Information. Más alto = solo afinidades muy fuertes. Más bajo = más combinaciones posibles. | Subir a 2.0-3.0 si las combinaciones recomendadas son ruidosas. Bajar a 0.5 si el módulo A casi nunca co-ocurre con B pero se necesita sugerirlo. |
| Mínimo de co-ocurrencia (implícito) | 2 docs | Frecuencia mínima para considerar un par. | Cambiar en `c_module_affinities.py` — variables `min_cooccurrence`. |

### Reentrenar

```bash
python ml-dataset/artifacts/c_module_affinities.py
```

Requiere: `ml-dataset/dataset.jsonl` + `workspace/catalog/jsons/`.

### Interpretar salida

```json
{
  "hero": {
    "et_pb_text": {"et_pb_image": 2.3, "et_pb_button": 1.8, "dipl_banner": 0.4},
    "et_pb_image": {"et_pb_text": 2.3, "et_pb_blurb": 1.2}
  }
}
```

PMI > 1.5 = afinidad fuerte (siempre aparecen juntos).  
PMI 0.5–1.5 = afinidad moderada (suelen aparecer juntos).  
PMI < 0.5 = prácticamente independientes o co-ocurrencia baja.

### Mejorar recomendaciones

1. **Bajar umbral PMI** para sugerir combinaciones menos obvias (más variación).
2. **Agregar filtro de soporte** mínimo en el ensamblador del DIE: ignorar sugerencias con frecuencia < 3 en el dataset.
3. **Separar PMI por tipo de sección**: ya está hecho (cada `section_type` tiene su matriz). Si un tipo tiene pocas muestras, sus PMI serán ruidosas — considerar usar la matriz global como fallback.

---

## A — Section Pattern Library (Estadística descriptiva)

Script: `artifacts/a_section_patterns.py`  
Salida: `artifacts/section-patterns.json`

### Qué configura

No tiene parámetros de ML. La salida es puramente estadística sobre el dataset existente. Lo que se puede ajustar:

| Aspecto | Default | Efecto |
|---------|---------|--------|
| `weighted_random` en DIE | pesos por frecuencia | Tipos de sección con más templates en catálogo tienen más probabilidad de ser elegidos en el `variant`. |
| Column structures | frecuencia real | `1_2,1_2` vs `1_4,1_4,1_4,1_4` según lo que más se usa en el catálogo para ese tipo. |

### Regenerar

```bash
python ml-dataset/artifacts/a_section_patterns.py
```

No necesita regenerarse a menos que cambie el dataset.

---

## DIE — Orquestador

Script: `artifacts/design_intelligence.py`

### Parámetros de ejecución

| Flag | Default | Efecto |
|------|---------|--------|
| `--brief-file` | (requerido) | Ruta al JSON de brief de página completa (varias secciones). |
| `--section-file` | — | Ruta al JSON de brief de una sección individual (alternativa a `--brief-file`). |
| `--output` | stdout | Ruta donde escribir `plan.json`. |

### Schema de `plan.json` (output)

```json
[
  {
    "section_type": "hero",
    "confidence": 0.9993,
    "template": "Accountant Hero Section",
    "template_path": "C:/.../catalog/jsons/Accountant Hero Section/file.json",
    "template_score": 0.3333,
    "column_structure": "1_2,1_2",
    "modules": ["dipl_button", "et_pb_text", "et_pb_image", ...],
    "variant": "editorial-grid",
    "has_gradient": false,
    "has_divider": false
  }
]
```

### Orden de precedencia del diseñador

```
1. section_type del brief → se usa tal cual (el diseñador manda)
2. section_type NO está en brief → se usa clasificador D
3. Búsqueda semántica en B → top 3 templates, filtrados por section_type
4. Variant elegido por weighted_random sobre frecuencias reales (artefacto A)
5. Módulos extraídos del template real (no generados)
```

### Ajustar pesos de decisión

En `design_intelligence.py`, función `generate_plan`:

```python
# Peso de búsqueda semántica vs aleatoriedad
top_n = 3                     # ← más = más variación, menos = más preciso
score_threshold = 0.25        # ← umbral de similitud (ver sección B)
variant_weight = "frequency"  # ← "frequency" o "uniform" (random puro)
```

- `top_n=1`: siempre el mejor template → composiciones repetitivas pero precisas.
- `top_n=5`: más variación, mejor para páginas largas.
- `variant_weight="uniform"`: todos los variants tienen la misma probabilidad (más variación, menos realismo estructural).

### Logging

El DIE imprime a stderr. Para depurar:

```bash
python artifacts/design_intelligence.py --brief-file brief.json 2>&1
```

Los mensajes `[DIE]`, `[D]`, `[A]`, `[B]`, `[C]` indican qué artefacto se está ejecutando.

---

## Flujo de mejora continua

### 1. Diagnóstico: algo no funciona bien

```
Problema                        → Qué mirar               → Qué ajustar
──────────────────────────────────────────────────────────────────────────
Template incorrecto              → confidence, score       → top_n, score_threshold
Poca variación entre páginas     → variant siempre igual   → variant_weight="uniform"
Misma columna structure siempre  → section-patterns.json   → agregar templates diversos
Módulos no relacionados          → module-affinities.json  → subir PMI threshold
Clasificación wrong section      → classifier accuracy     → alpha, max_features
Fallo silencioso (null template) → stderr logs             → dataset tiene ese section_type?
```

### 2. Agregar nuevos templates al catálogo

```bash
# 1. Extraer shortcode del nuevo layout Divi
# 2. Guardar como workspace/catalog/jsons/<Name>/file.json
# 3. Reconstruir dataset
python ml-dataset/prepare_dataset.py
# 4. Regenerar artefactos
python ml-dataset/artifacts/d_content_classifier.py
python ml-dataset/artifacts/b_semantic_index.py
python ml-dataset/artifacts/a_section_patterns.py
python ml-dataset/artifacts/c_module_affinities.py
```

### 3. Evaluar cambio

Comparar `plan.json` antes y después para ver si la variabilidad aumentó:

```bash
python -c "
import json
a = json.load(open('plan_before.json'))
b = json.load(open('plan_after.json'))
# Comparar templates, column structures, modules
"
```
