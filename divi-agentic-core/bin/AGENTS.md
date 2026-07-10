# Scripts de inspección de módulos y schemas

## inspect-module.php
Inspecciona atributos de un módulo desde el metadata oficial de Divi 5.

```powershell
php divi-agentic-core/bin/inspect-module.php <module-key> [attr-name]
php divi-agentic-core/bin/inspect-module.php number-counter
php divi-agentic-core/bin/inspect-module.php divi/text headingFont
```

Muestra: tipo del atributo, default, settings groups, tagName, inlineEditor.

---

## extract-module-meta.php
Extrae el schema completo de un módulo (metadata + render attributes default).

```powershell
php divi-agentic-core/bin/extract-module-meta.php <module-key>
php divi-agentic-core/bin/extract-module-meta.php number-counter
php divi-agentic-core/bin/extract-module-meta.php divi/text
```

Sin argumento lista todos los módulos disponibles.

---

## generate-module-schema.php
Genera schemas JSON autoritativos desde el metadata oficial de Divi 5.

```powershell
php divi-agentic-core/bin/generate-module-schema.php <module-key>                 # stdout
php divi-agentic-core/bin/generate-module-schema.php <module-key> --out path.json  # a archivo
php divi-agentic-core/bin/generate-module-schema.php --all --out dir/              # todos los módulos
php divi-agentic-core/bin/generate-module-schema.php --list                        # listar keys
```

Fuente de verdad única para la estructura de módulos. `build_page.php` lee los JSON que este script produce.

---

## inspect-metadata-group.php
Inspecciona un grupo de settings específico dentro de un atributo (innerContent, module, a, b, etc.).

```powershell
php divi-agentic-core/bin/inspect-metadata-group.php <module> <attribute> [group]
php divi-agentic-core/bin/inspect-metadata-group.php divi/text content innerContent
php divi-agentic-core/bin/inspect-metadata-group.php divi/button button module
```

Muestra estructura completa para entender serialización.

---

## lint_page_def.php
Quality Gate para page-defs JSON. Valida 6 leyes de calidad autónoma, presets, colores hex, et_pb_*, tokens no resueltos.

```powershell
php divi-agentic-core/bin/lint_page_def.php --def=inicio-combined.json
php divi-agentic-core/bin/lint_page_def.php --def=inicio-combined.json --verbose
php divi-agentic-core/bin/lint_page_def.php --def=inicio-combined.json --presets=_design_presets.json
```

Exit code: 0 = pass, 1 = fail.

---

## verify_page.php
Verificación post-deploy. Comprueba que la página está estructuralmente sana y los GCIDs se renderizan.

```powershell
php divi-agentic-core/bin/verify_page.php --slug=inicio
php divi-agentic-core/bin/verify_page.php --slug=inicio --url="http://lopezvelarde.local/inicio/"
php divi-agentic-core/bin/verify_page.php --slug=inicio --schema=page-defs/inicio.json
```

Exit code: 0 = pass, 1 = fail.

---

## validate_block_structure.php
Valida la estructura de bloques de un post de Divi 5 (cuenta bloques top-level, innerBlocks, fragmentos sin parsear).

```powershell
php divi-agentic-core/bin/validate_block_structure.php <post_id>
```

Útil para depurar contenido corrupto o mal generado.

---

## list_renderers.php
Lista los renderers disponibles en `inc/core/renderers/`.

```powershell
php divi-agentic-core/bin/list_renderers.php
```

---

## check_frontend.php
Verifica que el frontend de una página se renderiza sin errores.

```powershell
php divi-agentic-core/bin/check_frontend.php <slug>
```

---

## diff_post_content.php
Compara el post_content de dos versiones de una página (útil para ver qué cambió entre deploys).

```powershell
php divi-agentic-core/bin/diff_post_content.php <post_id_A> <post_id_B>
```
