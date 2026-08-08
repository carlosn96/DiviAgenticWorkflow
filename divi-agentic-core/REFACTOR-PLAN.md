# REFACTOR PLAN — DAC Architecture Consolidation

## Problema raíz
`Token_Registry` se creó como fuente de verdad única, pero los consumidores
(brand-sync, Design_Resolver, Customizer_Engine, BlocksToSchema, AgenticCommand,
AI_Bridge) aún tienen **hardcodeos, duplicaciones y derivaciones inline** que
generan deuda técnica. Cada nuevo token requiere editar N archivos.

## Principios de diseño aplicados
1. **Single Source of Truth** — Todo token vive en `Token_Registry`. Nada se hardcodea fuera.
2. **Dependency Inversion** — Consumidores dependen de `Token_Registry`, no de sus propios datos locales.
3. **Open/Closed** — Nuevos tokens = solo editar `Token_Registry`. Consumidores cerrados a modificación.
4. **DRY** — Cero duplicación de mappings, defaults, slots. Cada concepto existe una vez.

---

## CAPA 0 — Token_Registry (class-token-registry.php)
### Qué agregar
[M] Nuevo método `get_customizer_slots(): array`
```
'primary'   => 'gcid-primary-color',
'secondary' => 'gcid-secondary-color',
'heading'   => 'gcid-heading-color',
'body'      => 'gcid-body-color',
'link'      => 'gcid-link-color',
```
Reemplaza 4 copias: brand-sync.php:106, blocks-to-schema.php:403,
agentic-command.php:109, y los slugs hardcodeados en design-resolver.php:79.

[M] Nueva sección `'post_sync'` en cada token def — handlers post-sync
```
'logo_id' => [
    'type' => 'id', 'default' => null, 'et_divi' => [],
    'post_sync' => ['handler' => 'attachment_url', 'option' => 'divi_logo', 'target' => 'et'],
],
'favicon_id' => [
    'type' => 'id', 'default' => null, 'et_divi' => [],
    'post_sync' => ['handler' => 'attachment_id', 'option' => 'site_icon', 'target' => 'wp'],
],
'apple_icon_id' => [
    'type' => 'id', 'default' => null, 'et_divi' => [],
    'post_sync' => ['handler' => 'attachment_url', 'option' => 'divi_apple_touch_icon', 'target' => 'et'],
],
```

[H] Nuevo método `get_post_sync_handlers(): array`
Retorna solo tokens con `post_sync` definido.

[H] Nuevo método `get_gcid_slugs_to_skip(): array`
Retorna los slugs de customizer slots para que Design_Resolver los salte.
```
['primary-color', 'secondary-color', 'heading-color', 'body-color', 'link-color']
```

### Qué limpiar
[M] `get_customizer_slot_keys()` → **ELIMINAR** (siempre retorna `[]`)
[M] `is_secondary_key()` → **ELIMINAR** (nunca llamado)
[M] `resolve_secondary_key()` → **ELIMINAR** (nunca llamado)
[L] Fix PHP 8.2: `private static ?array $tokens = null` (ya fixeado)

---

## CAPA 1 — brand-sync.php
### Qué limpiar
[CRITICAL] `const CUSTOMIZER_SLOTS` → **ELIMINAR**. Usar `Token_Registry::get_customizer_slots()`.
[M] `get_prefixed_values()` → **ELIMINAR** (dead code, nunca llamado).
[H] Derivation `_secondary_accent` inline → Token_Registry ya lo incluye en `get_et_divi_map()`.
     Mantener la derivación inline porque es lógica de transformación, no dato.
     Pero documentar: "este loop procesa también claves que empiezan con '_' como derivaciones".

### Qué refactorizar
[H] Loop de logo/favicon/apple en `sync_et_divi()`:
    - Leer `Token_Registry::get_post_sync_handlers()`
    - Loop genérico con switch por handler type:
      - `attachment_url`: `wp_get_attachment_url()` → `et_update_option()`
      - `attachment_id`: `(int)` → `update_option()`

