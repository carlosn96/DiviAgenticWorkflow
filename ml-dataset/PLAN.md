# Plan de Artefactos Inteligentes (v2.0)

> **Propósito**: Una sola máquina. Brief entra. Page-def sale. Eliminar todo el pipeline suelto de PHP intermedio.

---

## Principios

1. **Un solo entry point**: `design_intelligence.py` importa A+B+C+D+E como módulos. No hay scripts sueltos.
2. **Zero archivos intermedios**: El DIE produce `plan.json` directamente. Muerto `orchestrate_page.php`, `compose_page.php`, `post_compose.php`.
3. **Decoración real, no inventada**: E usa 877 templates + 4 CSVs curados de ui-ux-pro-max.
4. **Tokenizado desde el origen**: decoration blocks usan `{{design:color:*}}`, `{{design:font:*}}`. Nunca hex.
5. **K-means + sentence-transformers**: Clustering híbrido en espacio visual+semántico. Reglas de UX guidelines como constraints.

---

## Arquitectura General

```
brief.yml + brand/_design_vars.json + brand/_design_presets.json
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│              DESIGN INTELLIGENCE ENGINE (Python)              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                design_intelligence.py                  │  │
│  │  (única entrada, único output — importa A/B/C/D/E)    │  │
│  │                                                       │  │
│  │  Paso 1: D (classifier)    → section_type + confianza │  │
│  │  Paso 2: A (patterns)      → structure + módulos      │  │
│  │  Paso 3: B (semantic)      → template match           │  │
│  │  Paso 4: C (affinities)    → módulos complementarios  │  │
│  │  Paso 5: E (decorator)     → decoration blocks        │  │
│  │  Paso 6: ensamblador       → plan.json completo       │  │
│  └───────────────────────────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼ plan.json
┌─────────────────────────────────────────────────────────────┐
│              PIPELINE PHP REDUCIDO                           │
│  Único script: build_page.php --deploy                       │
│  - Lee plan.json (resuelto con decoration blocks)            │
│  - Expande presets inline                                    │
│  - Resuelve {{design:*}} tokens                              │
│  - Despliega a WordPress                                     │
└─────────────────────────────────────────────────────────────┘
```

---

## Artefacto E: Decoration Engine

### Naturaleza
Motor de decoración visual basado en diseño real (877 templates) + reglas curadas (4 CSVs de ui-ux-pro-max).

### Pipeline interno de E

```
Brief (section_type + tone + product_type)
  │
  ├── dataset.jsonl (877 templates)
  │   └── regex parse decoration attributes (gradient, shadow, animation, 
  │       hover, scroll, divider, mask, border)
  │   └── vector numérico por template
  │   └── source_name → sentence embedding (384-dim)
  │   └── K-means → decoration persona clusters (6-8)
  │
  ├── colors.csv (97 paletas curadas)
  │   └── mapeo product_type → paleta (Primary, Secondary, CTA, BG, Text)
  │   └── brand_vars sobreescribe con tokens {{design:color:*}}
  │
  ├── styles.csv (~35 estilos)
  │   └── mapeo tone → style category (editorial→Minimal Swiss, modern→Aurora UI)
  │   └── cada estilo trae: efectos, animaciones, implementación checklist
  │
  ├── typography.csv (57 font pairings)
  │   └── mapeo tone → font pairing
  │   └── brand_vars sobreescribe fonts
  │
  └── ux-guidelines.csv (100 reglas)
      └── constraints aplicados a decoration:
          - animation duration: 150-300ms (micro-interactions)
          - touch targets: 44x44px min
          - spacing: 8px base unit, 2rem section padding
          - reduced-motion support
```

### Entrada
| Campo | Fuente |
|-------|--------|
| `section_type` | del brief o DIE A/D |
| `tone` | del brief (editorial, modern, premium, minimal, dramatic) |
| `product_type` | del brief o brand |
| `brand_vars` | `_design_vars.json` (colores, fonts) |
| `brand_presets` | `_design_presets.json` (64 presets section/text/module/divider/animation/scroll/hover) |

### Salida (decoration blocks en plan.json)
```json
{
  "section_type": "hero",
  "presets": ["section:hero-dark"],
  "decoration": {
    "animation": {"desktop": {"value": {"style": "fade", "duration": "800ms"}}},
    "scroll": {"desktop": {"value": {"verticalMotion": {"enable": "on", "offset": {"start": "6", "mid": "0", "end": "-4"}}}}},
    "hover_modules": ["divi/button", "divi/blurb"],
    "color_scheme": {
      "bg": "{{design:color:surface-deep}}",
      "text": "{{design:color:text-on-dark}}",
      "accent": "{{design:color:accent}}"
    }
  },
  "modules": [
    {"type": "divi/text", "presets": ["text:display-xl"], "content": "<h1>...</h1>"},
    {"type": "divi/button", "presets": ["module:btn-primary"], "decoration": {"hover": {"desktop": {"value": {"transform": {"scale": "105%"}, "transition": "300ms ease-out"}}}}}
  ]
}
```

### Cómo se importa en design_intelligence.py
```python
from e_decorator import DecorationEngine

deco = DecorationEngine(
    dataset_path="ml-dataset/dataset.jsonl",
    colors_path="ui-ux-pro-max/data/colors.csv",
    styles_path="ui-ux-pro-max/data/styles.csv",
    typography_path="ui-ux-pro-max/data/typography.csv",
    ux_path="ui-ux-pro-max/data/ux-guidelines.csv",
    brand_vars=brand_vars,
    brand_presets=brand_presets
)

plan.decoration = deco.get_decoration(
    section_type="hero",
    tone="editorial",
    product_type="Digital Library"
)
```

