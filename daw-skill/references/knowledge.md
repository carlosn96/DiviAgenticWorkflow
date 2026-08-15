# DAW — Ground Truth (Estándares Técnicos)

Este archivo contiene las reglas técnicas inmutables del proyecto.

**Versión objetivo:** Divi **5.10.1** (tema activo).

---

## Directorios Clave

| Path | Propósito |
|------|-----------|
| `site/<DAW_SITE>/page-defs/` | Page-defs de entrada (carpeta por página: `manifest.json` + `sections/` + `css/`) |
| `site/<DAW_SITE>/design-system/` | `divitheme.json` — **solo presets + strategy** (los tokens viven en stores nativos de Divi) |
| `site/<DAW_SITE>/brand/` | `_design_vars.json` (único input de marca) + `.design-pass` (aprobación) |
| `divi-agentic-core/` | Plugin WordPress (Layout Engine, CLI, bin/ de inspección) |
| `divi-agentic-core/bin/AGENTS.md` | Referencia de scripts: check-example, lint_page_def, verify_page, inspect-*, generate-module-schema… |
| `workspace/` | Scripts transversales: `combine.py`, `deploy.ps1`, `deploy-template.ps1` |
| `wp brand sync` | Sincroniza `_design_vars.json` → `et_divi` |

---

## Flujo de Brand (Actual)

- **`wp brand sync`** lee `_design_vars.json` y sincroniza **todo** (respeta quality gate; `--force` lo bypasea):
  - `wp_options['et_divi']` (Customizer global)
  - `design-system/divitheme.json` (**solo presets + strategy**)
  - gcids via `GlobalData::set_global_colors()` (colores vivos)
  - gvids via `GlobalData::set_global_variables()` (radios, espacios, fuentes como variables nativas Divi 5)
- Divi genera CSS automáticamente desde sus opciones de Customizer

---

## Reglas Técnicas

- No añadir CSS a `style.css` del tema
- No inyectar CSS en `functions.php`
- Usar decoration nativa de Divi 5 (`spacing`, `background`, `border`, `boxShadow`, etc.)
- Colores siempre como `{{design:color:*}}`
- Fonts siempre como `{{design:font:*}}`
- Border radius como objeto per-side (`{topLeft, topRight, bottomRight, bottomLeft, sync}`)
- Border width como string plano (`"1px"`), no objeto
- `backgroundColor` como string plano, no `background: {color: ...}`
- Usar entidades HTML para caracteres especiales en contenidos
- **Deploy solo vía wrappers** (`.\workspace\deploy.ps1` / `deploy-template.ps1`) — regla #5
- **CSS freeForm:** guardar en `css/<sección>.css`; el campo `"css"` del JSON va vacío. ⚠️ **Ningún `<` en ninguna parte** (regla #15 — `wp_strip_all_tags` trunca)
- **Clases:** `module_class` == `advanced.css.className` == `htmlAttributes.class`; `module_id` == `htmlAttributes.id`
- **Page-def:** carpeta por página (`page-defs/<slug>/manifest.json` + `sections/` + `css/`); secciones con `"_section": true`

---

## Referencias

- `AGENTS.md` (raíz proyecto) — reglas de operación
- `AGENTS.md` (DAW) — pipeline DAW completo
- `daw-skill/SKILL.md` — 4 fases