### Pseudocódigo post-refactor sync_et_divi()
```
function sync_et_divi(array $vars): array
    actualizado = []
    // 1. Token primarios (et_divi map)
    for each (source_key → et_keys) in Token_Registry::get_et_divi_map()
        if source_key empieza con '_'
            value = derivación especial (_secondary_accent = color_surface_mid)
        else
            value = vars[source_key]

        if vacío → continue
        aplicar color_ensure_hash si es color
        aplicar font name extraction si es font-family
        for each et_key → et_update_option

    // 2. Post-sync handlers (logo, favicon, apple)
    for each (source_key → handler) in Token_Registry::get_post_sync_handlers()
        id = vars[source_key]
        if empty → continue
        resolver URL según handler type
        escribir opción

    return actualizado
```

---

## CAPA 2 — Design_Resolver (class-design-resolver.php)
### Qué cambiar
[H] Línea 79: hardcoded slugs → `Token_Registry::get_gcid_slugs_to_skip()`
```
$skip_slugs = Token_Registry::get_gcid_slugs_to_skip();
if (in_array($slug, $skip_slugs, true)) continue;
```

[H] `flatten_from_global_variables()`: si gvids no existen → **fallback a defaults de Token_Registry**
```
if (empty($global_vars)) {
    $this->flatten_gvid_defaults_from_registry();
    return;
}
```
Nuevo método `flatten_gvid_defaults_from_registry()`:
```
foreach (Token_Registry::get_defaults() as $key => $value) {
    if (str_contains($key, 'radius_') || str_contains($key, 'space_') ||
        str_contains($key, 'shadow_') || str_contains($key, 'easing_') ||
        str_contains($key, 'duration_')) {
        $prefix = explode('_', $key)[0];
        $slug = substr($key, strlen($prefix) + 1);
        $token = "{{design:{$prefix}:{$slug}}}";
        $this->flat_tokens[$token] = $value;
    }
}
```

---

## CAPA 3 — Customizer_Engine (class-customizer-engine.php)
### Qué cambiar
[H] Refactor existente ya consume Token_Registry en constructor. Verificar que:
    - `build_token_map()` usa `Token_Registry::get_et_divi_map()` (YA)
    - `build_brand_defaults()` usa `Token_Registry::get_defaults()` (YA)
    - No quedan arrays hardcodeados

[L] Agregar type declarations si faltan:
    `private array $token_map;` → ya ok (construido en constructor)
    `private ?array $brand_defaults = null;` → inicializado en constructor

[M] Deprecar `apply_design_file()` y `parse_design_md()` — marcar con `@deprecated`
    La pipeline DESIGN.md ya no se usa. brand-sync.php es el reemplazo.

---

## CAPA 4 — BlocksToSchema (class-blocks-to-schema.php)
### Qué cambiar
[L] Línea 403-409: `$customizer_slots` → usar `Token_Registry::get_customizer_slots()`
```
$customizer_slots = Token_Registry::get_customizer_slots();
// Nota: este array mapea 'primary-color' → 'primary', no 'primary' → 'gcid-primary-color'
// Necesita inversión o adaptador.
```
Realidad: blocks-to-schema tiene el MAPA INVERSO:
```
'primary-color' => 'primary',   // gcid-slug → short name
```
Mientras que Token_Registry tiene:
```
'primary' => 'gcid-primary-color',  // short name → gcid
```
Solución: derivar el mapa inverso desde `Token_Registry::get_customizer_slots()`:
```
$forward = Token_Registry::get_customizer_slots(); // ['primary' => 'gcid-primary-color']
$inverse = [];
foreach ($forward as $short => $gcid) {
    $slug = str_replace('gcid-', '', $gcid); // 'primary-color'
    $inverse[$slug] = $short;                // ['primary-color' => 'primary']
}
```

---

