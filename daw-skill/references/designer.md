# DAW Module: Phase 3 — Visual Mapping (The Designer)

## Objetivo
Traducir el **Plan Semántico del Arquitecto + Dirección Visual del Design Lead** en una **definición de página JSON** compatible con `build_page.php`, que la compilará y desplegará como bloques Divi 5.5.0 nativos.

---

## 0. Principio Fundamental

**NO usar `module_class` con clases CSS.**
Toda propiedad visual se expresa como atributos nativos de Divi 5 (`decoration`, `headingFont`, `bodyFont`, `border`, `animation`, etc.) y referencias `{{design:*}}` tokens.

**FLUJO PHP-ONLY (DAW v4.0):**
El Diseñador crea un **archivo de definición** en `DAW_bundle/site/<DAW_SITE>/page-defs/<slug>.json`. `build_page.php` lo procesa en un solo paso:

```
page-defs/<slug>.json
  → build_page.php (carga módulos + design system + resuelve tokens + expande presets)
  → site/<DAW_SITE>/pages/<slug>.json (schema compilado, solo con --out)
  → wp agentic deploy_page (Layout Engine → bloques Divi 5 nativos en WP)
```

**Un solo comando para construir y desplegar:**
```powershell
.\php.bat DAW_bundle/divi-agentic-core/bin/build_page.php `
  --def=DAW_bundle/site/bibliotheca/page-defs/<slug>.json `
  --deploy
```

---

## 1. Reglas de Oro del Schema

- **NUNCA** usar `et_pb_*` — el motor espera el namespace `divi/*` (bloques Gutenberg nativos).
- **NUNCA** hardcodear hex colors ni valores en px. Usar siempre `{{design:token}}`.
- **NUNCA** usar `module_class` con clases CSS. Usar decoration attributes nativos.
- **SIEMPRE** usar el archivo `DAW_bundle/site/<DAW_SITE>/design-system/divitheme.json` como única fuente de tokens y presets.
- **SIEMPRE** usar `{{design:color:name}}` para colores. `build_page.php` los resuelve a `var(--gcid-name)` si los Global Colors están sincronizados, o a hex como fallback.

---

## 2. Bloques Divi 5 Disponibles

> **Guía de decisión semántica:** [`references/blocks-dictionary.md`](references/blocks-dictionary.md)
> **Índice de bloques:** [`references/blocks-index.json`](references/blocks-index.json) (102 bloques: slug, nombre, categoría, children)
> **Atributos detallados (bajo demanda):** Ejecutar `php DAW_bundle/divi-agentic-core/bin/extract-module-meta.php <slug>` para ver tipos, defaults, settings groups y render paths de cualquier bloque.

### Tabla rápida de bloques por elemento visual

| Elemento visual | Bloque | Preset recomendado |
| :--- | :--- | :--- |
| Hero oscuro tipográfico | `divi/section` | `section:hero-dark` |
| Hero con imagen de fondo | `divi/section` | `section:hero-cinematic` |
| Sección clara | `divi/section` | `section:light` |
| Sección oscura alternativa | `divi/section` | `section:dark` |
| Sección blanca (tarjetas) | `divi/section` | `section:white` |
| Eyebrow / etiqueta superior | `divi/text` | `text:eyebrow` |
| Titular H1 hero (masivo) | `divi/heading` | `text:display-xl` |
| H1 hero oscuro | `divi/heading` | `text:hero-title` |
| Subtítulo H2 fondo claro | `divi/heading` | `text:headline` |
| Subtítulo H2 fondo oscuro | `divi/heading` | `text:headline-light` |
| Título H3 sección | `divi/heading` | `text:headline-3` |
| Párrafo lead oscuro | `divi/text` | `text:lead` |
| Párrafo lead claro | `divi/text` | `text:lead-dark` |
| Feature card (icono+texto) | `divi/blurb` | `module:feature-card` |
| Card estándar | `divi/text` o `divi/blurb` | `module:card` |
| Glassmorphism card | `divi/text` o `divi/blurb` | `module:glass-card` |
| Stat / Contador grande | `divi/number-counter` | `module:stat-item` |
| Botón CTA primario | `divi/button` | `module:btn-primary` |
| Botón secundario ghost | `divi/button` | `module:btn-ghost` |
| Slider de contenido | `divi/slider` + hijos `divi/slide` | — |
| Mapa de ubicación | `divi/map` | — |
| Formulario de contacto | `divi/contact-form` + `divi/contact-field` | — |
| Separador decorativo | `divi/divider` | — |
| Separador SVG con curva | `divi/section` | `divider:curve-*` |
| Separador SVG con onda | `divi/section` | `divider:wave-*` |
| Separador SVG inclinado | `divi/section` | `divider:tilt-top` |

