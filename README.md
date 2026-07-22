# DAW Bundle — Divi Agentic Workflow

Pipeline: Brand vars → brand-sync.php → Divi Customizer → page-defs → combine.py → deploy_page → WordPress Divi 5.

---

## Requisitos

1. **Plugin activo**: `divi-agentic-core` como junction link desde `DAW_bundle/divi-agentic-core/` → `app/public/wp-content/plugins/divi-agentic-core/`. Activar en WP Admin > Plugins.
2. **Archivo `.env`**: Copiar `DAW_bundle/.env.example` → `.env` en la raíz del proyecto y completar valores reales.
3. **Brand vars**: `site/<DAW_SITE>/brand/_design_vars.json` — editar colores, fuentes, logo.

---

## ⚡ Quickstart

```powershell
# 1. Configurar entorno y marca activa en .env (DAW_SITE=<nombre>)

# 2. Sincronizar brand a Divi Customizer
.\wp eval-file DAW_bundle/divi-agentic-core/bin/brand-sync.php `
  DAW_bundle/site/<DAW_SITE>/brand/_design_vars.json

# 3. Crear page-defs (ver AGENTS.md §4)
#    site/<DAW_SITE>/page-defs/<slug>.json (manifiesto)
#    site/<DAW_SITE>/page-defs/sections/<section>.json (secciones)

# 4. Combinar y desplegar
python DAW_bundle/workspace/combine.py `
  DAW_bundle/site/<DAW_SITE>/page-defs/<slug>.json `
  --out DAW_bundle/site/<DAW_SITE>/page-defs/<slug>-combined.json
.\wp.bat agentic deploy_page `
  --title="Título" --slug="<slug>" `
  --schema="DAW_bundle/site/<DAW_SITE>/page-defs/<slug>-combined.json" `
  --design-system="DAW_bundle/site/<DAW_SITE>/design-system/divitheme.json"
```

---

## Pipeline

```
_design_vars.json
    │
    ▼
brand-sync.php → wp_options['et_divi'] → Divi Customizer CSS engine
    │
    ▼
page-defs/<slug>.json (manifiesto) + sections/*.json
    │
    ▼
workspace/combine.py → <slug>-combined.json
    │
    ▼
wp agentic deploy_page → post_content en WP
```

---

## Enlaces

| Recurso | Path |
|---------|------|
| Documentación completa | `AGENTS.md` |
| Orquestación 4 fases | `daw-skill/SKILL.md` |
| Brand Sync | `divi-agentic-core/bin/brand-sync.php` |
| Deploy | `divi-agentic-core/inc/core/class-layout-engine.php` |
