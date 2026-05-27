# DAW Module: Phase 3 — Visual Mapping (The Designer)

## Objetivo
Traducir el **Plan Semántico del Arquitecto + Dirección Visual del Design Lead** en un JSON Schema nativo compatible con el `Layout_Engine` de Divi 5.5.0, usando **Decoration Attributes** (no CSS classes).

---

## 0. Principio Fundamental

**NO usar `module_class` con clases `sp5-*`.**  
Toda propiedad visual debe expresarse como atributos nativos de Divi 5 (`decoration`, `headingFont`, `bodyFont`, `spacing`, `border`, etc.) y referencias `{{design:*}}` tokens.

**NUEVO FLUJO (DAW v4.1):**
El Diseñador **YA NO ESCRIBE ARCHIVOS JSON EN CRUDO**. Para evitar errores de sintaxis y facilitar la composición, el Diseñador debe crear un script Python en `workspace/build_nombre_pagina.py` importando `daw_builder.py`, el cual generará el JSON final de forma segura.

El pipeline es:
```
Script Python (daw_builder) 
  → Genera Schema JSON (seguro y escapado)
  → Design_Resolver (resuelve tokens contra design-system.json) 
  → Layout_Engine (compila a bloques Divi 5 nativos)
```

---

## 1. Reglas de Oro del Schema

- **NUNCA** usar `et_pb_*` — el motor espera el namespace `divi/*` (bloques Gutenberg nativos).
- **NUNCA** hardcodear hex colors ni valores en px. Usar siempre `{{design:token}}`.
- **NUNCA** usar `module_class` con clases `sp5-*`. Usar decoration attributes nativos.
- **SIEMPRE** crear un script Python `workspace/build_<slug>.py` que genere el schema. El script exportará el JSON final en `workspace/pages/<slug>.json`.
- **LIBERTAD TOTAL**: Usa `**kwargs` en el `daw_builder` para inyectar cualquier estructura nativa (`decoration`, `animation`, `transform`, `hover`), manteniendo el nivel Premium intacto.

---

## 2. Bloques Divi 5 Disponibles

> **Guía de decisión semántica:** [`references/blocks-dictionary.md`](references/blocks-dictionary.md)
> **Índice de bloques:** [`references/blocks-index.json`](references/blocks-index.json) (102 bloques: slug, nombre, categoría, children)
> **Atributos detallados (bajo demanda):** Ejecutar `php divi-agentic-core/bin/extract-module-meta.php <slug>` para ver tipos, defaults, settings groups y render paths de cualquier bloque.

### Tabla rápida de bloques por elemento visual

| Elemento visual | Bloque | Preset recomendado |
| :--- | :--- | :--- |
| Hero oscuro tipográfico | `divi/section` | `section:hero-dark` |
| Hero con imagen de fondo | `divi/section` | `section:hero-cinematic` |
| Sección clara | `divi/section` | `section:light` |
| Sección oscura alternativa | `divi/section` | `section:dark` |
| Sección blanca (tarjetas) | `divi/section` | `section:white` |
| Eyebrow / etiqueta superior | `divi/text` | `text:eyebrow` |
| Titular H1 hero (masivo) | `divi/text` | `text:display-xl` |
| Subtítulo H2 fondo claro | `divi/text` | `text:headline` |
| Subtítulo H2 fondo oscuro | `divi/text` | `text:headline-light` |
| Párrafo lead oscuro | `divi/text` | `text:lead` |
| Párrafo lead claro | `divi/text` | `text:lead-dark` |
| Feature card (icono+texto) | `divi/blurb` | `module:feature-card` |
| Card estándar | `divi/text` | `module:card` |
| Stat / Contador grande | `divi/number-counter` | `module:stat-item` |
| Botón CTA primario | `divi/button` | `module:btn-primary` |
| Botón secundario ghost | `divi/button` | `module:btn-ghost` |
| Slider de contenido | `divi/slider` + hijos `divi/slide` | — |
| Mapa de ubicación | `divi/map` | — |
| Formulario de contacto | `divi/contact-form` + `divi/contact-field` | — |
| Separador decorativo | `divi/divider` | — |

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