---

## 3. Column Structures Válidas

| Valor | Layout | Tipos (`type`) |
| :--- | :--- | :--- |
| `4_4` | Full width | `4_4` |
| `1_2,1_2` | Dos mitades | `1_2` |
| `1_3,1_3,1_3` | Tres iguales | `1_3` |
| `2_3,1_3` | 2/3 + 1/3 | `2_3`, `1_3` |
| `1_4,1_4,1_4,1_4` | Cuatro columnas | `1_4` |
| `3_4,1_4` | 3/4 + 1/4 | `3_4`, `1_4` |

---

## 4. Sistema de Design Tokens (`{{design:*}}`)

**IMPORTANTE:** El Diseñador no puede inventar colores ni fuentes. Debe consultar el archivo `DAW_bundle/site/<DAW_SITE>/design-system/divitheme.json` y usar ÚNICAMENTE los tokens allí definidos.

Los tokens mapean a las propiedades declaradas en el nodo `tokens` de ese JSON:

| Uso en el Schema | Sin Global Colors | Con Global Colors sincronizados |
| :--- | :--- | :--- |
| `{{design:color:ink}}` | `#1A1814` (hex) | `$variable({"type":"color","value":{"name":"gcid-ink","settings":{}}})$` → editable en VB |
| `{{design:color:accent}}` | `#A67C40` (hex) | `$variable({"type":"color","value":{"name":"gcid-accent","settings":{}}})$` → editable en VB |

> **IMPORTANTE (Two-Layer Resolution)**:
> 1. **build_page.php**: `{{design:color:*}}` → `var(--gcid-*)` (si hay sync previo; fallback a hex si no).
> 2. **Layout Engine** (`convert_gcid_to_variable_syntax`): `var(--gcid-*)` → `$variable({"type":"color","value":{"name":"gcid-*","settings":{}}})$` antes de `json_encode`.
>
> Divi 5 VB requiere la sintaxis `$variable()` para reconocer colores globales. El Layout Engine aplica la conversión automáticamente al serializar a JSON en `post_content`. Si no hay sync, resuelve a hex como fallback en ambos pasos.

*Nota: Para lograr el estándar premium, el Diseñador debe abusar de los tokens de espaciado grande (`space:lg`, `space:xl`) y los radios orgánicos (`radius:lg`, `radius:full`).*

---

### 4.1. Mapeo al Customizer de Divi (Obligatorio)

El design system JSON debe incluir una sección `customizer` que mapee los tokens de color a los 5 slots de color global del Customizer de Divi. El `global_colors sync` lee esta sección y actualiza automáticamente los colores del Customizer.

**Estructura obligatoria en `<proyecto>.json`:**

| Clave JSON | Slot de Divi | Propósito |
|---|---|---|
| `primary` | `gcid-primary-color` | Color principal (botones, enlaces) |
| `secondary` | `gcid-secondary-color` | Color secundario |
| `heading` | `gcid-heading-color` | Color de títulos |
| `body` | `gcid-body-color` | Color de texto de cuerpo |
| `link` | `gcid-link-color` | Color de enlaces |

Los valores deben ser nombres de tokens definidos en `tokens.color`:

```json
{
  "tokens": {
    "color": {
      "accent": "#A67C40",
      "premium": "#D4A96A",
      "ink": "#1A1814",
      "parchment-700": "#5C5244"
    }
  },
  "customizer": {
    "primary":   "accent",
    "secondary": "premium",
    "heading":   "ink",
    "body":      "parchment-700",
    "link":      "accent"
  }
}
```

**Regla:** si la sección `customizer` falta, el sync omite el mapeo — los colores del Customizer quedan en sus valores por defecto. Para activarlos, agrega el bloque y ejecuta `wp agentic global_colors sync --force`.

