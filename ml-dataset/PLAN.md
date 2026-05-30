# Plan de Artefactos Inteligentes

> **Propósito**: Romper la monotonía estructural del pipeline DAW actual integrando sistemas de decisión basados en datos reales (877 templates, 109 tipos de módulo).
>
> **No más lookup tables fijas. No más 9 templates. Decisiones basadas en evidencia empírica.**

---

## Principios

1. **Cada artefacto resuelve una causa raíz de monotonía** — si no elimina una causa concreta, no se construye.
2. **El algoritmo lo dicta la naturaleza del problema** — no todo es ML. Algunos problemas son de recuperación (embedding search), otros de estadística (PMI), otros de clasificación (Naive Bayes).
3. **Todo artefacto se consume a través de un orquestador central** — no son scripts sueltos. El `design_intelligence.py` los encadena y produce un `plan.json` que el pipeline PHP ejecuta.
4. **Datos existentes, no nuevos** — todo se entrena desde `dataset.jsonl` + `embeddings.pkl` + `workspace/data/modules/`.

---

## Arquitectura General

```
┌──────────────────────────────────────────────────────────────────┐
│                        brief section                             │
│              "hero academic con CTA y stats"                     │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│              DESIGN INTELLIGENCE ENGINE (Python)                  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │                    design_intelligence.py                  │    │
│  │  (orquestador interno — único punto de entrada)           │    │
│  │                                                           │    │
│  │  Entrada: --section='{"title":"...","type":"...",...}'    │    │
│  │  Salida:  plan.json (template + columns + modules + deco) │    │
│  │                                                           │    │
│  │  Pipeline interno:                                        │    │
│  │                                                           │    │
│  │   brief text                                              │    │
│  │      │                                                    │    │
│  │      ▼                                                    │    │
│  │  ┌──────────────┐                                         │    │
│  │  │  Artefacto D  │  Content-Semantic Matcher              │    │
│  │  │  (clasifica)  │  "docentes" → section_type: team       │    │
│  │  └──────┬───────┘  confianza: 0.87                        │    │
│  │         │                                                  │    │
│  │         ▼                                                  │    │
│  │  ┌──────────────┐                                         │    │
│  │  │  Artefacto B  │  Template Semantic Index                │    │
│  │  │  (recupera)   │  team → top-3 templates del catálogo   │    │
│  │  └──────┬───────┘  score: 0.91, 0.84, 0.72                │    │
│  │         │                                                  │    │
│  │         ▼                                                  │    │
│  │  ┌──────────────┐                                         │    │
│  │  │  Artefacto A  │  Section Pattern Library                │    │
│  │  │  (consulta)   │  team → column_structures frecuentes   │    │
│  │  └──────┬───────┘  4_4: 45%, 1_2,1_2: 30%, 1_3×3: 25%   │    │
│  │         │                                                  │    │
│  │         ▼                                                  │    │
│  │  ┌──────────────┐                                         │    │
│  │  │  Artefacto C  │  Module Composition KB                  │    │
│  │  │  (complementa)│  team → módulos con alta afinidad (PMI) │    │
│  │  └──────┬───────┘  team_member+image: PMI 2.1             │    │
│  │         │           blurb+button: PMI 1.4                  │    │
│  │         │                                                  │    │
│  │         ▼                                                  │    │
│  │  ┌──────────────┐                                         │    │
│  │  │  Ensamblador  │  Genera plan.json                      │    │
│  │  │  de plan      │  { template, columns, modules, deco }  │    │
│  │  └──────────────┘                                         │    │
│  └──────────────────────────────────────────────────────────┘    │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼ plan.json
┌──────────────────────────────────────────────────────────────────┐
│              PIPELINE PHP EXISTENTE                               │
│                                                                  │
│  orchestrate_page.php recibe plan.json y EJECUTA:                │
│  1. compose_page.php  → llena slots del template                 │
│  2. post_compose.php  → inyecta presets de marca                 │
│  3. build_page.php    → resuelve tokens, despliega               │
│                                                                  │
│  NO cambia la lógica de ejecución. Cambia la FUENTE de decisión: │
│  antes: lookup table fija (section_type → template fijo)         │
│  ahora: plan.json generado por DIE con datos reales              │
└──────────────────────────────────────────────────────────────────┘
```

