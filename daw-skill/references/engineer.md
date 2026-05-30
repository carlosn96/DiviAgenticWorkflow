# DAW Module: Phase 4 — CLI Execution (The Engineer)

## Objetivo
Tomar la definición de página (`site/<DAW_SITE>/page-defs/<slug>.json`) del Diseñador, construir el schema completo y desplegarlo en WordPress con un solo comando PHP.

---

## Instrucciones

### Paso 0: Generar (o actualizar) el Design System

Si el design system cambió (nuevos colores, fuentes, presets), regenerarlo antes de desplegar:

```powershell
# Generar design system completo desde variables:
$env:DAW_SITE="miprojecto"
python DAW_bundle/workspace/build_design_system.py
# O con rutas explícitas:
python DAW_bundle/workspace/build_design_system.py `
  --vars DAW_bundle/site/miprojecto/brand/_design_vars.json `
  --out DAW_bundle/site/miprojecto/design-system/divitheme.json
```

Ver [`../SKILL.md`](../SKILL.md) (Dependencia del Sistema de Diseño) y [`designer.md §4.2`](designer.md) para la lista de variables.

### Paso 1: Recibir la definición del Diseñador
El Diseñador entrega un archivo en `DAW_bundle/site/<DAW_SITE>/page-defs/<slug>.json`. Este archivo define la página con secciones, filas, módulos y referencias `{{design:*}}`.

### Paso 2: Build + Deploy (un solo comando)

**Comando estándar (construye schema + despliega):**
```powershell
.\php.bat DAW_bundle/divi-agentic-core/bin/build_page.php `
  --def=DAW_bundle/site/bibliotheca/page-defs/slug-de-pagina.json `
  --deploy
```

`build_page.php` hace todo:
- Carga la definición desde `site/<DAW_SITE>/page-defs/<slug>.json`
- Carga el design system desde `site/<DAW_SITE>/design-system/divitheme.json`
- Resuelve `{{design:color:*}}` → `var(--gcid-*)`
- Expande presets inline (64 presets vía deep_merge, incluyendo hero-video, glass-card, 5 separadores SVG)
- Normaliza gradient stops
- Valida la estructura (sections → rows → columns → modules)
- Escribe el schema completo en `site/<DAW_SITE>/pages/<slug>.json`
- Ejecuta `wp agentic deploy_page` con todos los flags necesarios

**Si la página debe ser la portada:**
```powershell
.\php.bat DAW_bundle/divi-agentic-core/bin/build_page.php `
  --def=DAW_bundle/site/bibliotheca/page-defs/slug-de-pagina.json `
  --deploy --front
```

**Solo build (sin deploy, para debug):**
```powershell
.\php.bat DAW_bundle/divi-agentic-core/bin/build_page.php `
  --def=DAW_bundle/site/bibliotheca/page-defs/slug-de-pagina.json `
  --out=DAW_bundle/site/bibliotheca/pages/slug-de-pagina.json
```

**Verificación post-deploy (comprueba gcids, bloques, estructura):**
```powershell
.\php.bat DAW_bundle/divi-agentic-core/bin/build_page.php `
  --def=DAW_bundle/site/bibliotheca/page-defs/slug-de-pagina.json `
  --deploy --verify
```

**Verificación con chequeo HTTP público:**
```powershell
.\php.bat DAW_bundle/divi-agentic-core/bin/build_page.php `
  --def=DAW_bundle/site/bibliotheca/page-defs/slug-de-pagina.json `
  --deploy --verify --url="https://midominio.com/slug-de-pagina"
```

**Verificación standalone (sin rebuild):**
```powershell
.\php.bat DAW_bundle/divi-agentic-core/bin/verify_page.php `
  --slug=slug-de-pagina --url="https://midominio.com/slug-de-pagina"