## CAPA 5 — AgenticCommand (class-agentic-command.php)
### Qué cambiar
[L] Línea 109-115: `$customizer_slots` → `Token_Registry::get_customizer_slots()`
Este es el mismo mapping directo `'primary' => 'gcid-primary-color'`, reemplazo directo.

---

## CAPA 6 — AI_Bridge (class-ai-bridge.php)
### Qué cambiar
[M] Hardcoded tokens (líneas 13-31): en lugar de valores fijos, leer defaults de
     Token_Registry. `generate_tokens()` puede usar `Token_Registry::get_defaults()`
     para llenar colores, tipografía, radios, etc. si la query no los especifica.

[M] `tokens_to_design()` (líneas 49-78): en lugar de hardcodear layout 'content_width' => 1600,
     usar `Token_Registry::get_defaults()` para valores por defecto.

### Pseudocódigo
```
private function local_generator(string $query): array {
    $defaults = Token_Registry::get_defaults();

    $tokens = [
        'colors' => [
            'primary'    => $defaults['color_accent'] ?? '#DC2626',
            'secondary'  => $defaults['_secondary_accent'] ?? '#D4A747',
            ...
        ],
        'typography' => [
            'heading' => $defaults['font_display'] ?? 'Playfair Display',
            'body'    => $defaults['font_body'] ?? 'DM Sans',
        ],
        'style' => [
            'radius'        => $defaults['radius_md'] ?? '8px',
            'radius_button' => $defaults['radius_full'] ?? '50px',
        ],
    ];
    ...
}
```

---

## CAPA 7 — Autoloader (inc/loader.php)
### Qué cambiar
[H] Case-sensitivity fix: Normalizar `$dir` a lowercase en el fallback path.
```
$dir = __DIR__ . '/' . strtolower(str_replace('\\', '/', implode('\\', $parts)));
```
Esto asegura que `DAC\CLI\Agentic_Command` busque en `inc/cli/` (no `inc/CLI/`).

[M] Eliminar bloque duplicado de autoload (líneas 57-71):
    El bloque `Divi_Agentic_Core\*` en `Loader::autoload()` (líneas 40-50) y el closure
    independiente (líneas 57-71) hacen EXACTAMENTE lo mismo. Eliminar el closure.

[L] Agregar type hints: `autoload(string $class): void`, `init(): void`

---

## CAPA 8 — Duplicado Layout_Engine (class-layout-engine-test.php)
### Qué hacer
[CRITICAL] Este archivo define `class Layout_Engine` en el mismo namespace que
           `class-layout-engine.php`. Si ambos se cargan → PHP Fatal Error.
           **OPCIÓN A**: Eliminar el archivo (es un test que no se ejecuta como test).
           **OPCIÓN B**: Renombrar la clase a `Layout_Engine_Test` y mover a `tests/`.

---

## CAPA 9 — Deuda menor
### deploy-to-header.php
[H] Línea 15: Ruta absoluta `C:\Users\Departamento WEB\...` → parametrizar.
    Reemplazar con `dirname(__DIR__) . '/temp_header_schema.json'` para que sea relativo
    al plugin, no a una máquina específica.

### trait-module-metadata.php
[L] Líneas 16-18: Typed properties sin null safety.
    `private static $meta_data = null;` → `private static ?array $meta_data = null;`

### dgpc-renderer.php
[L] Línea 22: `private string $builder_version;` → `private ?string $builder_version;`

---

## ORDEN DE EJECUCIÓN

```
Paso 0: Token_Registry (agregar métodos nuevos, eliminar dead code)
Paso 1: brand-sync.php (CUSTOMER_SLOTS → registry, post-sync handlers)
Paso 2: Design_Resolver (slugs desde registry, fallback a defaults)
Paso 3: Customizer_Engine (verificar, deprecar legacy)
Paso 4: BlocksToSchema (customizer slots desde registry)
Paso 5: AgenticCommand (customizer slots desde registry)
Paso 6: AI_Bridge (defaults desde registry)
Paso 7: Autoloader (case-sensitivity, duplicado)
Paso 8: Layout_Engine_Test (eliminar o renombrar)
Paso 9: Deuda menor (deploy-to-header, trait, dgpc)
```

