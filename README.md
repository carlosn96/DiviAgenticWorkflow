# DAW Bundle — Divi Agentic Workflow

Pipeline: Brief → VIE → plan.json → build_page.php → WordPress Divi 5.

---

## Requisitos

1. **Plugin activo**: `divi-agentic-core` como junction link desde `DAW_bundle/divi-agentic-core/` → `app/public/wp-content/plugins/divi-agentic-core/`. Activar en WP Admin > Plugins.
2. **Archivo `.env`**: Copiar `DAW_bundle/.env.example` → `.env` en la raíz del proyecto y completar valores reales.
3. **Design System**: `site/<DAW_SITE>/design-system/divitheme.json` (generado con `build_design_system.py` v4.0).

---

## ⚡ Quickstart

```powershell
# 1. Configurar entorno y marca activa en .env (DAW_SITE=<nombre>)

# 2. (una vez) Generar schemas de módulos
.\php.bat DAW_bundle/divi-agentic-core/bin/generate-module-schema.php --all

# 3. Generar design system
python DAW_bundle/workspace/build_design_system.py

# 4. Sincronizar colores globales
.\wp.bat agentic global_colors sync `
  --design-system="DAW_bundle/site/<DAW_SITE>/design-system/divitheme.json"

# 5. Pipeline completo (orquestador)
python DAW_bundle/workspace/daw_build.py --site $env:DAW_SITE --full --vie --prompt "descripción breve"

# O paso a paso:
#   5a. Brief
python DAW_bundle/workspace/automation/generate_brief.py --prompt "pagina principal" --tone editorial
#   5b. VIE → plan.json
python DAW_bundle/vie/cli.py `
  --brief-file=site/<DAW_SITE>/briefs/home.json `
  --design-system=site/<DAW_SITE>/design-system/divitheme.json `
  --output=site/<DAW_SITE>/plans/home.json
#   5c. Build + Deploy
.\php.bat DAW_bundle/divi-agentic-core/bin/build_page.php `
  --def=site/<DAW_SITE>/plans/home.json --deploy
```

---

## Pipeline

```
brief.json (con o sin design_direction)
    │
    ▼
VIE v3.0 (determinístico)
    │  (con design_direction → PATH A: diseño calculado por mood)
    │  (sin design_direction  → PATH B: presets fijos originales)
    ▼
plan.json (structure + decoration blocks + {{design:*}} tokens)
    │
    ▼
build_page.php → WordPress Divi 5
```

Pipeline ML anterior (DIE: 877 templates, clasificador TF-IDF, Hungarian slot assigner)
archivado en `_archive/die_pipeline/`. Ver `AGENTS.md` para detalles.

---

## Enlaces

| Recurso | Path |
|---------|------|
| Documentación completa | `AGENTS.md` |
| Orquestación 4 fases | `daw-skill/SKILL.md` |
| VIE package | `vie/` |
| Build + Deploy | `divi-agentic-core/bin/build_page.php` |
| Orquestador unificado | `workspace/daw_build.py` |
| DIE (archivado) | `_archive/die_pipeline/` |
