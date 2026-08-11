# divi-agentic-core — Plugin WordPress del DAW

Motor nativo para Divi 5: Layout Engine con renderers modulares, sistema de diseño de marca (Token_Registry), y comandos WP-CLI.

## Arquitectura

- **`inc/loader.php`**: Autoloader PSR-4 (namespace `DAC\` + renderers `Divi_Agentic_Core\Core\Renderers`).
- **`inc/core/`**: Token_Registry (fuente de verdad de tokens de marca), Brand_Sync_Handler, Brand_Reset_Handler, Design_Validator, Design_Resolver, Layout_Engine, renderers/, skills/ (hallmark, high-end, impeccable), intelligence/ (catálogos CSV).
- **`inc/cli/`**: Comandos WP-CLI (`wp brand {init,validate,approve,revoke,sync,reset,status}`, `wp agentic {deploy_page,export_page,global_colors,layout_*,template_*,deploy_global_ecosystem}`).
- **`data/`**: Metadata de módulos Divi 5 (`_all_modules_metadata.php`, schemas).
- **`modules/`**: Módulos Divi 5 custom (module.json + render.php + view.js).
- **`bin/`**: Scripts de inspección y utilidades (ver `divi-agentic-core/bin/AGENTS.md`).

## Guía rápida

### Marca

```powershell
.\wp.bat brand init <site>            # crear _design_vars.json
.\wp.bat brand validate <site>        # 54 checks mecánicos
.\wp.bat brand sync <site>            # vars → et_divi + gcids + gvids + divitheme.json
```

### Deploy de página

```powershell
.\workspace\deploy.ps1 -Slug <slug> -Title "<Título>"
```

Detalle del flujo completo en `AGENTS.md` (raíz del DAW) y `RUNBOOK.md`.