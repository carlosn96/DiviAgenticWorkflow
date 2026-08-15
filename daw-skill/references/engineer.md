# DAW Module: Phase 4 — CLI Execution (The Engineer)

## Objetivo
Tomar la definición de página, construir el schema completo y desplegarlo en WordPress.

---

## Prequisito: Sincronizar Brand (único comando)

Si el brand cambió (colores, fuentes, logo), sincronizar antes de desplegar:

```powershell
.\wp brand sync <slug>
```

Esto sincroniza **todo** en un paso: `et_divi` (Customizer) + `divitheme.json` (presets) + gcids (colores globales vivos) + gvids (variables nativas Divi 5 para radios, espacios y fuentes).

---

## Flujo Actual de Deploy

> **Regla #5 de AGENTS.md**: usar siempre los wrappers de `workspace/`, no comandos sueltos.

### Wrapper (recomendado) — combina, despliega y flushea caché

```powershell
# Página
.\workspace\deploy.ps1 -Slug <slug> -Title "Título"

# Template global (header/footer/body) — ver §Templates más abajo
.\workspace\deploy-template.ps1 -UseOn "singular:post_type:page:all" -Title "Todas las páginas"
```

`deploy.ps1` ejecuta: `combine.py` → `wp agentic deploy_page` → flush de caché (`wp cache flush` + borra `wp-content/et-cache/*`).

### Paso 1: Combinar manifiesto + secciones

El page-def es una carpeta: `page-defs/<slug>/` con `manifest.json`, `sections/*.json` y opcional `css/*.css`:

```powershell
python workspace/combine.py `
  site/<DAW_SITE>/page-defs/<slug>/manifest.json `
  --out site/<DAW_SITE>/page-defs/<slug>/<slug>-combined.json
```

