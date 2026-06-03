# Estado de Artefactos Inteligentes

Actualizado: 2026-05-30

## Leyenda
- [x] Completado y verificado
- [~] En construcción
- [ ] Pendiente

---

## Artefacto A: Section Pattern Library
- [x] Script: `ml-dataset/artifacts/a_section_patterns.py`
- [x] Output: `ml-dataset/artifacts/section-patterns.json`
- [x] 18 tipos de sección, 877 templates categorizados
- [x] Column structures, módulos, decoraciones por tipo

## Artefacto B: Template Semantic Index
- [x] Script: `ml-dataset/artifacts/b_semantic_index.py`
- [x] Output: `ml-dataset/artifacts/semantic-index.pkl`
- [x] 892 templates indexados con categorías reales
- [x] Búsqueda semántica integrada en DIE

## Artefacto C: Module Composition KB
- [x] Script: `ml-dataset/artifacts/c_module_affinities.py`
- [x] Output: `ml-dataset/artifacts/module-affinities.json`
- [x] Matriz PMI con 18 tipos de sección

## Artefacto D: Content-Semantic Matcher
- [x] Script: `ml-dataset/artifacts/d_content_classifier.py`
- [x] Modelo: `ml-dataset/artifacts/content-classifier.pkl`
- [x] 98.2% accuracy en training

## Artefacto E: Decoration Engine
- [x] Script: `ml-dataset/artifacts/e_decorator.py`
- [x] Output: `ml-dataset/artifacts/decoration-clusters.pkl`
- [x] Output: `ml-dataset/artifacts/decoration-rules.json`
- [x] K-means clustering (scikit-learn) sobre vectores decoration de 877 templates → 7 clusters
- [x] Integración con colors.csv → mapeo product_type → paleta (97 paletas)
- [x] Integración con styles.csv → mapeo tone → decoration persona (~35 estilos)
- [x] Integración con typography.csv → mapeo tone → font pairing (57 pairings)
- [x] Integración con ux-guidelines.csv → constraints de animación/timing (99 reglas)
- [x] `get_decoration()` devuelve decoration blocks completos con `{{design:color:*}}` tokens
- [x] Importable como `from e_decorator import DecorationEngine`

## DIE: Design Intelligence Engine (Orquestador)
- [x] Refactor para importar A+B+C+D+E como módulos (no shell_exec)
- [x] Eliminar dependencia de orchestrate_page.php
- [x] Eliminar dependencia de compose_page.php
- [x] Eliminar dependencia de post_compose.php
- [x] Pipeline final: brief.json → DIE → plan.json → build_page.php --deploy
- [x] `load_brand_vars()` / `load_brand_presets()` → brand-aware decoration
- [x] `product_type` soportado en section_def y brief
- [x] Decoration blocks incluidos en plan.json (step 5: E)
- [x] CLI: `--brief-file`, `--section-file`, `--section`, `--output`, `--no-brand`

## Cleanup Pipeline PHP
- [x] Eliminar `divi-agentic-core/bin/orchestrate_page.php`
- [x] Eliminar `divi-agentic-core/bin/compose_page.php`
- [x] Eliminar `divi-agentic-core/bin/post_compose.php`
- [x] `.gitignore` actualizado: `site/*/pages/**` en vez de `site/**`
- [x] AGENTS.md actualizado: nuevo pipeline, nuevas referencias, nuevas reglas

---

## Registro de Cambios

| Fecha | Artefacto | Cambio | Estado |
|---|---|---|---|
| 2026-05-29 | A | Build inicial | ✅ |
| 2026-05-29 | A | Output verificado: 18 tipos, 877 templates | ✅ |
| 2026-05-29 | B | Build + verificado: 892 templates indexados | ✅ |
| 2026-05-29 | C | Build + verificado: matriz PMI 18 tipos | ✅ |
| 2026-05-29 | D | Build + verificado: 98.2% accuracy | ✅ |
| 2026-05-29 | DIE | Build + verificado: orquesta A+B+C+D | ✅ |
| 2026-05-30 | E | Build + verificado: K-means, 7 clusters, 4 CSVs integradas, decoration blocks | ✅ |
| 2026-05-30 | DIE | Refactor v3.0: A+B+C+D+E como módulos, brand-aware, product_type | ✅ |
| 2026-05-30 | Pipeline | PHP muerto: orchestrate/compose/post_compose eliminados | ✅ |
| 2026-05-30 | Docs | AGENTS.md, .gitignore, TASKS.md actualizados | ✅ |
| 2026-05-30 | DIE v3.0 | e_page_mapper.py v3: post-inyección limpia basura de template y rellena campos sin slot | ✅ |
| 2026-05-31 | e_page_mapper | Fix P0: _clean_template_garbage recursivo en row-inner containers | ✅ |
| 2026-05-31 | e_page_mapper | Fix P0: _value_already_in_section recursivo en containers anidados | ✅ |
| 2026-05-31 | e_page_mapper | Fix P0: _dedup_section_content nueva función post-procesamiento | ✅ |
| 2026-05-31 | Validación | 0 contenido médico residual en los 4 planes (inicio, contacto, faq, nuestras-instalaciones) | ✅ |