---

## Conexión entre Artefactos

Cada artefacto es un módulo Python independiente e importable. No se llaman entre sí directamente — el orquestador `design_intelligence.py` los encadena:

```
design_intelligence.py
├── from artifacts import d_content_classifier    → D: predice section_type
├── from artifacts import b_semantic_index         → B: busca template
├── from artifacts import a_section_patterns       → A: consulta (archivo JSON)
└── from artifacts import c_module_affinities      → C: consulta (archivo JSON)
```

### Flujo de datos entre artefactos

```
Paso 1: D produce → section_type + confidence
Paso 2: B produce → template_candidate + score  
         (usa section_type como filtro, query como texto de búsqueda)
Paso 3: A produce → column_structures posibles
         (consulta keyeada por section_type, elige por frecuencia ponderada)
Paso 4: C produce → módulos recomendados + PMI scores
         (filtra por section_type, recomienda los de mayor afinidad)
Paso 5: Ensamblador → plan.json
         (template + variant + column_structure + modules + decorations)
```

### Dependencias de datos

```
Artefacto A → section-patterns.json → consulta directa (archivo)
Artefacto B → template-index.faiss + embeddings.pkl → consulta en runtime (FAISS)
Artefacto C → module-affinities.json → consulta directa (archivo)
Artefacto D → content-classifier.pkl → modelo en runtime (joblib)

design_intelligence.py requiere:
  - A y C → archivos JSON estáticos (se cargan al inicio)
  - B → índice FAISS binario + embeddings.pkl (se cargan al inicio)
  - D → modelo joblib serializado (se carga al inicio)
```

---

## Detalle de Cada Artefacto

### Artefacto A: Section Pattern Library

**Naturaleza**: Estadística descriptiva. Agregación de frecuencias desde 877 templates reales.

**Algoritmo**: Conteo + categorización. No es entrenamiento — es extracción de conocimiento empírico.

**Input**: `dataset.jsonl` + `extract_patterns.py` (categorización)

**Output**: `section-patterns.json`

Estructura:
```json
{
  "hero": {
    "total_samples": 173,
    "column_structures": [
      {"structure": "4_4", "frequency": 0.72, "count": 128},
      {"structure": "1_2,1_2", "frequency": 0.16, "count": 29}
    ],
    "common_modules": [
      {"module_tag": "heading", "frequency": 0.91, "count": 158},
      {"module_tag": "text", "frequency": 0.78, "count": 135}
    ],
    "decorations": {
      "gradient_frequency": 0.21,
      "divider_frequency": 0.15
    }
  }
}
```

**Cómo se consume**: El orquestador carga el JSON y hace `weighted_random(patterns[section_type]['column_structures'])`.

---

### Artefacto B: Template Semantic Index

**Naturaleza**: Recuperación de información en espacio vectorial.

**Algoritmo**: FAISS IndexFlatIP con cosine similarity sobre SentenceTransformer embeddings (384-dim).

**Input**: `embeddings.pkl` (ya existe) + `dataset.jsonl` (metadatos)

**Output**: `template-index.faiss` + `semantic_search.py`

**Cómo se consume**:
```python
from artifacts.b_semantic_index import SemanticIndex
index = SemanticIndex()  # carga FAISS + metadatos
results = index.search(query="hero academic", category="hero", limit=3)
# → [{"name": "Hero University", "score": 0.91, "path": "..."}, ...]
```

---

### Artefacto C: Module Composition KB

**Naturaleza**: Minería de patrones asociativos (market basket analysis).

**Algoritmo**: Pointwise Mutual Information (PMI).

`PMI(A,B) = log(P(A∩B) / (P(A) × P(B)))`

**Input**: `dataset.jsonl` (módulos por template)

