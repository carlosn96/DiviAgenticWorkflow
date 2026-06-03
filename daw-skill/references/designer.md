# DAW Module: Phase 3 — Visual Mapping (The Designer)

## Objetivo
Traducir el Plan Semántico + Dirección Visual en definiciones de página JSON compatibles con `build_page.php`.

---

## 0. Principio Fundamental

**NO usar `module_class` con clases CSS.** Toda propiedad visual se expresa como atributos nativos de Divi 5 (`decoration`, `headingFont`, `bodyFont`, `border`, `animation`) y referencias `{{design:*}}`.

---

## 1. Reglas de Oro del Schema

- **NUNCA** usar `et_pb_*` — namespace `divi/*` únicamente.
- **NUNCA** hardcodear hex colors ni valores en px. Usar `{{design:token}}`.
- **NUNCA** usar `module_class` con clases CSS. Usar decoration attributes nativos.
- **SIEMPRE** usar `divitheme.json` como única fuente de tokens y presets.
- **SIEMPRE** usar `{{design:color:name}}` para colores.
- **SIEMPRE** usar entidades HTML para acentos (`&aacute;`, `&ntilde;`) en contenidos.

---

## 2. Bloques Divi 5 Disponibles

> **Guía de decisión:** [`references/blocks-dictionary.md`](references/blocks-dictionary.md)
> **Índice:** [`references/blocks-index.json`](references/blocks-index.json) (102 bloques)

### Tabla rápida

| Elemento visual | Bloque | Preset |
|-----------------|--------|--------|
| Hero tipográfico | `divi/section` | `section:hero-dark` |
| Sección clara | `divi/section` | `section:light` |
| Sección oscura | `divi/section` | `section:dark` |
| Eyebrow | `divi/text` | `text:eyebrow` |
| Titular H1 | `divi/heading` | `text:display-xl` |
| Párrafo lead | `divi/text` | `text:lead` |
| Feature card | `divi/blurb` | `module:feature-card` |
| Glass card | `divi/text` o `divi/blurb` | `module:glass-card` |
| Botón primario | `divi/button` | `module:btn-primary` |
| Botón ghost | `divi/button` | `module:btn-ghost` |
| Separador SVG | `divi/section` | `divider:curve-*` |

---

## 3. Formato de Definición de Página (Actual)

### Estructura: Manifiesto + Secciones

El page-def se divide en dos niveles:

#### 3.1. Manifiesto (`page-defs/<slug>.json`)

```json
{
  "_manifest": "v1",
  "title": "Mi Página",
  "slug": "mi-pagina",
  "description": "Opcional",
  "sections": [
    "sections/hero.json",
    "sections/features.json"
  ]
}
```

Las secciones se referencian como paths relativos al directorio `page-defs/`.

#### 3.2. Sección (`page-defs/sections/<slug>.json`)

```json
{
  "_section": true,
  "module": {
    "advanced": {
      "css": {
        "className": "daw-hero-section"
      }
    }
  },
  "decoration": {
    "background": {
      "desktop": {
        "value": {
          "color": "{{design:color:surface-white}}"
        }
      }
    },
    "spacing": {
      "desktop": {
        "value": {
          "padding": { "top": "160px", "bottom": "80px", "right": "96px", "left": "96px" }
        }
      }
    }
  },
  "rows": [
    {
      "column_structure": "4_4",
      "modules": [
        {
          "type": "divi/text",
          "presets": ["text:eyebrow"],
          "content": "<p>Subt&iacute;tulo</p>"
        }
      ]
    },
    {
      "column_structure": "2_3,1_3",
      "columns": [
        {
          "type": "2_3",
          "modules": [
            { "type": "divi/button", "presets": ["module:btn-primary"],
              "button_text": "Acci&oacute;n", "button_url": "/ruta" }
          ]
        },
        {
          "type": "1_3",
          "modules": [
            { "type": "divi/image",
              "src": "{{SITE_URL}}/wp-content/uploads/imagen.jpg" }
          ]
        }
      ]
    }
  ]
}
```

