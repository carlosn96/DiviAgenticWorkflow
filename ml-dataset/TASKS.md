# Estado de Artefactos Inteligentes

Actualizado: 2026-05-29

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

## DIE: Design Intelligence Engine (Orquestador)
- [x] Script: `ml-dataset/artifacts/design_intelligence.py`
- [x] Integración con PHP: `orchestrate_page.php`
- [x] Pipeline: brief → call_die() → catalog template → compose → build

---

## Registro de Cambios

| Fecha | Artefacto | Cambio | Estado |
|---|---|---|---|
| 2026-05-29 | A | Build inicial | ✅ |
| 2026-05-29 | A | Output verificado: 18 tipos, 877 templates, estructura + módulos + decoraciones | ✅ |
| 2026-05-29 | B | Build + verificado: 892 templates indexados, búsqueda semántica con categorías reales | ✅ |
| 2026-05-29 | C | Build + verificado: matriz PMI con 18 tipos de sección, afinidades reales | ✅ |
| 2026-05-29 | D | Build + verificado: 98.2% accuracy en training, clasifica español e inglés | ✅ |
| 2026-05-29 | DIE | Build + verificado: orquesta A+B+C+D, produce plan.json accionable | ✅ |
| 2026-05-29 | DIE | Integración con orchestrate_page.php: DIE genera plans, PHP usa catalog templates con fallback | ✅ |
| 2026-05-29 | DIE | Fix: template fallback para queries sin word overlap (español) | ✅ |
| 2026-05-29 | DIE | Fix: trust brief section_type sobre clasificador D (evita sobreescritura) | ✅ |