---

### 4.2. Design System Creator (Generación Automatizada)

El script `DAW_bundle/workspace/build_design_system.py` (v3.0, design intelligence) genera un `divitheme.json` completo en `site/<DAW_SITE>/design-system/` desde un set mínimo de variables.

**Capacidades inteligentes:**
- Dado `color_accent`, deriva automáticamente `accent_hover`, `premium`, `sepia_*`, y la paleta completa (26 colores)
- Valida contraste WCAG AA/AAA en todas las combinaciones texto+fondo críticas
- Enriquece presets: añade hover states faltantes, clamp() fluido, divisores SVG, glass-card
- Auto-genera presets completos incluso sin archivo `_design_presets.json`

**Flujo de trabajo:**

1. Crea un archivo JSON con solo las variables que quieras personalizar:

```json
{
  "brand_name": "Mi Marca",
  "brand_description": "Descripción premium",
  "color_accent": "#8B6F47",
  "font_display": "'Playfair Display', Georgia, serif",
  "font_ui": "'Inter', system-ui, sans-serif"
}
```

2. Ejecuta el generador:

```powershell
python DAW_bundle/workspace/build_design_system.py `
  --vars DAW_bundle/site/<DAW_SITE>/brand/_design_vars.json `
  --presets DAW_bundle/site/<DAW_SITE>/brand/_design_presets.json `
  --out DAW_bundle/site/<DAW_SITE>/design-system/divitheme.json
```

3. Sincroniza colores globales:

```powershell
wp agentic global_colors sync `
  --design-system="DAW_bundle/site/bibliotheca/design-system/divitheme.json"
```

**Variables disponibles (50 total):**

| Grupo | Variables | Default ultra-pro | Inteligencia |
|---|---|---|---|
| Brand | `brand_name`, `brand_description` | "Ultra Pro Design System" | — |
| Colores (26) | `color_accent`, `color_ink`, `color_parchment_50`… | Paleta neutral-cálida con acento dorado | Deriva 26 colores desde solo `color_accent`. Valida contraste WCAG AA/AAA. |
| Tipografía (3) | `font_display`, `font_body`, `font_ui` | Cormorant Garamond / Crimson Pro / DM Sans | — |
| Radios (5) | `radius_sm`, `radius_md`, `radius_lg`, `radius_xl`, `radius_full` | 2px / 4px / 8px / 16px / 100px | — |
| Espaciado (9) | `space_xs`…`space_5xl` | 8px → 160px | — |
| Customizer (5) | `customizer_primary`…`customizer_link` | accent / premium / ink / parchment-700 / accent | — |

**Presets generados (64 total):**

- **8 secciones**: hero-dark, hero-image-dark, hero-video, trust-bar, cta-epic, light, dark, white
- **16 textos**: eyebrow, eyebrow-dark, hero-title, display-xl, display-md, display-md-light, headline, headline-light, headline-3, lead, lead-dark, body-md, stat-num, stat-label, quote-serif, caption
- **11 módulos**: card, feature-card, glass-card, stat-item, testimonial-card, image-shadow, accent-line, btn-primary, btn-ghost, btn-outline-light, btn-cta-dark
- **5 divisores SVG**: curve-top, curve-bottom, wave-top, wave-bottom, tilt-top
- **12 animaciones**: fade-in, fade-in-fast, slide-up, slide-down, slide-left, slide-right, reveal-up, zoom-in, bounce-up, flip, fold, roll
- **7 scroll**: fade-in, parallax-up, parallax-down, scale-in, reveal, rotate, blur-in
- **5 transform**: hover-lift, hover-scale, hover-glow, hover-slide-up, hover-expand

**Regla:** Si solo necesitas cambiar el color acento, provees `color_accent` y `color_accent_hover`. Las 24 variables de color restantes toman su valor ultra-pro por defecto. El sistema completo queda funcional.

---

## 5. Formato de Definición de Página (`page-defs/<slug>.json`)

El Diseñador crea este archivo. `build_page.php` lo procesa en su totalidad.

