# DAW Module: Phase 4 — CLI Execution (The Engineer)

## Objetivo
Persistir el JSON Schema en la base de datos de WordPress y verificar que la página queda correctamente construida con Divi 5 nativo.

---

## Instrucciones

### Paso 1: Guardar el Schema
El archivo JSON debe estar en `workspace/pages/<slug>.json` dentro de la raíz del proyecto, relativo al directorio desde donde se ejecutan los comandos.

### Paso 2: Desplegar con el wrapper local

**Comando estándar (crear o actualizar página):**
```powershell
.\wp.bat agentic deploy_page --title="Título de la Página" --slug="slug-de-pagina" --schema="workspace/pages/slug-de-pagina.json"
```

**Si la página debe ser la portada (home):**
```powershell
.\wp.bat agentic deploy_page --title="Inicio" --slug="inicio" --schema="workspace/pages/inicio.json" --front
```

**Para Header/Footer globales (Theme Builder):**
```powershell
.\wp.bat agentic deploy_global_ecosystem --header="workspace/pages/navbar-global.json" --footer="workspace/pages/footer-global.json" --body="workspace/pages/body-global.json"
```

> [!IMPORTANT]
> Usar SIEMPRE `.\wp.bat` (wrapper local). El binario global `wp` NO está disponible en este entorno de Local WP.

### Paso 2.5 (Debug): Verificar atributos de un bloque
Cuando el Diseñador necesita confirmar la serialización exacta de un bloque, ejecutar:
```powershell
.\php.bat divi-agentic-core\bin\extract-module-meta.php <slug>
```
Ejemplo: `.\php.bat divi-agentic-core\bin\extract-module-meta.php slide` — muestra todos los atributos, tipos, settings groups y paths de render que el Layout_Engine usa para serializar.

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
| `deploy_page` | Crea o actualiza una página desde un JSON schema |
| `deploy_global_ecosystem` | Despliega el Header, Footer y Body global en el Theme Builder |

> [!NOTE]
> `deploy_page` detecta automáticamente si la página ya existe por su `slug` y ejecuta `wp_update_post` o `wp_insert_post` según corresponda.

---

## Script de Despliegue Automatizado

Para despliegues repetibles, usa el script interno del skill:

```powershell
powershell -File ".agents\skills\daw-skill\scripts\deploy_page.ps1" `
  -Title "Título de la Página" `
  -Slug "slug-de-pagina" `
  -SchemaPath "workspace/pages/slug-de-pagina.json" `
  -ClearCache
```

---

## Fase 4 (Post-Deploy): Respaldo y Producción

### Generar snapshot local
```powershell
.\php.bat workspace\automation\manage_content.php --mode=local
```

### Sanear caracteres corruptos
```powershell
.\php.bat workspace\automation\universal_clean.php
```

### Despliegue a producción (Hex-Safe)

**Página ya existente en producción:**
```powershell
.\php.bat workspace\automation\push_to_remote.php --slug=slug-de-pagina --dir=local
Get-Content push_payload.sql | .\mysql_remote.bat
```

**Página nueva en producción:**
```powershell
.\php.bat workspace\automation\create_page_remote.php --slug=slug-de-pagina --title="Título"
Get-Content create_slug-de-pagina_remote.sql | .\mysql_remote.bat
```

---

## Troubleshooting

| Síntoma | Causa | Solución |
| :--- | :--- | :--- |
| `Schema validation error: Block 'X' not allowed` | Block name usa nomenclatura `et_pb_*` | Cambiar a `divi/text`, `divi/code`, etc. |
| `Schema validation error: Design class 'X' not found` | Clase `sp5-*` no registrada | Revisar `class-agentic-command.php` → `$design_classes` |
| `JSON Decode Error` | Acentos raw en el JSON | Usar entidades HTML (`&aacute;`, `&ntilde;`) |
| `Error: WP-CLI deployment failed` | Falla en el script `.ps1` | Ejecutar `.\wp.bat agentic deploy_page ...` directamente para ver el error |
| Página no renderiza estilos | Caché de Divi no limpiada | Ejecutar `.\wp.bat eval "et_core_clear_wp_cache();"` |
