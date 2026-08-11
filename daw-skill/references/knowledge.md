# DAW — Ground Truth (Estándares Técnicos)

Este archivo contiene las reglas técnicas inmutables del proyecto.

---

## Directorios Clave

| Path | Propósito |
|------|-----------|
| `site/<DAW_SITE>/page-defs/` | Page-defs de entrada (manifiesto + secciones) |
| `site/<DAW_SITE>/design-system/` | `divitheme.json` generado |
| `site/<DAW_SITE>/brand/` | `_design_vars.json` (único input de marca) |
| `divi-agentic-core/` | Plugin WordPress (junction link) |
| `wp brand sync` | Sincroniza `_design_vars.json` → `et_divi` |

---

## Flujo de Brand (Actual)

- **`wp brand sync`** lee `_design_vars.json` y sincroniza **todo**:
  - `wp_options['et_divi']` (Customizer global)
  - `design-system/divitheme.json` (tokens para Design_Resolver)
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

---

## Referencias

- `AGENTS.md` (raíz proyecto) — reglas de operación
- `AGENTS.md` (DAW) — pipeline DAW completo
- `daw-skill/SKILL.md` — 4 fases
