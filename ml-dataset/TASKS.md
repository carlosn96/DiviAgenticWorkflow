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
