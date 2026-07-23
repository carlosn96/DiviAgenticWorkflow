# RUNBOOK — Pipeline DAW

Un solo comando WP-CLI. Sin `eval-file`.

```powershell
.\wp brand <comando> [<slug>]
```

| Comando | Qué hace |
|---------|----------|
| `init` | Crea `_design_vars.json` (solo si no existe) |
| `sync` | Sincroniza el diseño a WordPress |
| `reset` | Revierte todo a valores de fábrica de Divi |
| `status` | Muestra estado actual del brand |

`<slug>` es opcional. Si se omite, usa `DAW_SITE` del `.env`.

## Marca nueva

```powershell
# 1. Editar .env — DAW_SITE=nombre-de-tu-marca
.\wp brand init

# 2. Cargar un skill de dirección visual (hallmark, impeccable, high-end-visual-design)
#    y editar site/<DAW_SITE>/brand/_design_vars.json con criterio de diseño real

# 3. Sincronizar
.\wp brand sync
```

## Página nueva

```powershell
# 1. Crear page-defs/<slug>.json + sections/*.json
# 2. Combinar
python DiviAgenticWorkflow/workspace/combine.py `
  DiviAgenticWorkflow/site/<DAW_SITE>/page-defs/<slug>.json `
  --out DiviAgenticWorkflow/site/<DAW_SITE>/page-defs/<slug>-combined.json
# 3. Deployar
.\wp agentic deploy_page --title="Título" --slug="<slug>" `
  --schema="DiviAgenticWorkflow/site/<DAW_SITE>/page-defs/<slug>-combined.json" `
  --design-system="DiviAgenticWorkflow/site/<DAW_SITE>/design-system/divitheme.json"
```

## Si algo falla

```powershell
.\wp brand reset
.\wp brand sync
```

## Notas

- `wp brand` es el ÚNICO comando que existe para el usuario.
- Los scripts en `bin/` (`brand-sync.php`, `brand-reset.php`, `brand.php`) son LEGACY. No se usan. El plugin registra el comando `wp brand` directamente.
- Los skills de dirección visual (hallmark, impeccable, high-end-visual-design) deben cargarse ANTES de editar `_design_vars.json`.
- Token_Registry, Design_Resolver, Customizer_Engine son internos. No hay que pensarlos.