### Outputs precargados (generados una vez, consulta O(1))
- `workspace/data/decoration-clusters.pkl` — modelos K-means + índices
- `workspace/data/decoration-rules.json` — mapeos decoration persona → blocks

---

## Conexión entre Artefactos

```python
design_intelligence.py  (único entry point)
├── from a_section_patterns   → consulta patterns (JSON, O(1))
├── from b_semantic_index     → busca template (FAISS, O(log n))
├── from c_module_affinities  → consulta afinidades (JSON, O(1))
├── from d_content_classifier → clasifica texto (modelo, O(n))
└── from e_decorator          → genera decoration (clusters + CSVs, O(1))
```

No hay archivos intermedios. No hay PHP entre scripts. `design_intelligence.py` produce `plan.json` completo → `build_page.php --deploy`.

---

## Detalle de Cada Artefacto

### Artefacto A: Section Pattern Library
**Naturaleza**: Estadística descriptiva. Agregación de frecuencias desde 877 templates.
**Input**: `dataset.jsonl`
**Output**: `section-patterns.json`
**Algoritmo**: Conteo + categorización. No es entrenamiento.

### Artefacto B: Template Semantic Index
**Naturaleza**: Recuperación de información en espacio vectorial.
**Input**: `dataset.jsonl` + `workspace/automation/embeddings.pkl`
**Output**: `semantic-index.pkl` (FAISS-like, cosine similarity)
**Algoritmo**: SentenceTransformer (384-dim) + cosine similarity.

### Artefacto C: Module Composition KB
**Naturaleza**: Minería de patrones asociativos (market basket analysis).
**Input**: `dataset.jsonl`
**Output**: `module-affinities.json`
**Algoritmo**: Pointwise Mutual Information (PMI).

### Artefacto D: Content-Semantic Matcher
**Naturaleza**: Clasificación de texto corto.
**Input**: `dataset.jsonl` (nombres como X, categorías como y)
**Output**: `content-classifier.pkl`
**Algoritmo**: TF-IDF (500 features) + Multinomial Naive Bayes.

### Artefacto E: Decoration Engine
**Naturaleza**: Clustering híbrido + mapeo multi-CSV.
**Input**: `dataset.jsonl` + 4 CSVs de ui-ux-pro-max + brand vars/presets
**Output**: `decoration-clusters.pkl` + `decoration-rules.json`
**Algoritmo**: K-means (scikit-learn) sobre vectores decoration numéricos + sentence embeddings (384-dim) para clustering semántico + mapeo por tone/product_type.

---

## Pipeline PHP Destruido

### Muertos (eliminar)
| Archivo | Razón |
|---------|-------|
| `orchestrate_page.php` | DIE produce plan.json directo. No necesita orquestador PHP. |
| `compose_page.php` | DIE ya compone decoration + estructura. No necesita compositor PHP. |
| `post_compose.php` | decoration blocks incluyen presets. No hay "post" que hacer. |

### Vivo
| Archivo | Razón |
|---------|-------|
| `build_page.php --deploy` | Único script PHP necesario. Lee plan.json, resuelve tokens, despliega. |
| `lint_page_def.php` | Quality gate. No cambia. |
| `verify_page.php` | Verificación post-deploy. No cambia. |

### Archivos intermedios eliminados
| Carpeta/Archivo | Razón |
|-----------------|-------|
| `site/<DAW_SITE>/compositions/` | Ya no existe. DIE escribe directo a page-defs/ |
| `site/<DAW_SITE>/pages/` | Debug-only. Se mantiene ignorado por git. |
| `workspace/sections/catalog/` | Los 877 .section.json compilados nunca se usaron. DIE usa dataset.jsonl directo. |

---

## Resumen

| Artefacto | Naturaleza | Algoritmo | Output | Inputs |
|-----------|---|---|---|---|
| A: Section Patterns | Estadística | Frecuencias + agregación | section-patterns.json | dataset.jsonl |
| B: Semantic Index | Recuperación | Cosine similarity (384-dim) | semantic-index.pkl | dataset.jsonl + embeddings |
| C: Module Affinities | Minería | PMI | module-affinities.json | dataset.jsonl |
| D: Content Classifier | Clasificación | TF-IDF + Naive Bayes | content-classifier.pkl | dataset.jsonl |
| E: Decoration Engine | Clustering + mapeo | K-means + sentence-transformers + multi-CSV | decoration-clusters.pkl + decoration-rules.json | dataset.jsonl + colors.csv + styles.csv + typography.csv + ux-guidelines.csv + brand vars/presets |
| **DIE** (orquestador) | Pipeline | Secuencial importando A+B+C+D+E | plan.json → build_page.php | brief.yml + brand |

**Archivos resultantes en `ml-dataset/`:**

```
ml-dataset/
├── dataset.jsonl                                   ← data fuente (877 registros)
├── artifacts/
│   ├── a_section_patterns.py                       ← genera section-patterns.json
│   ├── b_semantic_index.py                         ← genera semantic-index.pkl
│   ├── c_module_affinities.py                      ← genera module-affinities.json
│   ├── d_content_classifier.py                     ← genera content-classifier.pkl
│   ├── e_decorator.py                              ← genera decoration-clusters.pkl + decoration-rules.json
│   ├── design_intelligence.py                      ← ORQUESTADOR (único entry point, importa A+B+C+D+E)
│   ├── section-patterns.json                       ← output A
│   ├── semantic-index.pkl                          ← output B
│   ├── module-affinities.json                      ← output C
│   ├── content-classifier.pkl                      ← output D
│   ├── decoration-clusters.pkl                     ← output E (modelos K-means)
│   └── decoration-rules.json                       ← output E (mapeos decoration persona → blocks)
└── PLAN.md                                         ← este archivo
```
