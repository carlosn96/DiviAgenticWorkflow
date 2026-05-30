# DAW Bundle — Divi Agentic Workflow

Pipeline inteligente: DIE (Python) → plan.json → build_page.php (PHP) → WordPress Divi 5.

---

## Requisitos

1. **Plugin activo**: `divi-agentic-core` instalado como plugin de WordPress (junction link desde `DAW_bundle/divi-agentic-core/` → `app/public/wp-content/plugins/divi-agentic-core/`). Activar en WP Admin > Plugins.
2. **Archivo `.env`**: Copiar `DAW_bundle/.env.example` → `.env` en la raíz del proyecto y completar valores reales.
3. **Design System**: `site/bibliotheca/design-system/divitheme.json` (generado con `build_design_system.py` v3.0 — inteligencia de diseño).
4. **Dependencias Python DIE**: `python -m pip install -r ml-dataset/requirements.txt` (scikit-learn, sentence-transformers, numpy, scipy, PyYAML).

---

## ⚡ Quickstart

```powershell
# 1. Activar plugin (WP Admin > Plugins > Divi Agentic Core)

# 2. Configurar entorno
Copy-Item DAW_bundle/.env.example .env

# 3. (una vez) Generar schemas de módulos
.\php.bat DAW_bundle/divi-agentic-core/bin/generate-module-schema.php --all

# 4. (una vez) Construir artefactos ML del DIE
python DAW_bundle/ml-dataset/artifacts/e_decorator.py --build
python DAW_bundle/ml-dataset/artifacts/d_content_classifier.py
python DAW_bundle/ml-dataset/artifacts/b_semantic_index.py
python DAW_bundle/ml-dataset/artifacts/a_section_patterns.py
python DAW_bundle/ml-dataset/artifacts/c_module_affinities.py

# 5. Generar design system
$env:DAW_SITE="bibliotheca"
python DAW_bundle/workspace/build_design_system.py

# 6. Sincronizar colores globales
.\wp.bat agentic global_colors sync `
  --design-system="DAW_bundle/site/bibliotheca/design-system/divitheme.json"

# 7. Generar brief (opcional, requiere API key en .env)
python DAW_bundle/workspace/automation/generate_brief.py `
  --prompt "pagina principal de biblioteca digital" --tone editorial

# 8. DIE → plan.json → Build + Deploy
python DAW_bundle/ml-dataset/artifacts/design_intelligence.py `
  --brief-file=DAW_bundle/site/bibliotheca/briefs/home.json `
  --output=DAW_bundle/site/bibliotheca/plans/home.json
.\php.bat DAW_bundle/divi-agentic-core/bin/build_page.php `
  --def=DAW_bundle/site/bibliotheca/plans/home.json `
  --deploy
```

---

## Pipeline

```
brief.json → DIE (A+B+C+D+E) → plan.json → build_page.php --deploy → WordPress
```

### Fase ML: DIE (Design Intelligence Engine)
```powershell
python DAW_bundle/ml-dataset/artifacts/design_intelligence.py `
  --brief-file=site/<DAW_SITE>/briefs/<slug>.json `
  --output=site/<DAW_SITE>/plans/<slug>.json
```

El DIE orquesta 5 artefactos:
- **A** — Section patterns (18 tipos, column structures)
- **B** — Semantic index (892 templates, búsqueda semántica)
- **C** — Module affinities (matriz PMI)
- **D** — Content classifier (TF-IDF + Naive Bayes, 98.2%)
- **E** — Decoration engine (7 clusters K-means + 4 CSVs → gradients, shadows, animations, presets)

Output: `plan.json` con decoration blocks + `{{design:color:*}}` tokens.

### Fase Build: build_page.php
```powershell
php DAW_bundle/divi-agentic-core/bin/build_page.php ^
  --def=DAW_bundle/site/bibliotheca/plans/home.json ^
  --deploy
```