```json
{
  "title": "Título de la Página",
  "slug": "mi-pagina",
  "description": "Opcional",
  "sections": [
    {
      "presets": ["section:hero-dark"],
      "parallax": "on",
      "bg_gradient": {
        "type": "linear", "direction": "135deg",
        "overlaysImage": "on",
        "stops": [
          {"color": "rgba(15,23,42,0.92)", "position": "0"},
          {"color": "rgba(15,23,42,0.35)", "position": "100"}
        ]
      },
      "rows": [
        {
          "column_structure": "4_4",
          "modules": [
            {
              "type": "divi/text",
              "presets": ["text:eyebrow"],
              "content": "<p>Etiqueta superior</p>"
            },
            {
              "type": "divi/text",
              "presets": ["text:display-xl"],
              "content": "<h1>Título <em>Principal</em></h1>"
            }
          ]
        },
        {
          "column_structure": "1_2,1_2",
          "columns": [
            {
              "type": "1_2",
              "modules": [
                {
                  "type": "divi/button",
                  "presets": ["module:btn-primary"],
                  "button_text": "Acción principal",
                  "button_url": "/contacto"
                }
              ]
            },
            {
              "type": "1_2",
              "modules": [
                {
                  "type": "divi/blurb",
                  "presets": ["module:feature-card"],
                  "title": "Feature",
                  "icon": "&#xe03a;",
                  "content": "<p>Descripción breve de la característica.</p>"
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

**Formato de definición:**
- `sections[]` — arreglo de secciones
  - `presets[]` — refs a presets del design system (`section:*`, `text:*`, `module:*`)
  - `rows[]` — arreglo de filas
    - `column_structure` — string como `"4_4"`, `"1_2,1_2"`, `"1_3,1_3,1_3"`
    - `modules[]` — (modo simple) módulos en columna única (4_4 implícito)
    - `columns[]` — (modo explícito) arreglo de columnas, cada una con `type` y `modules[]`
    - `module.type` — nombre del módulo Divi 5: `divi/text`, `divi/blurb`, etc.
    - `module.presets[]` — presets a aplicar (se expanden inline vía deep_merge)
    - `module.decoration` — decoration object (spacing, border, boxShadow, animation, etc.)
    - `animation`, `scroll`, `transform` — motion presets como string (ej: `"fade-in"`)

---

## 6. Mapeo Semántico → Atributos Divi 5

| Elemento | Bloque | Cómo se estiliza |
| :--- | :--- | :--- |
| Hero background | `divi/section` | `"presets": ["section:hero-image-dark"], "background_image": "{{SITE_URL}}/wp-content/uploads/...", "bg_gradient": { ... }` |
| Hero con video background | `divi/section` | `"presets": ["section:hero-video"]` + `background_video_mp4` en page def |
| Sección oscura | `divi/section` | `"presets": ["section:dark"]` |
| Sección clara | `divi/section` | `"presets": ["section:light"]` |
| Sección barra stats | `divi/section` | `"presets": ["section:trust-bar"]` |
| CTA Final con imagen | `divi/section` | `"presets": ["section:cta-epic"]` |
| Eyebrow / overline | `divi/text` | `"presets": ["text:eyebrow"]` |
| Titular hero H1 | `divi/heading` | `"presets": ["text:display-xl"]` |
| Hero grande oscuro H1 | `divi/heading` | `"presets": ["text:hero-title"]` |
| Subtítulo / H2 | `divi/heading` | `"presets": ["text:headline"]` (o `text:headline-light` para fondo oscuro) |
| H3 sección | `divi/heading` | `"presets": ["text:headline-3"]` |
| Texto lead oscuro | `divi/text` | `"presets": ["text:lead"]` |
| Texto lead claro | `divi/text` | `"presets": ["text:lead-dark"]` |
| Cita / Quote grande | `divi/text` | `"presets": ["text:quote-serif"]` |
| Línea decorativa | `divi/divider`| `"presets": ["module:accent-line"]` |
| Tarjeta testimonial | `divi/testimonial`| `"presets": ["module:testimonial-card"]` |
| Tarjeta glassmorphism | `divi/text` o `divi/blurb` | `"presets": ["module:glass-card"]` |
| Tarjeta blanca | `divi/text` | `decoration: { background: { color: "{{design:color:surface-white}}" }, border: { radius: ... }, boxShadow: ... }` |
| Separador curva entre secciones | `divi/section` | `"presets": ["divider:curve-top"]` (como preset de section, no de módulo) |
| Separador wave entre secciones | `divi/section` | `"presets": ["divider:wave-bottom"]` |
| Animaciones | Todos | Las animaciones están integradas en los presets. Para animación personalizada: `"decoration": { "animation": { "desktop": { "value": { "style": "slide", "direction": "bottom", "duration": "700ms", "delay": "0ms", "intensity": "15%" } } } }` |

---

## 7. Patrones de Composición Ultra-Premium (Definiciones JSON)

Ejemplos de definiciones de sección para los patrones que producen el mayor impacto visual:

### Patrón: Hero Tipográfico con Imagen de Fondo

```json
{
  "presets": ["section:hero-image-dark"],
  "background_image": "{{SITE_URL}}/wp-content/uploads/hero-bg.jpg",
  "bg_position": "center 40%",
  "bg_gradient": {
    "type": "linear", "direction": "135deg", "overlaysImage": "on",
    "stops": [
      {"color": "rgba(0,19,56,0.90)", "position": "0"},
      {"color": "rgba(0,19,56,0.30)", "position": "100"}
    ]
  },
  "rows": [
    {
      "column_structure": "4_4",
      "modules": [
        {"type": "divi/text", "presets": ["text:eyebrow"], "content": "<p>Etiqueta</p>"},
        {"type": "divi/heading", "presets": ["text:display-xl"], "content": "<h1>T&iacute;tulo Principal</h1>"},
        {"type": "divi/button", "presets": ["module:btn-primary"], "button_text": "Comenzar", "button_url": "/contacto"}
      ]
    }
  ]
}
```

### Patrón: Hero con Video Background

```json
{
  "presets": ["section:hero-video"],
  "background_video_mp4": "{{SITE_URL}}/wp-content/uploads/hero-video.mp4",
  "rows": [
    {
      "column_structure": "4_4",
      "modules": [
        {"type": "divi/text", "presets": ["text:eyebrow-dark"], "content": "<p>Contenido audiovisual</p>"},
        {"type": "divi/heading", "presets": ["text:hero-title"], "content": "<h1>Experiencia <em>Inmersiva</em></h1>"},
        {"type": "divi/button", "presets": ["module:btn-ghost"], "button_text": "Ver m&aacute;s", "button_url": "/acerca"}
      ]
    }
  ]
}
```

### Patrón: Separador SVG entre secciones

Agrega el shape divider como preset adicional en cualquier sección:

```json
{
  "presets": ["section:dark", "divider:curve-top"],
  "rows": [
    {
      "column_structure": "4_4",
      "modules": [
        {"type": "divi/heading", "presets": ["text:headline-light"], "content": "<h2>Nueva secci&oacute;n con entrada curva</h2>"}
      ]
    }
  ]
}
```

Los presets `divider:*` se aplican como presets de sección y decoran el `shapeDivider` del borde superior o inferior de la sección. Cada preset define el estilo, color, altura responsiva y orientación del separador SVG.

### Patrón: Barra de Stats de Autoridad

```json
{
  "presets": ["section:trust-bar"],
  "rows": [
    {
      "column_structure": "1_3,1_3,1_3",
      "columns": [
        {"type": "1_3", "modules": [
          {"type": "divi/number-counter", "presets": ["module:stat-item"], "title": "Años de experiencia", "number": "15"}
        ]},
        {"type": "1_3", "modules": [
          {"type": "divi/number-counter", "presets": ["module:stat-item"], "title": "Clientes activos", "number": "500"}
        ]},
        {"type": "1_3", "modules": [
          {"type": "divi/number-counter", "presets": ["module:stat-item"], "title": "Proyectos completados", "number": "1200"}
        ]}
      ]
    }
  ]
}
```

### Patrón: Grid de Features con Hover

```json
{
  "presets": ["section:light"],
  "rows": [
    {
      "column_structure": "1_3,1_3,1_3",
      "columns": [
        {"type": "1_3", "modules": [
          {"type": "divi/blurb", "presets": ["module:feature-card"],
           "title": "Servicio Uno", "icon": "&#xe03a;", "content": "<p>Descripci&oacute;n breve.</p>",
           "decoration": {"animation": {"desktop": {"value": {"style": "slide", "direction": "bottom", "delay": "0ms"}}}}}
        ]},
        {"type": "1_3", "modules": [
          {"type": "divi/blurb", "presets": ["module:feature-card"],
           "title": "Servicio Dos", "icon": "&#xe03b;", "content": "<p>Descripci&oacute;n breve.</p>",
           "decoration": {"animation": {"desktop": {"value": {"style": "slide", "direction": "bottom", "delay": "100ms"}}}}}
        ]},
        {"type": "1_3", "modules": [
          {"type": "divi/blurb", "presets": ["module:feature-card"],
           "title": "Servicio Tres", "icon": "&#xe03c;", "content": "<p>Descripci&oacute;n breve.</p>",
           "decoration": {"animation": {"desktop": {"value": {"style": "slide", "direction": "bottom", "delay": "200ms"}}}}}
        ]}
      ]
    }
  ]
}
```

### Patrón: CTA Final de Alto Impacto

```json
{
  "presets": ["section:hero-dark"],
  "decoration": {
    "spacing": {"desktop": {"value": {"padding": {"top": "{{design:space:3xl}}", "bottom": "{{design:space:3xl}}"}}}}
  },
  "rows": [
    {
      "column_structure": "4_4",
      "modules": [
        {"type": "divi/heading", "presets": ["text:headline-light"], "content": "<h2>&iquest;Listo para comenzar?</h2>"},
        {"type": "divi/text", "presets": ["text:lead"], "content": "<p>Trabajemos juntos en tu pr&oacute;ximo proyecto.</p>"},
        {"type": "divi/button", "presets": ["module:btn-primary"], "button_text": "Contactar ahora", "button_url": "/contacto",
         "decoration": {"spacing": {"desktop": {"value": {"margin": {"top": "{{design:space:lg}}"}}}}}}
      ]
    }
  ]
}
```

### Patrón: Features Grid con Glassmorphism

```json
{
  "presets": ["section:hero-video"],
  "background_video_mp4": "{{SITE_URL}}/wp-content/uploads/bg-loop.mp4",
  "rows": [
    {
      "column_structure": "4_4",
      "modules": [
        {"type": "divi/heading", "presets": ["text:hero-title"], "content": "<h1>Servicios <em>Premium</em></h1>"}
      ]
    },
    {
      "column_structure": "1_3,1_3,1_3",
      "columns": [
        {"type": "1_3", "modules": [
          {"type": "divi/blurb", "presets": ["module:glass-card"],
           "title": "Diseño", "icon": "&#xe03a;", "content": "<p>Descripci&oacute;n del servicio.</p>"}
        ]},
        {"type": "1_3", "modules": [
          {"type": "divi/blurb", "presets": ["module:glass-card"],
           "title": "Desarrollo", "icon": "&#xe03b;", "content": "<p>Descripci&oacute;n del servicio.</p>"}
        ]},
        {"type": "1_3", "modules": [
          {"type": "divi/blurb", "presets": ["module:glass-card"],
           "title": "Estrategia", "icon": "&#xe03c;", "content": "<p>Descripci&oacute;n del servicio.</p>"}
        ]}
      ]
    }
  ]
}
```
```

---

## 8. Build + Deploy (El Ingeniero)

```powershell
# Un solo comando: construye el schema y despliega en WordPress
.\php.bat DAW_bundle/divi-agentic-core/bin/build_page.php `
  --def=DAW_bundle/site/bibliotheca/page-defs/<slug>.json `
  --deploy

# Opciones adicionales:
# --out=path.json         escribir schema sin desplegar (debug)
# --no-resolve            schema raw sin expandir presets/tokens
# --deploy --front        desplegar y establecer como portada
# --site-url="https://..."  URL explícita (se auto-detecta con --deploy)
```

Ver [`references/engineer.md`](references/engineer.md) para el flujo completo con Global Colors, verificación de deployment y troubleshooting.

> [!CAUTION]
> **PROHIBIDO** usar `et_pb_*` (shortcodes Divi 4). El motor `Layout_Engine` espera únicamente el namespace `divi/*`.
> **PROHIBIDO** usar `divi/code` como comodín visual. Consultar `blocks-dictionary.md` primero.