---

## DIE v4.0 — Agente Director + Quality Gate ✅

### design_translator.py (puente UX-PRO → Divi)
- [x] Script: `ml-dataset/artifacts/design_translator.py`
- [x] Output: `ml-dataset/artifacts/design_rules_divi.pkl` (273 KB)
- [x] Lee styles.csv → feature encoder por tone (editorial, modern, premium, minimal, dramatic, playful)
- [x] Lee colors.csv → matriz de distancia cromática por product_type
- [x] Lee typography.csv → scorer de pares tipográficos (serif+sans, sans+sans, etc.)
- [x] Lee ux-guidelines.csv → mapeo de constraints UX a fields Divi nativos (spacing, contraste, animación)
- [x] Build one-time: produce .pkl con todas las reglas traducidas, no hardcodeadas

### design_director.py (agente de decisión por stacking ensemble)
- [x] Script: `ml-dataset/artifacts/design_director.py`
- [x] Carga todas las fuentes de conocimiento en init (one-time cold start): 11 fuentes ML
- [x] `decide_template(section_def, context)` → stacking ensemble:
  - [x] Experto 1: distancia euclidiana de KMeans entre secciones adyacentes
  - [x] Experto 2: confidence del content classifier en el section_type
  - [x] Experto 3: slot coverage (slot IDF matching B2)
  - [x] Experto 4: column match (template cols vs esperadas)
  - [x] Meta: weighted average de expertos → template score → selección
- [x] `decide_columns(section_def, template, adjacent_section)` → columna que maximiza compatibilidad visual
- [x] `decide_decoration(section_def, template, brand_vars)` → decoration contextual:
  - [x] Cluster del template + brand fonts + UX-PRO contraste + patterns
- [x] `decide_modules(section_def, template, column_structure)`:
  - [x] Module schemas (fields correctos) + affinities (PMI) + classifier
- [x] `decide_spacing(section, adjacent_sections, cluster)`:
  - [x] Catalog stats (padding mean/std por cluster) + UX-PRO ritmo vertical
- [x] `validate_visual_cohesion(page_def)` → score compuesto 0-1:
  - [x] KMeans cluster coherence (adyacentes en mismo cluster?)
  - [x] Tipografía: familias distintas por página (UX-PRO: max 2)
  - [x] Contraste: bg vs text (UX-PRO: 4.5:1 mínimo)
  - [x] Ritmo vertical: diferencia de padding entre secciones adyacentes
  - [x] Layout metrics (HF evaluate: alignment, overlap, validity)
  - [x] Slot overflow: brief text vs slot capacity from slot_stats.json
  - [x] Módulos vacíos: imágenes sin src, textos vacíos
  - [x] Stacking ensemble final → score 0-1 + reporte de issues

### design_intelligence.py v4.0 (reescritura)
- [x] Integrar design_director como núcleo de decisión
- [x] Cada método de generación consulta al director (no opera solo)
- [x] Quality gate ejecuta validate_visual_cohesion() sobre plan generado
- [x] Si score < threshold (0.65): re-asignar template + re-balancear espaciado + re-ejecutar mapper
- [x] Si score >= threshold: output plan.json
- [x] CLI idéntico: `--brief-file`, `--output` — sin cambios de interfaz

### Module schemas como fuente de verdad (integración)
- [x] Cargar 103 module schemas desde `workspace/data/modules/*.json`
- [x] design_director.decide_modules() consulta fields reales de cada módulo
- [x] Quality gate valida que los fields usados existen en el schema

### Catalog stats (padding/spacing por cluster)
- [x] Script one-time: `ml-dataset/artifacts/extract_catalog_stats.py`
- [x] Output: `catalog_stats.json` (padding mean/std/p10/p90 por cluster KMeans)
- [x] DesignDirector carga catalog_stats.json y lo usa en quality gate (atypical padding detection)

