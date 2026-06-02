# PLAN.md — DIE (Design Intelligence Engine)

Este documento describe la arquitectura de los 5 artefactos ML (A+B+C+D+E) que componen el DIE y su pipeline.

**Nota**: La v4.0 descrita originalmente como plan futuro ya está implementada. Todos los artefactos existen y operan en el pipeline activo.

---

## Arquitectura (v4.0 consolidada)

### Pipeline actual

```
brief.json
  → DIE (design_intelligence.py)
    → A (section_patterns): extrae estructura de columnas
    → B2 (slot_assigner): Hungarian + IDF, 9 slot types sobre dataset.jsonl
    → B (semantic_index): fallback legacy si B2 no encuentra match
    → C (module_affinities): matriz PMI de co-ocurrencia
    → D (content_classifier): clasificador TF-IDF + Naive Bayes (98.2%)
    → E (decorator): K-means sobre 877 templates + 4 CSVs → decoration blocks
    → design_director: recomienda colores, tipografía, template
    → design_translator: mapea reglas de diseño a tokens {{design:*}}
    → quality gate: valida contraste WCAG, estructura, cobertura de slots
  → plan.json
  → build_page.php --deploy
  → WordPress Divi 5
```

### Archivos clave

| Artefacto | Script | Output |
|-----------|--------|--------|
| A (Patterns) | `ml-dataset/artifacts/a_section_patterns.py` | `workspace/design-patterns.json` |
| B2 (Slot Assigner) | `ml-dataset/artifacts/b_slot_assigner.py` | `ml-dataset/artifacts/slot-catalog.pkl` |
| B (Semantic Index) | `ml-dataset/artifacts/b_semantic_index.py` | `ml-dataset/artifacts/semantic-index.pkl` |
| C (Affinities) | `ml-dataset/artifacts/c_module_affinities.py` | `workspace/module-affinities.json` |
| D (Classifier) | `ml-dataset/artifacts/d_content_classifier.py` | `ml-dataset/artifacts/content-classifier.pkl` |
| E (Decorator) | `ml-dataset/artifacts/e_decorator.py` | `ml-dataset/artifacts/decoration-clusters.pkl`, `ml-dataset/artifacts/decoration-rules.json` |
| Director | `ml-dataset/artifacts/design_director.py` | (en memoria) |
| Translator | `ml-dataset/artifacts/design_translator.py` | `ml-dataset/artifacts/design_rules_divi.pkl` |
| Quality Gate | `ml-dataset/artifacts/quality_gate.py` | (en memoria) |

---

## Pipeline PHP destruido (legacy)

Los siguientes archivos ya no existen ni se usan:
- `orchestrate_page.php` — eliminado en la migración a DIE
- `compose_page.php` — eliminado en la migración a DIE
- `post_compose.php` — eliminado en la migración a DIE

La carpeta `site/<DAW_SITE>/compositions/` fue eliminada (no se usaba en el pipeline activo).

---

## Archivos intermedios eliminados

| Archivo | Estado | Nota |
|---------|--------|------|
| `workspace/compositions/` | ✅ Eliminado | Sustituido por `plans/` |
| ~~`site/<DAW_SITE>/compositions/`~~ | ❌ Eliminado | No contenía datos; reemplazado por `plans/` |
| `workspace/sections/catalog/*.section.json` (877) | ✅ En uso | Consumido por `e_page_mapper.py` vía `_load_template()` |
| `ml-dataset/artifacts/decoration-rules.json` | ✅ En ml-dataset/artifacts/ | No en workspace/data/ |

---

## Sobre el Decorator (Artefacto E)

El Decoration Engine genera decoration blocks completos en el plan.json usando:
- **Gradients**: lineales/radiales con stops mapeados por tone + product_type
- **Shadows**: box-shadow + text-shadow con opacidad/blur
- **Animaciones**: keyframes + easing + delays
- **Hover/scroll effects**: parallax, fade, stagger, reveal
- **Shape dividers**: 6 estilos
- **Presets**: section, text, module, divider, animation, scroll, hover, transform

Origen de datos:
- K-means clustering (scikit-learn) sobre 877 templates reales
- 4 CSVs curados: colors.csv, styles.csv, typography.csv, ux-guidelines.csv
- Output: `ml-dataset/artifacts/decoration-clusters.pkl` + `ml-dataset/artifacts/decoration-rules.json`

---

## Calidad y Cobertura