```
`verify_page.php` comprueba: existencia en WP, contenido con bloques Divi, presencia de `var(--gcid-*)`, ausencia de tokens `{{design:*}}` sin resolver, y acceso HTTP público (si se da `--url`).

> [!IMPORTANT]
> `build_page.php` auto-detecta `SITE_URL` desde WordPress cuando se usa `--deploy`. También se puede forzar con `--site-url="https://midominio.com"`.

> [!NOTE]
> **page-defs/ vs pages/**: `page-defs/` es la entrada (lo que escribe el diseñador). `pages/` es un directorio de debug donde `--out` escribe el schema resuelto. El deploy no necesita `pages/` — `--deploy` construye y envía en memoria. Usa `--out` solo si quieres inspeccionar el schema expandido antes de desplegar.

### Paso 2.5 (Debug): Verificar atributos de un bloque
Cuando el Diseñador necesita confirmar la serialización exacta de un bloque, ejecutar:
```powershell
.\php.bat DAW_bundle/divi-agentic-core/bin/extract-module-meta.php <slug>
```
Ejemplo: `.\php.bat DAW_bundle/divi-agentic-core/bin/extract-module-meta.php slide` — muestra todos los atributos, tipos, settings groups y paths de render que el Layout_Engine usa para serializar.

### Paso 3: Limpiar la caché de Divi

```powershell
.\wp.bat eval "et_core_clear_wp_cache();"
```

### Paso 4: Verificar la persistencia

```powershell
# Verificar que la página existe
.\wp.bat post list --post_type=page --name="slug-de-pagina" --format=json

# Verificar meta Divi 5
.\wp.bat post meta get <ID> _et_pb_built_with_d5
.\wp.bat post meta get <ID> _et_builder_version
```

**Resultado esperado:**
- `_et_pb_built_with_d5` → `1`
- `_et_builder_version` → `5.5.0`

---

## Subcomandos `wp agentic` Disponibles

| Subcomando | Descripción |
| :--- | :--- |
| `global_colors sync` | Sincroniza colores del design system → Divi 5 Global Colors (gcid-*) |
| `global_colors status` | Verifica si los Global Colors están sincronizados |
| `global_colors list` | Lista los Global Colors registrados en Divi 5 |
| `deploy_page` | Crea o actualiza una página desde un JSON schema |
| `export_page --slug=<slug>` | Exporta una página existente de WordPress a `page-defs/<slug>.json` (roundtrip: Divi 5 blocks → schema editable) |
| `deploy_global_ecosystem` | Despliega el Header, Footer y Body global en el Theme Builder |

> [!NOTE]
> `deploy_page` detecta automáticamente si la página ya existe por su `slug` y ejecuta `wp_update_post` o `wp_insert_post` según corresponda.

### ⚠️ Flujo correcto con Global Colors

```
0. python DAW_bundle/workspace/build_design_system.py (con $env:DAW_SITE)
   └── Genera divitheme.json completo desde site/<DAW_SITE>/brand/ (ver SKILL.md o designer.md §4.2).

1. wp agentic global_colors sync --design-system="DAW_bundle/site/bibliotheca/design-system/divitheme.json"
   └── Se hace UNA VEZ al crear el design system, o cuando cambien colores en el JSON.

2. wp agentic global_colors status --design-system="DAW_bundle/site/bibliotheca/design-system/divitheme.json"
   └── Verificar estado ANTES de cada deploy de página.

3. php DAW_bundle/divi-agentic-core/bin/build_page.php --def=site/bibliotheca/page-defs/<slug>.json --deploy
   └── build_page.php carga el design system y llama a deploy_page con --design-system.
       deploy_page detecta el hash de sync. Design_Resolver emite var(--gcid-*),
       luego Layout Engine convierte a $variable() para Divi 5 VB (ver abajo).

**Error común**: Desplegar sin `global_colors sync`. En ese caso los colores se resuelven a hex hardcodeados, no a `gcid-*`, y el Visual Builder no los reconoce como colores editables del tema.

### ⚠️ Two-Layer Resolution (var(--gcid-*) → $variable())