**Output**: `module-affinities.json`

Estructura:
```json
{
  "hero": {
    "affinities": [
      {"pair": ["heading", "button"], "pmi": 2.34, "count": 87},
      {"pair": ["text", "button"], "pmi": 1.45, "count": 65}
    ],
    "by_module": {
      "heading": {
        "compatible": [{"module": "button", "pmi": 2.34}],
        "incompatible": [{"module": "pricing_table", "pmi": -0.8}]
      }
    }
  }
}
```

**Cómo se consume**: El orquestador filtra `affinities[section_type]` y selecciona los módulos con PMI > 1.0 que complementan los ya elegidos.

---

### Artefacto D: Content-Semantic Matcher

**Naturaleza**: Clasificación de texto corto.

**Algoritmo**: `TfidfVectorizer(max_features=500)` + `MultinomialNB(alpha=0.1)`. Alternativa: kNN sobre SentenceTransformer embeddings.

**Input**: `dataset.jsonl` (nombres de template como X, categorías como y)

**Output**: `content-classifier.pkl` (modelo serializado con joblib)

**Cómo se consume**:
```python
from artifacts.d_content_classifier import ContentClassifier
clf = ContentClassifier.load()
result = clf.predict("docentes y personal académico")
# → {"section_type": "team", "confidence": 0.87}
```

---

## Integración con el Pipeline PHP

El `orchestrate_page.php` actual procesa cada sección del brief así:

```php
// ANTES (determinista, lookup table fija)
$template = $SECTION_TEMPLATES[$section_type] ?? 'content-split';
$variant  = $TONE_VARIANTS[$tone][$template] ?? '';

// DESPUÉS (consulta al DIE, basado en datos reales)
$plan_cmd = sprintf(
    'python "%s/design_intelligence.py" --section=%s 2>&1',
    DIE_DIR,
    escapeshellarg(json_encode($sec_def))
);
$plan = json_decode(shell_exec($plan_cmd), true);

$template = $plan['template'];
$variant  = $plan['variant'];
$column_structure = $plan['column_structure'];
$modules  = $plan['modules'];
```

El pipeline PHP **no cambia** su lógica de composición, post-compose, build y deploy. Solo cambia **dónde obtiene las decisiones de layout**: antes era una lookup table fija en PHP, ahora es el `plan.json` generado por el DIE.

---

## Resumen

| Artefacto | Naturaleza | Algoritmo | Output | Resuelve |
|---|---|---|---|---|
| A: Section Pattern Library | Estadística descriptiva | Frecuencias + agregación | section-patterns.json | CR#1, CR#3 |
| B: Template Semantic Index | Recuperación de información | FAISS + cosine similarity | template-index.faiss | CR#2, CR#7 |
| C: Module Composition KB | Minería de patrones asociativos | PMI (Pointwise Mutual Information) | module-affinities.json | CR#4, CR#5 |
| D: Content-Semantic Matcher | Clasificación de texto | TF-IDF + Naive Bayes | content-classifier.pkl | CR#1, CR#5 |
| **DIE** (orquestador) | Encadenamiento de decisiones | Pipeline secuencial | plan.json → PHP | Todas |

**Archivos resultantes en `ml-dataset/`:**

```
ml-dataset/
├── dataset.jsonl                                 ← data fuente (877 registros)
├── artifacts/
│   ├── a_section_patterns.py                     ← genera section-patterns.json
│   ├── b_semantic_index.py                       ← genera template-index.faiss
│   ├── c_module_affinities.py                    ← genera module-affinities.json
│   ├── d_content_classifier.py                   ← genera content-classifier.pkl
│   ├── design_intelligence.py                    ← ORQUESTADOR (único entry point)
│   ├── section-patterns.json                     ← output A
│   ├── template-index.faiss                      ← output B
│   ├── module-affinities.json                    ← output C
│   ├── content-classifier.pkl                    ← output D
│   └── semantic_search.py                        ← wrapper B para queries
└── PLAN.md                                       ← este archivo
```
