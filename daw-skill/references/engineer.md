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
python DAW_bundle/workspace/combine.py `
  DAW_bundle/site/<DAW_SITE>/page-defs/<slug>.json `
  --out DAW_bundle/site/<DAW_SITE>/page-defs/<slug>-combined.json
```

### Paso 2: Deploy directo (con Layout Engine refactorizado)

```powershell
.\wp.bat agentic deploy_page `
  --title="Título de la página" `
  --slug="<slug>" `
  --schema="DAW_bundle/site/<DAW_SITE>/page-defs/<slug>-combined.json" `
  --design-system="DAW_bundle/site/<DAW_SITE>/design-system/divitheme.json"
```

`deploy_page` hace todo:
- Carga design system desde `site/<DAW_SITE>/design-system/divitheme.json`
- Resuelve `{{design:color:*}}` → `var(--gcid-*)`
- Resuelve `{{design:font|radius|space:name}}` → literales
- Compila a Divi 5 blocks via Layout Engine refactorizado
  → Dispatcher delgado enruta a renderers modulares (`inc/core/renderers/*.php`)
  → Namespaces de terceros (`dgpc/*`, `dac/*`) tienen renderer propio
  → Convierte `var(--gcid-*)` → `$variable()` en post_content

> [!NOTE]
> `build_page.php` es **legacy** y ya no se usa para deploy. No tiene schemas para módulos de terceros (`dgpc`, etc). Si el combined.json contiene tokens `{{design:*}}`, `deploy_page` los resuelve igual.

### Opciones adicionales

```powershell
# Portada
.\wp.bat agentic deploy_page --title="..." --slug="<slug>" --schema="..." --design-system="..." --front

# Si el schema tiene tokens {{design:color:*}} sin resolver, deploy_page los maneja automáticamente
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
| Error: WP-CLI deployment failed | Falla en `wp agentic deploy_page` | Verificar que el schema JSON sea válido y que combine.py se haya ejecutado |
| Página no renderiza estilos | Caché de Divi | `.\wp.bat eval "et_core_clear_wp_cache();"` |
