# Scripts de inspección de módulos y schemas

## check-example.php
Mantiene `site/example` sincronizado con `Token_Registry` y con la estructura de carpetas documentada. Es el mecanismo de mantenimiento de la plantilla de marcas nuevas. También valida sitios productivos contra el mismo contrato.

```powershell
php divi-agentic-core/bin/check-example.php                     # verificar site/example (exit 0 = OK, 1 = desincronizado)
php divi-agentic-core/bin/check-example.php --fix               # regenerar vars + estructura de site/example
php divi-agentic-core/bin/check-example.php --active            # validar el site activo (DAW_SITE de .env)
php divi-agentic-core/bin/check-example.php --site=<slug>       # validar un site productivo puntual
php divi-agentic-core/bin/check-example.php <slug>              # forma corta de --site=
php divi-agentic-core/bin/check-example.php --all               # site/example + site activo
```

Verifica: (1) keys de `site/<slug>/brand/_design_vars.json` == schema de `Token_Registry` (+ `customizer_*`), (2) para `example`, dirs esperados presentes y obsoletos ausentes. Correr tras tocar `Token_Registry` o la estructura de `site/`. Cuando un site productivo diverge, corregir su `_design_vars.json` y re-sincronizar con `wp brand sync`.

---

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

Fuente de verdad única para la estructura de módulos. El Layout Engine usa estos schemas vía `Module_Metadata` (ver `divi-agentic-core/inc/core/trait-module-metadata.php`).

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