> ⚠️ Si una sección tiene CSS freeForm, se guarda en `css/<sección>.css` (lo inyecta `combine.py`). **Ningún `<` en ese CSS** — `wp_strip_all_tags()` trunca (AGENTS.md §4.6 / regla #15).

### Paso 2: Deploy directo (con Layout Engine refactorizado)

```powershell
.\wp.bat agentic deploy_page `
  --title="Título de la página" `
  --slug="<slug>" `
  --schema="site/<DAW_SITE>/page-defs/<slug>/<slug>-combined.json" `
  --design-system="site/<DAW_SITE>/design-system/divitheme.json"
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
.\wp.bat cache flush
# + borrar la caché estática de Divi (lo hace deploy.ps1 automáticamente):
Remove-Item -Path "wp-content\et-cache\*" -Recurse -Force
```

> ⚠️ **Trilogía de caché** (AGENTS.md): los URLs de `et-cache` no cambian entre regeneraciones. Si un fix "no se ve", hacer: purge + `ET_Core_PageResource::remove_static_resources()` + borrar los `*.css` de `et-cache` + hard refresh. **Ojo (render-verificado):** los archivos estáticos de `et-cache` mantienen su URL entre regeneraciones, así que un CSS viejo puede seguir sirviéndose incluso tras regenerar. Para confirmar si un fix aplicó, inspeccionar el CSS servido en vivo (fetch del HTML final) con greps específicos del selector — no asumir que el deploy falló solo porque el frontend no cambió.

## Paso 4: Verificar persistencia

```powershell
.\wp.bat post list --post_type=page --name="<slug>" --format=json
.\wp.bat post meta get <ID> _et_pb_built_with_d5
.\wp.bat post meta get <ID> _et_builder_version

# Verificación estructural post-deploy (scripts de bin/)
php divi-agentic-core/bin/verify_page.php --slug=<slug>        # sano + gcids renderizan
php divi-agentic-core/bin/check_frontend.php <slug>            # frontend sin errores
php divi-agentic-core/bin/validate_block_structure.php <ID>    # bloques bien formados
```

**Resultado esperado:** `_et_pb_built_with_d5` → `1`, `_et_builder_version` → `5.10.1`

---

## Brand CSS (Pipeline Actual)

El brand se sincroniza a `wp_options['et_divi']` mediante `wp brand sync`. Divi genera y encola el CSS automáticamente. No hay CSS propio de marca, ni encolado manual, ni archivos brand.css en disco.

---

## Subcomandos `wp agentic` Disponibles

| Subcomando | Descripción |
|------------|-------------|
| `deploy_page` | Crea o actualiza una página desde un JSON schema (wrapper: `deploy.ps1`) |
| `export_page --slug=<slug>` | Exporta página WP a schema editable |
| `global_colors {sync,status,list}` | Sincroniza/verifica/lista Global Colors (gcids). El sync lo hace `wp brand sync` inline |
| `template_create --use-on= --title=` | Crea template. Falla si `--use-on` ya existe |
| `template_find --use-on=` | Retorna ID del template o 0 si no existe |
| `template_ensure --use-on= --title=` | Crea si no existe, retorna el existente |
| `template_default` | Retorna el template default (lo crea si falta) |
| `template_show <id>` | Muestra template (use-on, layouts, enabled) |
| `template_update <id> --title --use-on` | Actualiza título y/o use-on |
| `template_delete <id>` | Trashes el template y lo desvincula |
| `template_wire <id> --*-id= [--*-enabled=] [--*-global=]` | Asigna layouts a un template |
| `layout_deploy <type> --schema=` | Crea un layout nuevo (nunca sobrescribe). Retorna ID |
| `layout_ensure <type> --schema= --by-id=` | Actualiza un layout existente por ID |
| `layout_list <type>` | Lista layouts con ID y título |
| `deploy_global_ecosystem ...` | Convenience: header + footer + body + template en uno (`--mode=create|update|upsert`) |
| `sync_css` | **Legacy** (pipeline viejo). No usar — Divi genera el CSS desde Customizer |

## Templates (Theme Builder)

Desplegar header/footer/body globales vía el wrapper:

```powershell
# Default — aplica a TODAS las páginas
.\workspace\deploy-template.ps1 -Default -Title "Footer"

# Custom — solo páginas que cumplan la condición
.\workspace\deploy-template.ps1 -UseOn "singular:post_type:page:all" -Title "Footer Pages" -FooterPath "site/<site>/page-defs/footer/footer-combined.json"

# Solo body, layout exclusivo, sin header/footer
.\workspace\deploy-template.ps1 -UseOn "404" -Title "Error 404" -BodyPath "..." -BodyGlobal 0 -HeaderEnabled 0 -FooterEnabled 0
```

`deploy-template.ps1` resuelve templates por `--use-on`, reusa layouts existentes (no duplica) y soporta `-Mode create|update|upsert`. Parámetros completos y tabla de `--use-on` válidos: `../AGENTS.md` §5.

> ⚠️ **R14 (render-verificado en Divi 5.10):** los templates **solo header+footer renderizan el body VACÍO** (el contenido de la página no cae en el layout). Usar SIEMPRE las 3 áreas `["header","body","footer"]` — el body es el layout que monta el `divi/post-content`. Un "default" solo-header/footer en producción = páginas en blanco. Al regenerar un template existente, re-usar los layout IDs (`-HeaderId`/`-FooterId`/`-BodyId`) o re-aplicar desde la Library; no borrar y recrear layouts (los GCIDs/GCIDs del header se re-vinculan).

## Brand Quality Gate (antes de sync)

```powershell
.\wp brand validate <slug> [--suggest]      # 54+ checks: contraste WCAG AAA, escala, armonía, pairing
.\wp brand approve <slug>                    # persiste aprobación con vars_hash (.design-pass)
.\wp brand sync <slug>                       # bloquea si no hay approve o si vars cambiaron
.\wp brand sync <slug> --force               # bypass total (solo si se aprobó explícitamente)
```

`Brand_Sync_Handler` ejecuta la validación automáticamente en cada sync. Si falla, aborta con instrucciones.

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
| Página no renderiza estilos | Caché de Divi | `.\wp.bat cache flush` + borrar `wp-content\et-cache\*` |
| **CSS se trunca / selectores desaparecen** | `wp_strip_all_tags()` encontró un `<` en el freeForm CSS | Eliminar cualquier `<` del CSS (incluso en comentarios) — AGENTS.md §4.6 |
| **Fix "no se ve" tras deploy** | Caché estática de Divi mantiene URLs | Trilogía: purge + `remove_static_resources()` + borrar `et-cache` + hard refresh (AGENTS.md §11). Verificar en el CSS vivo con grep, no asumir que el deploy falló |
| Bloque corrupto / mal generado | Estructura de bloques rota en post_content | `php divi-agentic-core/bin/validate_block_structure.php <post_id>` |
