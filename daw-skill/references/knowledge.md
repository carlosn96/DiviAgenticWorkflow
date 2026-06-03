# DAW — Ground Truth (Estándares Técnicos)

Este archivo contiene las reglas técnicas inmutables del proyecto.

---

## Directorios Clave

| Path | Propósito |
|------|-----------|
| `DAW_bundle/site/<DAW_SITE>/page-defs/` | Page-defs de entrada (manifiesto + secciones) |
| `DAW_bundle/site/<DAW_SITE>/design-system/` | `divitheme.json` generado |
| `DAW_bundle/site/<DAW_SITE>/brand/` | `_design_vars.json`, `_design_presets.json` |
| `DAW_bundle/site/<DAW_SITE>/brand/assets/css/` | `brand.css` generado (único por marca) |
| `DAW_bundle/divi-agentic-core/` | Plugin WordPress (junction link) |

---

## Flujo de CSS (Actual)

- **brand.css** se escribe a `site/<DAW_SITE>/brand/assets/css/brand.css` por `build_design_system.py`
- **No se usa** `wp_update_custom_css_post()` — el CSS se encola desde disco
- **No se usa** `et_custom_css` — fue eliminado
- **`sync_css`** solo limpia legacy, no escribe

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
- `DAW_bundle/AGENTS.md` — pipeline DAW completo
- `daw-skill/SKILL.md` — 4 fases