**IMPORTANTE:** El Diseñador no puede inventar colores ni fuentes. Debe consultar el archivo `workspace/design-system/<proyecto>.json` y usar ÚNICAMENTE los tokens allí definidos.

Los tokens mapean a las propiedades declaradas en el nodo `tokens` de ese JSON:

| Uso en el Schema | Resuelve a |
| :--- | :--- |
| `{{design:color:ink}}` | Valor definido en `tokens.color.ink` |
| `{{design:color:accent}}` | Valor definido en `tokens.color.accent` |
| `{{design:font:display}}` | Valor definido en `tokens.font.display` |
| `{{design:radius:lg}}` | Valor definido en `tokens.radius.lg` (ej. 16px) |
| `{{design:space:xl}}` | Valor definido en `tokens.space.xl` (ej. 48px) |

*Nota: Para lograr el estándar premium, el Diseñador debe abusar de los tokens de espaciado grande (`space:lg`, `space:xl`) y los radios orgánicos (`radius:lg`, `radius:full`).*

---

## 5. Presets del Sistema de Diseño

El archivo `<proyecto>.json` también incluye un objeto `presets` prefabricado (ej. configuraciones complejas de sombras y padding). 

Si el JSON incluye el preset `section.hero-dark` o `module.card`, en el schema se aplican así:

```json
{
  "presets": ["section:hero-dark"],
  "rows": [...]
}
```

**Regla de Calidad Premium:** Si el JSON no tiene un preset adecuado, el Diseñador debe construir un bloque `decoration` que asegure calidad ultra-premium (paddings amplios, sombras de gran difusión, border-radius redondeados). El resolver mergea el preset como base; las claves explícitas en `decoration` vencen al preset.

---

## 6. Mapeo Semántico → Atributos Divi 5

| Elemento | Bloque | Cómo se estiliza |
| :--- | :--- | :--- |
| Hero background | `divi/section` | `"presets": ["section:hero-image-dark"], "background_image": "{{SITE_URL}}/wp-content/uploads/...", "bg_gradient": { "type": "linear", "direction": "180deg", "overlaysImage": "on", "stops": [ ... ] }` |
| Sección oscura | `divi/section` | `"presets": ["section:dark"]` |
| Sección clara | `divi/section` | `"presets": ["section:light"]` |
| Sección barra stats | `divi/section` | `"presets": ["section:trust-bar"]` |
| CTA Final con imagen | `divi/section` | `"presets": ["section:cta-epic"]` |
| Eyebrow / overline | `divi/text` | `"presets": ["text:eyebrow"]` |
| Titular hero H1 | `divi/text` | `"presets": ["text:display-xl"]` |
| Subtítulo / H2 | `divi/text` | `"presets": ["text:headline"]` (o `text:headline-light` para fondo oscuro) |
| Texto lead oscuro | `divi/text` | `"presets": ["text:lead"]` |
| Texto lead claro | `divi/text` | `"presets": ["text:lead-dark"]` |
| Cita / Quote grande | `divi/text` | `"presets": ["text:quote-serif"]` |
| Línea decorativa | `divi/divider`| `"presets": ["module:accent-line"]` |
| Tarjeta testimonial | `divi/testimonial`| `"presets": ["module:testimonial-card"]` |
| Tarjeta blanca | `divi/text` | `decoration: { background: { color: "{{design:color:white}}" }, border: { radius: ... }, boxShadow: ... }` |
| Animaciones | Todos | Las animaciones están integradas en los presets. Para animación personalizada: `"decoration": { "animation": { "desktop": { "value": { "style": "slide", "direction": "bottom", "duration": "700ms", "delay": "0ms", "intensity": "15%" } } } }` |

---

## 7. Construyendo la página con DAW Builder SDK (Python)