El Design_Resolver emite `var(--gcid-accent)` en los atributos. El Layout Engine, antes de `json_encode`, ejecuta `convert_gcid_to_variable_syntax()` que recorre recursivamente `$attrs` y convierte valores standalone `var(--gcid-*)` a la sintaxis que Divi 5 VB entiende:

```
var(--gcid-accent) → $variable({"type":"color","value":{"name":"gcid-accent","settings":{}}})$
```

Esto es necesario porque:
- Las páginas se crean con `builderVersion: "5.5.0"`, que impide que el migrador `GlobalColorMigration` haga la conversión (solo corre si version < 5.0.0-alpha.17.1).
- El `$variable()` syntax se escapa correctamente dentro de `json_encode` (las `"` internas pasan a `\"`).
- El frontend resuelve `$variable()` → `var(--gcid-*)` → valor hex vía `resolve_dynamic_variable()`.

Código relevante: `DAW_bundle/divi-agentic-core/inc/core/class-layout-engine.php:845-875`.

> Si un color no se ve en el VB pero se ve en frontend, verificar que el bloque en `post_content` contenga `$variable(...)` y no `var(--gcid-*)`.

---

## Script de Despliegue Automatizado

Para despliegues repetibles, usa directamente `build_page.php --deploy`:

```powershell
.\php.bat DAW_bundle/divi-agentic-core/bin/build_page.php `
  --def=DAW_bundle/site/bibliotheca/page-defs/slug-de-pagina.json `
  --deploy
```

---

## Fase 4 (Post-Deploy): Respaldo y Producción

### Generar snapshot local
```powershell
.\php.bat DAW_bundle\workspace\automation\manage_content.php --mode=local
```

### Sanear caracteres corruptos
```powershell
.\php.bat DAW_bundle\workspace\automation\universal_clean.php
```

### Despliegue a producción (flujo local → remoto)

**Nota:** El pipeline de deploy remoto está pendiente de revalidación. Ver `AGENTS.md` §3.2 (raíz del proyecto) para el estado actual de la conexión remota.

**Página ya existente en producción:**
```powershell
.\php.bat DAW_bundle\workspace\automation\push_to_remote.php --slug=slug-de-pagina --dir=local
```

**Página nueva en producción:**
```powershell
.\php.bat DAW_bundle\workspace\automation\create_page_remote.php --slug=slug-de-pagina --title="Título"
```

> El comando `mysql_remote.bat` no está disponible como herramienta válida hasta que se confirme el servidor remoto y la conexión sea revalidada.

---

## Troubleshooting

| Síntoma | Causa | Solución |
| :--- | :--- | :--- |
| `Schema validation error: Block 'X' not allowed` | Block name usa nomenclatura `et_pb_*` | Cambiar a `divi/text`, `divi/code`, etc. |
| `Schema validation error: Design class 'X' not found` | Clase `sp5-*` no registrada | Revisar `class-agentic-command.php` → `$design_classes` |
| `JSON Decode Error` | Acentos raw en el JSON | Usar entidades HTML (`&aacute;`, `&ntilde;`) |
| `Error: WP-CLI deployment failed` | Falla en `build_page.php --deploy` | Ejecutar sin `--deploy` para ver errores de build, o agregar `--out=debug.json` para inspeccionar el schema generado |
| Página no renderiza estilos | Caché de Divi no limpiada | Ejecutar `.\wp.bat eval "et_core_clear_wp_cache();"` |
| Color no se ve en VB (sí en frontend) | Bloque usa `var(--gcid-*)` en lugar de `$variable()` | Verificar `post_content` — debe contener `$variable({\"type\":\"color\",...})$`. Si no, re-desplegar con Layout Engine actualizado (clase 845-875). |
| Gradiente no se ve en VB | Color sólido y gradiente ambos presentes en la misma sección | Usar solo gradiente (sin `color` key) o poner `overlaysImage:"on"` en el gradiente. |
