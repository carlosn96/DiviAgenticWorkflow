# DAW — Divi Agentic Workflow

Pipeline: `_design_vars.json` → `wp brand sync` → Divi Customizer + Global Colors/Variables → `page-defs` → `combine.py` → `deploy_page` → WordPress Divi 5.

---

## Requisitos

1. **Plugin activo**: `divi-agentic-core` visible desde `wp-content/plugins/` (junction link a `divi-agentic-core/`). Activarlo en WP Admin > Plugins.
2. **Wrapper `wp`**: un passthrough `wp.bat` (Win) o `wp` (Unix) en `$WpRoot` (raíz de WordPress) que invoque WP-CLI. Ver AGENTS.md §0.1.
3. **Archivo `.env`** en `$WpRoot` con `DAW_SITE=<marca>` (copia `DiviAgenticWorkflow/.env.example`).
4. **Brand vars**: `site/<DAW_SITE>/brand/_design_vars.json` — editar colores, fuentes, logo.

---

## Quickstart

```powershell
# 1. Configurar .env (DAW_SITE=<nombre>) y el wrapper wp.bat en $WpRoot

# 2. Marca: crear + sincronizar a Divi Customizer
.\wp.bat brand init <site>
.\wp.bat brand sync <site>

# 3. Crear page-defs (ver AGENTS.md §4)
#    site/<site>/page-defs/<slug>/manifest.json + sections/*.json + css/*.css

# 4. Desplegar con el wrapper (hace combine + deploy_page + flush)
.\workspace\deploy.ps1 -Slug <slug> -Title "<Título>"
```

---

## Pipeline

```
_design_vars.json
   └── wp brand sync ──► wp_options['et_divi'] (Customizer global)
                 ├──► divitheme.json (presets + strategy)
                 ├──► gcids (Global Colors) via GlobalData::set_global_colors()
                 └──► gvids (Global Variables: radios, espacios, fuentes)

page-defs/<slug>/manifest.json + sections/*.json + css/*.css
   └── workspace/combine.py ──► <slug>-combined.json
         └── wp agentic deploy_page ──► post_content en WP (Divi 5 blocks)
```

---

## Enlaces

| Recurso | Path | Propósito |
|---------|------|-----------|
| Documentación completa | `AGENTS.md` | Fuente de verdad del flujo |
| Runbook | `RUNBOOK.md` | Comandos frecuentes |
| Orquestación 4 fases | `daw-skill/SKILL.md` | Análisis → diseño → mapeo → CLI |
| Brand (commands) | `wp brand {init,validate,approve,sync,reset,status}` | Gestión del sistema de diseño |
| Deploy | `wp agentic deploy_page` + `workspace/deploy.ps1` | Compila y publica páginas |
| Example checker | `divi-agentic-core/bin/check-example.php` | Mantiene `site/example` sincronizado con `Token_Registry` |