| Flag | Descripción |
|------|-------------|
| `--def=<file>` | Plan de página (en `plans/` o ruta completa) |
| `--out=<file>` | Escribir schema resuelto sin desplegar |
| `--deploy` | Construir + desplegar vía `wp agentic deploy_page` |
| `--front` | Establecer como portada (solo con `--deploy`) |
| `--verify` | Ejecutar verificación post-deploy |
| `--url=<url>` | URL pública para verificación visual |
| `--no-resolve` | Schema raw sin expandir presets/tokens (debug) |
| `--help` | Ayuda |

---

---

## Estructura

```
DAW_bundle/
├── README.md                           <- Este archivo
├── AGENTS.md                           <- Documentación completa del flujo
├── VEREDICTO_GLOBAL_DAW.md             <- Diagnóstico unificado del sistema
├── .env.example                        <- Template de configuración
├── site/                               <- ⭐ DATOS DE PROYECTO
│   ├── bibliotheca/                    <-    Marca activa (brand/, plans/, briefs/, pages/, design-system/)
│   └── example/                        <-    Template para nuevas marcas
├── ml-dataset/                         <- ⭐ ML: dataset + artefactos del DIE
│   ├── dataset.jsonl                   <-    877 templates Divi 4
│   ├── requirements.txt                <-    Dependencias Python
│   ├── PLAN.md                         <-    Arquitectura de artefactos
│   ├── TASKS.md                        <-    Tracking de progreso
│   └── artifacts/                      <-    Scripts + modelos (A, B, C, D, E + DIE)
│       ├── design_intelligence.py      <-       ⭐ Orquestador (--brief-file)
│       ├── e_decorator.py              <-       Decoration Engine (--build)
│       ├── section-patterns.json       <-       Output A
│       ├── semantic-index.pkl          <-       Output B
│       ├── module-affinities.json      <-       Output C
│       └── content-classifier.pkl      <-       Output D
├── workspace/
│   ├── build_design_system.py          <- Diseño inteligente v3.0
│   ├── data/modules/                   <- Schemas de módulos Divi 5 (102)
│   └── automation/                     <- Scripts de automatización
├── daw-skill/                          <- Orquestación de 4 fases (SKILL.md)
├── divi-agentic-core/
│   ├── Plugin WordPress (Layout Engine + CLI + metadata)
│   └── bin/
│       ├── build_page.php              <- ⭐ Único script PHP de build+deploy
│       └── generate-module-schema.php  <- Genera schemas de módulos
├── ui-ux-pro-max/                      <- Skill externo de diseño UI/UX
└── tests/                              <- Tests del pipeline
```

---

## Reglas

1. Namespace correcto: `divi/*` — nunca `et_pb_*`.
2. Colores como `{{design:color:*}}` — nunca hex hardcodeados.
3. Plans en `site/<DAW_SITE>/plans/`.
4. Pipeline: `brief.json → DIE (Python) → plans/<slug>.json → build_page.php --deploy` → WordPress.
5. Sin CSS inyectado en `functions.php` ni overrides en `style.css`.
6. No editar `divitheme.json` a mano — regenerar con `build_design_system.py` (v3.0 con inteligencia de diseño).
7. El DIE (Python, ML) genera el plan; `build_page.php` (PHP) ejecuta el deploy. Cada uno en su lenguaje.
8. **site/ es la frontera**: framework DAW puro arriba, datos de proyecto en `site/<DAW_SITE>/`.

---

## Referencias

| Recurso | Path |
|---------|------|
| Documentación completa del flujo | `AGENTS.md` |
| Diagnóstico del sistema | `VEREDICTO_GLOBAL_DAW.md` |
| Orquestación 4 fases | `daw-skill/SKILL.md` |
| Diccionario de bloques | `daw-skill/references/blocks-dictionary.md` |
| Lógica del diseñador | `daw-skill/references/designer.md` |
| Lógica del ingeniero | `daw-skill/references/engineer.md` |
| DIE — Design Intelligence Engine | `ml-dataset/artifacts/design_intelligence.py` |
| Arquitectura de artefactos ML | `ml-dataset/PLAN.md` |
| Tracking de artefactos | `ml-dataset/TASKS.md` |
| Decoration Engine (E) | `ml-dataset/artifacts/e_decorator.py` |
