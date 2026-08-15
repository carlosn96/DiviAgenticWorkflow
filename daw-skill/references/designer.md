# DAW Module: Phase 3 — Visual Mapping (The Designer)

## Objetivo
Traducir el Plan Semántico + Dirección Visual en definiciones de página JSON compatibles con `deploy_page`.

---

## 0. Principio Fundamental

**Toda propiedad visual se expresa con atributos nativos de Divi 5** (`decoration`, `headingFont`, `bodyFont`, `border`, `animation`) y referencias `{{design:*}}`, **no** con CSS por clases. Las clases se usan únicamente para **scoping del CSS freeForm** y deben declararse **iguales en los 3 campos** (regla #1 de AGENTS.md §4.3):

```json
"module_class": "daw-hero",                          // raíz del section
"advanced": {
  "css": { "className": "daw-hero" },
  "htmlAttributes": { "desktop": { "value": { "class": "daw-hero", "id": "hero" } } }
}
```

`advanced.css.className` + `advanced.htmlAttributes.desktop.value.class` + `module_class` — los 3 iguales. Lo mismo con `module_id` y `advanced.htmlAttributes.desktop.value.id`.

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

> ⚠️ **Presets**: `site/<DAW_SITE>/design-system/divitheme.json` hoy contiene **presets vacíos** (`"presets": []`). No asumir que los presets de abajo existen — verificar siempre contra el archivo. El sitio real construye con **decoration nativa + `{{design:color:*}}`**, no con presets.

| Elemento visual | Bloque | Cómo |
|-----------------|--------|------|
| Hero tipográfico | `divi/section` | decoration.background oscuro + `divi/heading` grande |
| Eyebrow | `divi/text` | headingFont/bodyFont con uppercase + letterSpacing |
| Titular H1 | `divi/heading` | headingFont.h1 con `{{design:font:*}}` y `{{design:color:*}}` |
| Párrafo lead | `divi/text` | bodyFont.body con tamaño mayor y lineHeight amplio |
| Feature card | `divi/blurb` | decoration (bg, radius, padding) + hover |
| Botón primario | `divi/button` | decoration.button.desktop.value.backgroundColor + textColor |
| Botón ghost | `divi/button` | border en vez de background |
| Separador | `divi/divider` | decoration nativa |

---

## 3. Formato de Definición de Página (Actual)

### Estructura: Carpeta por página + Manifiesto + Secciones

```
page-defs/<slug>/
├── manifest.json         ← lista de secciones en orden
├── sections/             ← un JSON por sección
│   ├── 01-hero.json
│   └── 02-features.json
├── css/                  ← CSS freeForm por sección (opcional)
│   ├── 01-hero.css
│   └── 02-features.css
└── <slug>-combined.json  ← output de combine.py (NO editar)
```

#### 3.1. Manifiesto (`page-defs/<slug>/manifest.json`)

```json
{
  "_manifest": "v1",
  "title": "Mi Página",
  "slug": "mi-pagina",
  "description": "Opcional",
  "sections": [
    "sections/01-hero.json",
    "sections/02-features.json"
  ]
}
```

Las secciones se referencian con paths **relativos al directorio de la página** (donde está `manifest.json`).

#### 3.2. Sección (`page-defs/<slug>/sections/01-hero.json`)

Formato real del pipeline (ver `site/<DAW_SITE>/page-defs/inicio/sections/01-hero.json` como ejemplo vivo):

```json
{
  "module_class": "daw-hero",
  "module_id": "hero",
  "decoration": {
    "background": {
      "desktop": {
        "value": {
          "color": "{{design:color:surface-deep}}",
          "image": { "url": "{{SITE_URL}}/wp-content/uploads/2026/07/hero-bg.webp", "size": "cover", "position": "center center", "repeat": "no-repeat" }
        }
      }
    },
    "spacing": {
      "desktop": { "value": { "padding": { "top": "160px", "right": "96px", "bottom": "80px", "left": "96px" } } }
    }
  },
  "advanced": {
    "css": { "className": "daw-hero" },
    "htmlAttributes": { "desktop": { "value": { "class": "daw-hero", "id": "hero" } } }
  },
  "css": "",
  "rows": [
    {
      "column_structure": "1_1",
      "columns": [
        {
          "type": "1_1",
          "decoration": {
            "sizing": {
              "desktop": { "value": { "flexType": "24_24" } },
              "tablet":  { "value": { "flexType": "24_24" } },
              "phone":   { "value": { "flexType": "24_24" } }
            }
          },
          "advanced": {
            "type": {
              "desktop": { "value": "1_1" },
              "tablet":  { "value": "1_1" },
              "phone":   { "value": "vertical" }
            }
          },
          "modules": [
            {
              "type": "divi/heading",
              "module_class": "daw-hero-title",
              "content": "<h1>Venga Tu Reino</h1>",
              "headingFont": {
                "h1": {
                  "font": {
                    "desktop": { "value": { "fontFamily": "Onest", "size": "2.5rem", "color": "{{design:color:text_on_dark}}" } },
                    "tablet":  { "value": { "size": "2.25rem" } },
                    "phone":   { "value": { "size": "2rem" } }
                  }
                }
              }
            }
          ]
        }
      ]
    }
  ],
  "_section": true
}
```

**Reglas del schema (AGENTS.md §4.3):**
1. Clase: `advanced.css.className` + `advanced.htmlAttributes.desktop.value.class` + `module_class` — **los 3 iguales**. ID: `advanced.htmlAttributes.desktop.value.id` + `module_id`.
2. Responsive: `decoration.spacing`/`sizing` con los 3 breakpoints `{desktop:{value:{...}}}`, `{tablet:...}`, `{phone:...}`. El phone de column usa `"vertical"`.
3. Columnas: `column_structure` en row (ej. `"1_2,1_2"`) + `type` + `flexType` (`24_24` = 1/1, `12_24` = 1/2, `8_24` = 1/3…) en column.
4. Tipografía: `headingFont`/`bodyFont` con `fontFamily`, `size`, `weight`, `color`. NO CSS manual.
5. Contenido: `content` string con HTML plano. NO markdown. Usar entidades HTML para acentos (`&aacute;`, `&ntilde;`).
6. CSS freeForm: se almacena en `css/<sección>.css` (mismo nombre que el JSON de sección) y lo inyecta `combine.py`. El campo `"css"` del JSON se deja `""`. **⚠️ NINGÚN `<` en ese CSS** (regla #15).
7. URLs de imágenes: resolver vía media library; usar `{{SITE_URL}}` como prefijo de base.

#### 3.3. Combinar y desplegar

```powershell
# Combinar manifiesto + secciones en un solo JSON
python workspace/combine.py `
  site/<DAW_SITE>/page-defs/<slug>/manifest.json `
  --out site/<DAW_SITE>/page-defs/<slug>/<slug>-combined.json

# Deploy con el wrapper (combina + deploy_page + flush)
.\workspace\deploy.ps1 -Slug <slug> -Title "Título"

# (alternativa directa) Layout Engine refactorizado
.\wp.bat agentic deploy_page `
  --title="Título" --slug="<slug>" `
  --schema="site/<DAW_SITE>/page-defs/<slug>/<slug>-combined.json" `
  --design-system="site/<DAW_SITE>/design-system/divitheme.json"
```

---

## 4. Column Structures Válidas

`column_structure` en el row define el reparto; cada columna declara `type` (igual al suyo) y `flexType` (`N_24`).

| `column_structure` | Layout | `type` por columna | `flexType` |
|--------------------|--------|--------------------|------------|
| `1_1` | Full width | `1_1` | `24_24` |
| `1_2,1_2` | Dos mitades | `1_2` | `12_24` |
| `1_3,1_3,1_3` | Tres iguales | `1_3` | `8_24` |
| `2_3,1_3` | 2/3 + 1/3 | `2_3`, `1_3` | `16_24`, `8_24` |
| `1_4,1_4,1_4,1_4` | Cuatro columnas | `1_4` | `6_24` |
| `1_2,1_2,1_2,1_2` | Cuatro mitades (grid) | `1_2` | `12_24` |

- El phone de cada columna: `advanced.type.phone.value = "vertical"` (se apilan).
- `flexColumnStructure` (bloques) equivale a `column_structure` (schema) — el Layout Engine los traduce.

---

## 5. Design Tokens (`{{design:*}}`)

Los nombres de token se derivan de `site/<DAW_SITE>/brand/_design_vars.json` (keys en snake_case → kebab-case en el schema). `divitheme.json` hoy **solo tiene presets + strategy** (`"presets": []`); los valores reales viven en los stores nativos de Divi (gcids/gvids), a los que el `Design_Resolver` accede en deploy.

| Uso | Referencia en schema | Resolución |
|-----|----------------------|------------|
| Colores | `{{design:color:surface-deep}}` (de `color_surface_deep`) | `var(--gcid-*)` |
| Tipografía | `{{design:font:display}}` (de `font_display`) | store de fuentes |
| Espacios | `{{design:space:2xl}}` (de `space_2xl`) | gvid |
| Radios | `{{design:radius:lg}}` (de `radius_lg`) | gvid |

**Two-Layer Resolution:**
1. `deploy_page` / `Design_Resolver`: `{{design:color:*}}` → `var(--gcid-*)`
2. Layout Engine: `var(--gcid-*)` → `$variable({"type":"color","value":{"name":"gcid-*","settings":{}}})$` (sintaxis que el VB entiende)

Si no hay gcids sincronizados, `deploy_page` emite warning y resuelve a hex. Correr `wp brand sync` para que existan.

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

## 7. Brand Sync

El brand se define en `_design_vars.json` y se sincroniza a Divi Customizer:

```powershell
.\wp brand sync <DAW_SITE>
```

Esto escribe 38+ opciones de color + fuentes a `wp_options['et_divi']`. Divi genera CSS automáticamente. No se genera `brand.css` ni se ejecuta `build_design_system.py`.

---

## 8. Gotchas de Autoría (render-verificados)

Trampas que se cometen al escribir secciones y **que el render confirma**. Adaptadas del divi5-skill (render-verified en Divi 5.10) al schema DAW:

### 8.1. Botones: `enable` gate y dónde va el padding

En el schema DAW el renderer mapea `module.decoration.button` → `button.decoration` y **ya normaliza** el padding (lo mueve a `button.decoration.spacing`). Lo que NO se debe hacer:

- ❌ Escribir el padding del botón fuera de `decoration.button` con la idea de que no aplica: el renderer sí lo lee desde `decoration.button.desktop.value.padding` y lo coloca en `button.decoration.spacing`.
- ❌ Depender de `enable` para que los estilos de botón se apliquen: el renderer setea `enable` él mismo (no hace falta ponerlo a mano).
- ✅ Para que un botón se vea como tal, declarar SIEMPRE el hover (ver §6 y Ley 4): `decoration.button.hover.value.*` o `decoration.transform.hover`.

### 8.2. Overlays / badges: NO usar `position`

El grupo `position` (absolute/offset) **no emite CSS fiable** en el path MCP — mejor no construir overlays con él. El patrón verificado es **flow-over-background**:

1. Un grupo (o columna) con la **imagen como background** (`decoration.background.image`).
2. El chip/badge como **texto en flow** dentro de ese grupo (sin posicionar).
3. `alignItems: flex-start` en el grupo para que el chip se ajuste a su contenido.

Aplica a: chips de card, badges "NUEVO", etiquetas sobre fotos, cards overlay en About/Footer. Trade-off: la imagen de fondo no emite `<img>`/alt (flaguear si el SEO de imágenes importa). El position nativo en el renderer DAW sí existe (`class-divi-base-renderer.php` lo mapea), pero es menos robusto que flow-over-background.

### 8.3. Rows multi-columna NO se apilan solas

Divi 5 **no auto-stackea** rows multi-columna en móvil. Hay que declarar el apilado explícitamente en tablet (la cascada aplica hacia abajo):

```json
"decoration": {
  "layout": {
    "desktop": { "value": { "display": "flex", "flexDirection": "row", "columnGap": "22px" } },
    "tablet":  { "value": { "flexDirection": "column", "rowGap": "22px" } }
  }
}
```

Al apilar, **neutralizar** los efectos desktop-only en la misma banda (tablet): hairlines verticales → `border.tablet...left.width: "0px"`, paddings grandes → reducir, y `disabledOn` para decorations solo-desktop.

### 8.4. Tipografía dominante sin presets

Los presets (`text:display-xl`, `hero-title`, etc.) **no existen** en este design system (`"presets": []`). El titular dominante se hace con `headingFont.h1` (o `bodyFont`) nativo: tamaño desktop ≥ 2rem (72px ideal), escala responsive explícita:

```json
"headingFont": { "h1": { "font": {
  "desktop": { "value": { "fontFamily": "Onest", "size": "2.5rem", "fontWeight": "500", "lineHeight": "1.2", "color": "{{design:color:text_on_dark}}" } },
  "tablet":  { "value": { "size": "2.25rem" } },
  "phone":   { "value": { "size": "2rem" } }
} } }
```

### 8.5. Contenido: HTML plano con entidades, no markdown

`content` es un string HTML plano (renderer lo serializa): `<p>…</p>`, `<h1>…</h1>`. Usar entidades para acentos (`&aacute;`, `&ntilde;`). NO markdown, NO `<style>` inline (se pierde al guardar en VB).

### 8.6. Gradientes: stops sin `%`

Los `stops` usan `position` numérico sin `%` (`"0"`, `"50"`, `"100"`) — el normalizador recorta el `%` y `"0%" + "%"` = `"0%%"` rompe el CSS. El lint lo valida.

---

## 9. Doctrina Responsive Multi-Breakpoint

Reglas que aplican a TODA sección/página multi-columna (también header/footer de Theme Builder):

1. **Cascada**: los valores de desktop caen hacia abajo; `tablet` cubre tablet + phoneWide + phone salvo override.
2. **Rows nunca auto-stackean**: declarar `layout.tablet.value.flexDirection: "column"` en CADA row multi-columna (§8.3). El lint lo avisa (WARN).
3. **Columnas**: `flexType` `24_24`/`12_24`/`8_24`… por banda; el phone de column usa `"vertical"`.
4. **Neutralizar desktop-only al apilar**: hairlines verticales → `width: 0`; paddings XL → reducir; `disabledOn` en decorations solo-desktop.
5. **Tipografía por banda**: escala tipo `h1 78/54/38` (desktop/tablet/phone). Nunca un solo tamaño.
6. **Grids** (si se usan): `gridColumnCount` responsive (3 → 2 → 1), el grid NO auto-stackea.

> El lint (`lint_page_def.php`) avisa cuando una row multi-columna no declara apilado en tablet (WARN), cuando secciones adyacentes comparten fondo (WARN, puede ser intencional) y cuando falta ancla visual grande (WARN).

---

## 10. Verificación

Antes de entregar a Fase 4:
- [ ] Ningún `et_pb_*` en el JSON
- [ ] Ningún hex hardcodeado — todo `{{design:color:*}}`
- [ ] Ningún preset inexistente (verificar contra `divitheme.json`)
- [ ] Ningún `border.all.width` como objeto
- [ ] Ningún `background.color` en botones (usar `backgroundColor`)
- [ ] Posiciones de gradient sin `%`
- [ ] Las 6 leyes del Design Brief reflejadas
- [ ] Clases consistentes: `module_class` == `advanced.css.className` == `htmlAttributes.class`; `module_id` == `htmlAttributes.id`
- [ ] CSS freeForm en `css/<sección>.css` y **sin `<`** en ninguna parte
- [ ] Rows multi-columna con apilado en tablet (`layout.tablet.value.flexDirection: "column"`)
- [ ] Hover declarado en todos los `divi/button` (Ley 4)
- [ ] Titular dominante nativo: `headingFont.h1` con size desktop ≥ 2rem (Ley 2)
- [ ] Pasa `php divi-agentic-core/bin/lint_page_def.php --def=<slug>-combined.json`

---

## 11. Referencias

- [`references/blocks-dictionary.md`](references/blocks-dictionary.md) — 102 módulos Divi 5
- `site/<DAW_SITE>/brand/_design_vars.json` — fuente de tokens (nombres → `{{design:*}}`)
- `site/<DAW_SITE>/design-system/divitheme.json` — presets + strategy (los tokens se leen de stores nativos)
- [`../SKILL.md`](../SKILL.md) — 4 fases completas
- `test/divi5-skill/DIVI5-RECIPES.md` — biblioteca de componentes render-verificados (referencia externa)
