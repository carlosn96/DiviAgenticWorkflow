# DAW Module: Phase 4 — CLI Execution (The Engineer)

## Objetivo
Tomar la definición de página, construir el schema completo y desplegarlo en WordPress.

---

## Prequisito: Regenerar Design System

Si el design system cambió (nuevos colores, fuentes, presets), regenerarlo antes de desplegar:

```powershell
python DAW_bundle/workspace/build_design_system.py
```

Esto genera:
- `site/<DAW_SITE>/design-system/divitheme.json`
- `site/<DAW_SITE>/brand/assets/css/brand.css` (por marca, único)

---

## Flujo Actual de Deploy

### Paso 1: Combinar manifiesto + secciones

El page-def se divide en manifiesto (`<slug>.json`) y secciones (`sections/*.json`):

```powershell
python DAW_bundle/site/<DAW_SITE>/page-defs/combine.py `
  DAW_bundle/site/<DAW_SITE>/page-defs/<slug>.json `
  --out DAW_bundle/site/<DAW_SITE>/page-defs/<slug>-combined.json
```

### Paso 2: Build + Deploy

```powershell
.\php.bat DAW_bundle/divi-agentic-core/bin/build_page.php `
  --def="<slug>-combined.json" --deploy
```

> El path de `--def` es relativo a `site/<DAW_SITE>/page-defs/`. El flag `--deploy` ejecuta el deploy automáticamente.

`build_page.php` hace todo:
- Carga la definición de página
- Carga el design system desde `site/<DAW_SITE>/design-system/divitheme.json`
- Resuelve `{{design:color:*}}` → `var(--gcid-*)`
- Expande presets inline
- Normaliza gradient stops
- Valida estructura (sections → rows → columns → modules)
- Ejecuta `wp agentic deploy_page`

> [!NOTE]
> `build_page.php` ya **no ejecuta `sync_css`** post-deploy. El CSS de marca se sirve desde disco vía el enqueue del plugin en runtime. No necesitas sincronizar nada después del deploy.

### Opciones adicionales

```powershell
# Portada
.\php.bat build_page.php --def="<slug>-combined.json" --deploy --front

# Solo build (debug)
.\php.bat build_page.php --def="<slug>-combined.json" --out=debug.json

# Verificación post-deploy
.\php.bat build_page.php --def="<slug>-combined.json" --deploy --verify
```

---

## Paso 3: Limpiar caché de Divi

```powershell
.\wp.bat eval "et_core_clear_wp_cache();"
```

---

## Paso 4: Verificar persistencia

```powershell
.\wp.bat post list --post_type=page --name="<slug>" --format=json
.\wp.bat post meta get <ID> _et_pb_built_with_d5
.\wp.bat post meta get <ID> _et_builder_version
```

**Resultado esperado:** `_et_pb_built_with_d5` → `1`, `_et_builder_version` → `5.5.0`

---

## Flujo de CSS de Marca (sin BD)

El CSS de marca (`daw-*` classes, variables CSS) se sirve desde disco:

```
brand.css se encola como daw-brand-css en wp_enqueue_scripts
design tokens se inyectan como inline styles
module CSS se encola via Module_Registry
```

No hay escritura a la BD. `sync_css` ya no se ejecuta en deploy.

Si necesitas **limpiar datos legacy** (por ejemplo después de migrar de una versión anterior):

```powershell
.\wp.bat agentic sync_css
# → Verifica archivos en disco
# → Limpia et_custom_css legacy
# → Vacía custom_css CPT
# No es necesario en el día a día
```

---

## Subcomandos `wp agentic` Disponibles

| Subcomando | Descripción |
|------------|-------------|
| `global_colors sync` | Sincroniza colores del design system → Divi 5 Global Colors |
| `global_colors status` | Verifica estado de sync |
| `global_colors list` | Lista Global Colors registrados |
| `deploy_page` | Crea o actualiza una página desde un JSON schema |
| `export_page --slug=<slug>` | Exporta página WP a schema editable |
| `sync_css` | Ya no escribe — solo limpia legacy y verifica archivos |

---

## Two-Layer Resolution (var(--gcid-*) → $variable())

El Design Resolver emite `var(--gcid-accent)`. El Layout Engine convierte a sintaxis que Divi 5 VB entiende:

```
var(--gcid-accent) → $variable({"type":"color","value":{"name":"gcid-accent","settings":{}}})$
```

Código relevante: `divi-agentic-core/inc/core/class-layout-engine.php:845-875`.

---

## Troubleshooting

| Síntoma | Causa | Solución |
|---------|-------|----------|
| `StyleDeclarations::add('border-width', Array)` | `border.all.width` es objeto per-side en vez de string | Usar `"width": "1px"` en vez de `{top,right,bottom,left}` en page-def |
| `UnexpectedValueException` en `MultiViewUtils` | Atributo de contenido es array en vez de string | Revisar que `innerContent.desktop.value` sea string |
| Color no se ve en VB (sí en frontend) | Bloque usa `var(--gcid-*)` en lugar de `$variable()` | Redeployar con Layout Engine actualizado |
| Error: WP-CLI deployment failed | Falla en `build_page.php --deploy` | Ejecutar sin `--deploy` para ver errores de build |
| Página no renderiza estilos | Caché de Divi | `.\wp.bat eval "et_core_clear_wp_cache();"` |