```python
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from daw_builder import Page, Section, Row, Module

page = Page("Mi Página")

hero = Section(
    presets=["section:hero-image-dark"],
    background_image="{{SITE_URL}}/wp-content/uploads/2026/05/hero-bg.jpg"
)
r1 = Row("1_2,1_2")
r1.add_module(0, Module(
    "divi/text",
    headingFont={
        "h1": {"font": {"desktop": {"value": {
            "fontFamily": "{{design:font:display}}",
            "color": "{{design:color:white}}",
            "size": "48px", "weight": "700"
        }}}}
    },
    content="<h1>Título <em>Principal</em></h1>"
))
r1.add_module(0, Module(
    "divi/code",
    content="<a href='/contacto' style='...'>Contactar</a>"
))
r1.add_module(1, Module(
    "divi/image",
    src="{{SITE_URL}}/wp-content/uploads/2026/05/imagen.png",
    alt="Descripción"
))

hero.add_row(r1)
page.add_section(hero)

page.export(os.path.join(os.path.dirname(os.path.abspath(__file__)), "pages", "mi-pagina.json"))
```

---

## 8. Patrones de Composición Ultra-Premium (Ejemplos Python)

Ejemplos de scripts para los patrones que producen el mayor impacto visual:

### Patrón: Hero Tipográfico de Clase Mundial con Imagen de Fondo

```python
hero = Section(
    presets=["section:hero-image-dark"],
    background_image="{{SITE_URL}}/wp-content/uploads/2026/04/La_Biblia_PW-scaled.jpg",
    bg_position="center 40%",
    bg_gradient={
        "type": "linear", "direction": "135deg", "overlaysImage": "on",
        "stops": [
            { "color": "rgba(0,19,56,0.90)", "position": "0%" },
            { "color": "rgba(0,19,56,0.30)", "position": "100%" }
        ]
    }
)
r1 = Row("4_4")
r1.add_module(0, Module("divi/text", presets=["text:eyebrow"], content="<p>Etiqueta</p>"))
hero.add_row(r1)
```
### Patrón: Barra de Stats de Autoridad

```python
trust = Section(presets=["section:dark"])
r2 = Row("1_3,1_3,1_3")
stats = [("15+", "Años"), ("50", "Expertos"), ("100%", "Satisfechos")]
for i, (num, title) in enumerate(stats):
    r2.add_module(i, Module(
        "divi/number-counter", presets=["module:stat-item"],
        title=title, number=num
    ))
trust.add_row(r2)
```

### Patrón: Grid de Features con Hover Elevación

```python
features = Section(presets=["section:light"])
grid = Row("1_3,1_3,1_3")
servicios = [
    ("Servicio Uno", "&#xe03a;", "Descripción breve..."),
    ("Servicio Dos", "&#xe03b;", "Descripción breve..."),
    ("Servicio Tres", "&#xe03c;", "Descripción breve...")
]
for i, (title, icon, text) in enumerate(servicios):
    grid.add_module(i, Module(
        "divi/blurb",
        presets=["module:feature-card"],
        title=title, icon=icon, content=f"<p>{text}</p>",
        decoration={
            "animation": {"desktop": {"value": {"style": "slide", "delay": f"{i*100}ms"}}}
        }
    ))
features.add_row(grid)
```

### Patrón: CTA Final de Alto Impacto

```python
cta = Section(
    presets=["section:hero-dark"],
    decoration={ "spacing": { "desktop": { "value": { "padding": { "top": "{{design:space:3xl}}", "bottom": "{{design:space:3xl}}" } } } } }
)
r_cta = Row("4_4")
r_cta.add_module(0, Module("divi/text", presets=["text:headline-light"], content="<h2>¿Listo para comenzar?</h2>"))
r_cta.add_module(0, Module("divi/text", presets=["text:lead"], content="<p>Únete hoy mismo.</p>"))
r_cta.add_module(0, Module("divi/button", presets=["module:btn-primary"], button_text="Contactar", button_url="/contacto",
    decoration={ "spacing": { "desktop": { "value": { "margin": { "top": "{{design:space:lg}}" } } } } }
))
cta.add_row(r_cta)
```

---

## 10. Despliegue (El Ingeniero)

```powershell
.\wp.bat agentic deploy_page `
  --title="T&iacute;tulo de la P&aacute;gina" `
  --slug="slug-de-pagina" `
  --schema="workspace/pages/slug-de-pagina.json" `
  --design-system="workspace/design-system/proyecto.json"
```