#### 3.3. Combinar y desplegar

```powershell
# Combinar manifiesto + secciones en un solo JSON
python DAW_bundle/site/<DAW_SITE>/page-defs/combine.py `
  DAW_bundle/site/<DAW_SITE>/page-defs/<slug>.json `
  --out DAW_bundle/site/<DAW_SITE>/page-defs/<slug>-combined.json

# Build + Deploy (--def es relativo a page-defs/)
.\php.bat DAW_bundle/divi-agentic-core/bin/build_page.php `
  --def="<slug>-combined.json" --deploy
```

---

## 4. Column Structures Válidas

| Valor | Layout | Types |
|-------|--------|-------|
| `4_4` | Full width | `4_4` |
| `1_2,1_2` | Dos mitades | `1_2` |
| `1_3,1_3,1_3` | Tres iguales | `1_3` |
| `2_3,1_3` | 2/3 + 1/3 | `2_3`, `1_3` |
| `1_4,1_4,1_4,1_4` | Cuatro columnas | `1_4` |

---

## 5. Design Tokens (`{{design:*}}`)

Consultar `site/<DAW_SITE>/design-system/divitheme.json` para tokens disponibles.

| Uso | Sin Global Colors | Con Global Colors |
|-----|-------------------|-------------------|
| `{{design:color:ink}}` | `#1A1814` (hex) | `$variable({...})$` → editable en VB |
| `{{design:color:accent}}` | `#A67C40` (hex) | `$variable({...})$` → editable en VB |

**Two-Layer Resolution:**
1. `build_page.php`: `{{design:color:*}}` → `var(--gcid-*)`
2. Layout Engine: `var(--gcid-*)` → `$variable({"type":"color","value":{"name":"gcid-*","settings":{}}})$`

---

## 6. Reglas para decoration.button

Cuando definas estilos de botón en `decoration.button.desktop.value`:

```json
"decoration": {
  "button": {
    "desktop": {
      "value": {
        "backgroundColor": "#E76F51",
        "color": "#FFFFFF",
        "border": {
          "all": {
            "radius": {
              "topLeft": "9999px",
              "topRight": "9999px",
              "bottomRight": "9999px",
              "bottomLeft": "9999px",
              "sync": "on"
            },
            "style": "solid",
            "width": "1px",
            "color": "rgba(42,157,143,0.2)"
          }
        }
      }
    }
  }
}
```

**⚠️ Reglas:**
- `backgroundColor` — usar string plano, NO `background: {color: ...}`
- `border.all.width` — usar string simple `"1px"`, NO objeto `{top, right, bottom, left}`
- `border.all.radius` — usar objeto per-side `{topLeft, topRight, ...}`
- `boxShadow`, `transform` — ponerlos en `module.decoration.*` (raíz), no dentro de `button.*`

---

## 7. Sistema de Diseño

El script `build_design_system.py` genera:

```
site/<DAW_SITE>/design-system/divitheme.json  (58 presets)
site/<DAW_SITE>/brand/assets/css/brand.css     (clases daw-*, único por marca)
```

Ejecutar:

```powershell
python DAW_bundle/workspace/build_design_system.py
```

Esto auto-descubre tokens por prefijo (`color_`, `font_`, `radius_`, `space_`) y genera presets completos.

---

## 8. Verificación

Antes de entregar a Fase 4:
- [ ] Ningún `et_pb_*` en el JSON
- [ ] Ningún hex hardcodeado — todo `{{design:color:*}}`
- [ ] Ningún preset inexistente
- [ ] Ningún `border.all.width` como objeto
- [ ] Ningún `background.color` en botones (usar `backgroundColor`)
- [ ] Posiciones de gradient sin `%`
- [ ] Las 6 leyes del Design Brief reflejadas

---

## 9. Referencias

- [`references/blocks-dictionary.md`](references/blocks-dictionary.md) — 102 módulos Divi 5
- `site/<DAW_SITE>/design-system/divitheme.json` — tokens + presets
- [`../SKILL.md`](../SKILL.md) — 4 fases completas