| Métrica | Valor |
|---------|-------|
| Templates en dataset | 877 |
| Módulos Divi 5 con schema | 103 |
| Precisión content classifier (D) | 98.2% |
| Slot types (B2) | 9 (titles, paragraphs, buttons, images, features, testimonials, stats, logos, items) |
| Clusters de decoración (E) | 7 |
| CSVs curados (E) | 4 |
| Presets en design system (`site/<DAW_SITE>/brand/_design_presets.json`) | **64** |
| Presets realmente usados por el pipeline | **~30%** |

### Gap: design system infrautilizado

El `_design_presets.json` contiene 64 presets en 8 categorías, pero el pipeline (DIE + mapper) solo referencia una fracción:

| Categoría | Presets existentes | Presets referenciados por el pipeline |
|-----------|-------------------|--------------------------------------|
| `section:` | 8 (hero-dark, hero-image-dark, hero-video, trust-bar, cta-epic, light, dark, white) | 4 (hero-dark, trust-bar, cta-epic, light) — vía `SECTION_PRESET_FALLBACK` |
| `text:` | 12 (eyebrow, hero-title, display-xl, display-md, headline, lead, stat-num, quote-serif, caption...) | ~3 (inyectados por templates individuales, no por el pipeline) |
| **`module:`** | **9** (card, feature-card, stat-item, testimonial-card, image-shadow, accent-line, glass-card + 4 btn-*) | **2** (feature-card, testimonial-card) — solo en `ITEM_TEMPLATES` |
| **`animation:`** | **10** (fade-in, fade-in-fast, slide-up, slide-down, slide-left, slide-right, reveal-up, zoom-in, bounce-up, flip, fold, roll) | **0** — `_add_animations` los reemplaza todos con `fade 600ms` hardcodeado |
| **`scroll:`** | **7** (fade-in, parallax-up, parallax-down, scale-in, reveal, rotate, blur-in) | **0** — nunca referenciados |
| **`transform:`** | **5** (hover-lift, hover-scale, hover-glow, hover-slide-up, hover-expand) | **1** (hover-lift) — solo en `ITEM_TEMPLATES` |
| **`divider:`** | **6** (curve-top, curve-bottom, wave-top, wave-bottom, tilt-top) | **0** — shape dividers nunca aplicados |
| **`btn-*:`** | **4** (btn-primary, btn-ghost, btn-outline-light, btn-cta-dark) | **0** — los botones del template no reciben preset de botón; usan decoration heredada |

**Causa raíz**: `_add_animations()` en `e_page_mapper.py` sobrescribe TODAS las animaciones de módulo con `fade 600ms`, independientemente de qué preset traiga el módulo. El decoration engine (E) no referencia presets de `animation:`, `scroll:`, `transform:`, o `divider:` — solo genera `color_scheme`, `typography`, `style_name`, `motion`, y `spacing`.

---

## Gap Analysis: Output Real vs Potencial del Design System

### P0 (RESUELTO — 2026-05-31)
- `_clean_template_garbage` ahora recursivo en `row-inner` containers
- `_value_already_in_section` ahora recursivo en containers anidados
- `_dedup_section_content` nueva función post-procesamiento
- Validado: 0 contenido médico residual en los 4 planes

### P1 (PERSISTE — Decoración monótona)
- `style_name`, `typography`, `motion` idénticos en TODAS las secciones porque se derivan de `tone` (mismo para toda la página), no de `section_type`
- `_add_animations` fuerza `fade 600ms` en todos los módulos — ignora los 10 animation presets + animaciones propias de cada module preset (feature-card tiene `slide 480ms`, testimonial-card tiene `fade 800ms`)
- Scroll effects, shape dividers, hover transforms variados nunca se aplican

### P2 (PERSISTE — Imágenes)
- `resolve_image_src` solo se ejecuta en `_build_item_rows` (imágenes de items), no en imágenes del template
- No es prioritario para el usuario

### P3 (PERSISTE — UX Básica)
- `cursor-pointer` ausente en todos los módulos interactivos
- `prefers-reduced-motion` no implementado
- Focus states no implementados
- Transitions de hover no declaradas (solo botones tienen transition: 300ms)
- `max-width` no usado en ninguna sección

---

## Dataset

- `ml-dataset/dataset.jsonl` — 877 registros limpios con contenido real (usado por B2)
- `ml-dataset/dataset-full.jsonl` — Dataset completo con metadatos adicionales
- `ml-dataset/inventory.csv` — Inventario del catálogo