### Dataset.jsonl stats (slot capacity)
- [x] Script one-time: `ml-dataset/artifacts/extract_slot_stats.py`
- [x] Output: `slot_stats.json` (text length stats por slot type: body, title, eyebrow, button)
- [x] Quality gate usa slot_stats para detectar content overflow (Expert 7, weight 0.25)

### Dependencias nuevas (pip)
- [x] `evaluate` (ya instalado)
- [x] layout metrics de HF: alignment, overlap, validity (ya verificados)

## DIE v4.1 — Design System Utilization (Pendiente)

### Objetivo
Conectar los 64 presets del design system (`_design_presets.json`) que están infrautilizados (~30% de uso real) con los módulos que el pipeline despliega.

### Cambios en e_page_mapper.py

#### 1. `_add_animations` — section-type-aware
- [ ] Dejar de sobrescribir animaciones de módulos que ya tienen preset
- [ ] Variar `style` y `duration` por `section_type` usando lookup table:
  ```
  hero:       reveal 800ms, hero-image: fade 1000ms
  features:   slide 480ms (ya en preset feature-card)
  testimonials: fade 800ms (ya en preset testimonial-card)
  stats:      fade 800ms (ya en preset stat-item)
  cta:        fade 800ms (ya en preset cta-epic)
  faq:        fade 600ms
  content:    fade 600ms
  gallery:    slide 600ms
  ```
- [ ] Respetar animation existente si viene de preset (solo añadir si no hay)

#### 2. Decoración — section-type-aware
- [ ] `process_section` debe asignar `scroll:` preset por section_type en lugar de decoration plana
- [ ] Hero → `parallax-up`, features → `scale-in`, testimonials → `reveal`
- [ ] Shape dividers entre secciones: `curve-bottom` entre hero y siguiente, `curve-top` entre penúltima y CTA

#### 3. ITEM_TEMPLATES — más presets
- [ ] Imágenes en items → preset `module:image-shadow` (hover scale 1.02 + box-shadow)
- [ ] Botones en secciones dark → preset `module:btn-cta-dark`
- [ ] Botones en secciones light → preset `module:btn-primary`
- [ ] Separadores entre items → preset `module:accent-line`

#### 4. UX micro-interacciones
- [ ] Añadir `cursor: pointer` a todos los módulos con hover preset
- [ ] Añadir `transition: 300ms ease-out` a módulos con hover transform que no lo tengan

#### 5. Imágenes post-mapping
- [ ] Aplicar `resolve_image_src` a módulos `divi/image` con `src=""` después del mapeo

### Impacto esperado
| Métrica | Antes | Después (estimado) |
|---------|-------|-------------------|
| Presets usados | ~30% | ~70% |
| Estilos de animación | 1 (fade) | 5+ (fade, slide, reveal, zoom, bounce) |
| Hover effects variados | 1 (hover-lift) | 4+ (lift, scale, glow, expand) |
| Scroll effects | 0 | 3+ (parallax, scale-in, reveal) |
| Shape dividers | 0 | 2+ (curve entre secciones) |
| UX micro-interacciones | 0 | cursor-pointer, transitions |

### Registro de Cambios

| Fecha | Artefacto | Cambio | Estado |
|-------|-----------|--------|--------|
| 2026-05-30 | design_translator | Build one-time: traduce 4 CSVs UX-PRO → `design_rules_divi.pkl` (273 KB) | ✅ |
| 2026-05-30 | design_director | Agente stacking ensemble con 7 expertos ML + quality gate (6→7 expertos) | ✅ |
| 2026-05-30 | DIE v4.0 | Reescritura con director + quality gate integrado (score 0.921/1.0 en test) | ✅ |
| 2026-05-30 | Module schemas | Integración como fuente de verdad de fields (103 schemas cargados) | ✅ |
| 2026-05-30 | Catalog stats | `catalog_stats.json` generado desde dataset.jsonl + integrado en quality gate | ✅ |
| 2026-05-30 | Dataset stats | `slot_stats.json` generado desde dataset.jsonl + integrado como Expert 7 | ✅ |
| 2026-05-31 | e_page_mapper | Fix P0: _clean_template_garbage recursivo, dedup, validación 4 planes limpios | ✅ |
| 2026-05-31 | e_page_mapper | Design System Utilization v4.1: _add_animations section-aware, ITEM_TEMPLATES extendido, UX micro, imágenes |  |