### Leyenda
[CRITICAL] → rompe en prod si no se arregla
[H] → high priority, parte del core token flow
[M] → medium, cleanup necesario
[L] → low, buena práctica

---

## VERIFICACIÓN POST-REFACTOR

Por cada paso ejecutar:
```powershell
php -l "divi-agentic-core/<archivo-modificado>.php"
```

Al final:
```powershell
# Syntax check de todos los archivos tocados
Get-ChildItem divi-agentic-core -Recurse -Filter *.php | ForEach-Object { php -l $_.FullName }
```

Verificar que brand-sync.php corre sin errores:
```powershell
.\wp eval-file divi-agentic-core/bin/brand-sync.php
```

---

## ✅ COMPLETADO — 2026-07-22

### Resumen de cambios

| Archivo | Cambio |
|---------|--------|
| `class-token-registry.php` | +`get_customizer_slots()`, +`get_gcid_slugs_to_skip()`, +`get_inverse_customizer_slots()`, +`get_post_sync_handlers()`, +`get_derived_keys()`. Eliminados dead methods: `get_customizer_slot_keys()`, `is_secondary_key()`, `resolve_secondary_key()`. Agregado token `_secondary_accent` con type `derived`. Agregado `post_sync` a `logo_id`, `favicon_id`, `apple_icon_id`. `get_color_keys()` excluye derived. `get_validation_schema()` skipea type `derived`. |
| `brand-sync.php` | Eliminados `const CUSTOMIZER_SLOTS` y `get_prefixed_values()` (dead). Logo/favicon/apple inline refactorizados a loop genérico con `Token_Registry::get_post_sync_handlers()`. `sync_global_colors()` usa `Token_Registry::get_customizer_slots()`. |
| `class-design-resolver.php` | Slugs hardcodeados (`primary-color`, etc.) → `Token_Registry::get_gcid_slugs_to_skip()`. `flatten_from_global_variables()` con fallback a `Token_Registry::get_gvid_groups()` + `get_defaults()` cuando gvids no existen. |
| `class-customizer-engine.php` | `@deprecated` en `apply_design_file()` y `apply_design()`. Ya consumía Token_Registry desde refactor previo. |
| `class-blocks-to-schema.php` | `$customizer_slots` hardcodeado → `Token_Registry::get_inverse_customizer_slots()`. |
| `class-agentic-command.php` | `$customizer_slots` hardcodeado → `Token_Registry::get_customizer_slots()`. |
| `class-ai-bridge.php` | Colores y defaults hardcodeados → `Token_Registry::get_defaults()`. |
| `loader.php` | `$dir` normalizado a lowercase (case-sensitivity Linux). Eliminado closure duplicado de autoload (líneas 57-71). Type hints agregados: `autoload(string $class): void`, `init(): void`. |
| `class-layout-engine-test.php` | **Eliminado** — definía `class Layout_Engine` duplicada = fatal error. |
| `deploy-to-header.php` | Path absoluto `C:\Users\Departamento WEB\...` → `__DIR__ . '/temp_header_schema.json'`. |
| `trait-module-metadata.php` | `$meta_data`, `$render_data`, `$meta_loaded` con type declarations correctas (`?array`, `bool`). |
| `class-dgpc-renderer.php` | `string $builder_version` → `?string $builder_version = null`. |

### Deuda eliminada
- **4 copias** de `customizer_slots` → 1 en Token_Registry (consumida por brand-sync, Design_Resolver, BlocksToSchema, AgenticCommand)
- **2 copias** de autoload `Divi_Agentic_Core\*` → 1 en Loader
- **2 clases** `Layout_Engine` → 1 (test eliminado)
- **Hardcodeos** en AI_Bridge → defaults desde Registry
- **Path absoluto Windows** → path relativo
- **3 dead methods** eliminados
- **Case-sensitivity** en autoloader corregida
- **Typed properties** sin null safe fixeadas
