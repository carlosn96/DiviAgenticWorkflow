# INSTRUCCION DEFINITIVA: Sistema de Composicion Visual Premium para DAW

## Contexto de existencia

Esta instruccion define el unico pipeline valido para generar paginas Divi 5 premium dentro del proyecto divitheme. Si el resultado final no es visualmente comparable a diviplus.io o a los estandares ux-pro, la implementacion ha fallado. No se aceptan parches parciales ni justificaciones tecnicas.

---

## 1. Diagnostico de la falla actual (no repetir)

El pipeline PATH A (`design_direction`) falla porque:

1. **Los layouts son monoliticos** — `_build_designer_hero`, `_build_designer_features`, etc. usan `column_structure` hardcodeado (siempre `4_4`, `1_2,1_2`, `1_4,1_4`) sin importar el tipo de pagina.
2. **Ignora los activos del proyecto** — Los 877 templates de `workspace/sections/catalog/`, los 103 schemas de modulos, y el clasificador UX-Pro no se consultan para decidir la composicion visual.
3. **Mapea semanticamente al vacio** — `brief.image` no genera `divi/image`; `brief.testimonials` no genera `divi/testimonial`; todo se mete en `divi/text` o placeholders `<p>&nbsp;</p>`.
4. **Trata el diseno como decoracion** — Se enfoca en glass/grain/orb CSS como si eso fuera "premium", pero el layout subyacente es siempre el mismo grid simetrico de 3 columnas.
5. **No hay narrativa visual** — Las secciones no se relacionan visualmente. No hay ritmo de alternancia claro-oscuro, no hay escala visual, no hay focal points asimetricos.

---

## 2. Activos disponibles (usar obligatoriamente)

| Asset | Ubicacion | Rol en la solucion |
|-------|-----------|-------------------|
| **877 templates de seccion** | `workspace/sections/catalog/*.section.json` | Fuente de verdad de layouts profesionales. Extraer `column_structure`, tipos de modulo, y orden de composicion. |
| **12 block patterns (diviplus)** | `workspace/data/diviplus_dataset.json` | Combinaciones ganadoras de modulos por estrategia. Usar para validar que un layout incluye los modulos correctos. |
| **103 schemas de modulo nativo** | `workspace/data/modules/*.json` | Fuente autoritativa de atributos. Cada campo del brief debe mapear a un modulo real con sus atributos validos. |
| **UXProBridge** | `ml-dataset/artifacts/ux_pro_bridge.py` | `classify(tone, product_type)` retorna `variant_hint` y `effects_tags`. Mapear `variant_hint` a layout family (editorial → broken grid, liquid-glass → glassmorphism, etc.). |
| **FRONTEND_PRINCIPLES** | `daw/constants.py` | `aesthetic.*` flags para activar glass, grain, multi_shadow, blur_reveal. Aplicar como capa final, no como sustituto de layout. |
| **Design system** | `site/<DAW_SITE>/design-system/divitheme.json` | Tokens de color, tipografia, espacio. Usar para mantener coherencia visual. |
| **Brand vars** | `site/<DAW_SITE>/brand/_design_vars.json` | Colores, fonts, espaciado de marca. |

---

## 3. Arquitectura de la solucion

La solucion requiere 3 capas nuevas en el VIE, operando EN ESTE ORDEN:

### Capa 1: NarrativeComposer (`vie/narrative_composer.py`) — NUEVO

**Proposito**: Transformar el brief de secciones aisladas en una **secuencia visual con ritmo**.

**Reglas**:
1. Alternancia forzada de zonas oscuro/claro: hero (dark) → features (light) → stats (dark) → testimonials (light) → CTA (dark).
2. Escalado visual progresivo: hero (H1 grande) → features (H2 medio) → stats (numeros gigantes) → testimonials (citas) → CTA (H2 compacto).
3. Cada pagina debe tener 6-8 secciones minimum. Nunca 4.
4. Secciones obligatorias por `page_type`:
   - **home**: hero, trust-bar, features, stats, testimonials, pricing, CTA
   - **about**: hero, trust-bar, content (imagen+texto), features, team, stats, CTA
   - **services**: hero, features, process/steps, pricing, testimonials, CTA
   - **destinations**: hero, gallery, features, testimonials, CTA
   - **contact**: hero (minimal), content (mapa+info), contact-form, CTA

**Entrada**: brief JSON con `page_type` y `sections[]`.
**Salida**: `composed_brief` con secciones expandidas, ordenadas, y con `visual_zone` (dark/light) asignado.

### Capa 2: SemanticModuleMapper (`vie/semantic_module_mapper.py`) — NUEVO

**Proposito**: Mapear cada campo semantico del brief al **modulo Divi nativo correcto** usando los 103 schemas.

**Tabla de mapeo obligatorio**:

| Campo del brief | Modulo Divi | Atributos a poblar (del schema) |
|-----------------|-------------|--------------------------------|
| `image` (URL simple) | `divi/image` | `image.src` = URL |
| `video` (URL) | `divi/video` | `video.src` = URL |
| `gallery[]` (array de URLs) | `divi/gallery` | `gallery.images[]` = `{src, alt}` |
| `slider[]` | `divi/slider` | `slider.slides[]` = `{image, title, content}` |
| `testimonial` | `divi/testimonial` | `testimonial.author`, `testimonial.company`, `testimonial.body`, `testimonial.portrait_url` |
| `pricing[]` | `divi/pricing` | `pricing.tables[]` = `{title, currency, price, period, features[], button}` |
| `map` | `divi/map` | `map.address` o `map.lat`/`map.lng` |
| `form` | `divi/contact-form` | `contact-form.fields[]` |
| `accordion[]` | `divi/accordion` | `accordion.items[]` = `{title, content}` |
| `number` + `label` | `divi/number-counter` | `number-counter.number`, `number-counter.title` |
| `eyebrow` | `divi/text` | `content` = texto, `decoration.font` = eyebrow style |
| `title` / `heading` | `divi/heading` o `divi/text` con `<h1>`/`h2>` | `content` = `<h1>texto</h1>`, `level` = h1/h2 |
| `text` / `body` | `divi/text` | `content` = `<p>texto</p>` |
| `btn_primary_text` | `divi/button` | `button.text`, `button.url` |
| `icon` + `title` + `text` | `divi/blurb` | `blurb.title`, `blurb.content`, `imageIcon.icon` = unicode |

**Reglas de mapeo**:
1. Si `brief.image` existe y la seccion es hero/about/content → crear `divi/image` con `src` real. NO placeholder `<p>&nbsp;</p>`.
2. Si `brief.testimonials[]` existe → crear `divi/testimonial` por cada uno, con foto si existe `image` en el testimonial.
3. Si `brief.pricing[]` existe → crear `divi/pricing` con tablas reales, NO blurbs con texto.
4. Si `brief.gallery[]` o `brief.slider[]` existe → crear `divi/gallery` o `divi/slider` con imagenes reales.
5. Si `brief.map` existe → crear `divi/map` con direccion real.
6. Si `brief.form` existe → crear `divi/contact-form` con campos reales.
7. Si `brief.accordion[]` existe → crear `divi/accordion`.

**Politica de imagenes**:
- Si el brief no tiene URLs de imagen, usar `https://picsum.photos/seed/<nombre-unico>/<ancho>/<alto>` con seeds semanticas (ej: `nomade-patagonia`, `nomade-bali`, `nomade-team-ana`).
- Las imagenes deben tener dimensiones consistentes con el layout: hero `1600/900`, testimonials `400/400` (cuadrado), team `600/800` (vertical), gallery `800/600`.

### Capa 3: LayoutComposer (`vie/layout_composer.py`) — NUEVO

**Proposito**: Seleccionar `column_structure` y disposicion de modulos dentro de columnas usando el catalogo de 877 templates y las decisiones del UXProBridge.

**Familias de layout por `variant_hint` de UXProBridge**:

| variant_hint | Layout family | Caracteristicas |
|--------------|---------------|-----------------|
| `liquid-glass` | Glassmorphism | Cards con backdrop blur, video/image full-bleed en hero, overlays oscuros semi-transparentes |
| `editorial-grid` | Broken grid | Elementos que se salen de columnas, texto superpuesto a imagen, grids asimetricos (2_5+3_5, 1_3+2_3) |
| `minimal-card` | Swiss minimal | Grids simetricos estrictos, mucho whitespace, tipografia limpia, sin decoracion |
| `monochrome-brutalist` | Brutalism | Bordes gruesos, tipografia bold, contraste extremo, layouts rectangulares agresivos |
| `glass-metric` | Data viz | Numeros grandes, grids de datos, iconos lineales, fondos claros |

**Layouts por seccion y page_type** (ejemplos ejecutables):

**Home (warm_minimal + editorial-grid)**:
- Hero: `2_5,3_5` → izquierda texto (eyebrow+h1+body+button), derecha imagen grande
- Trust-bar: `4_4` → logo carousel (divi/image repetido 5x en fila)
- Features: `1_3,1_3,1_3` → 3 blurbs con icono + titulo + texto
- Stats: `1_4,1_4,1_4,1_4` → 4 number-counters
- Testimonials: `1_3,1_3,1_3` → 3 divi/testimonial con portrait circular
- Pricing: `1_3,1_3,1_3` → 3 divi/pricing con highlight en el medio
- CTA: `4_4` → texto centrado + boton grande

**About (warm_minimal + editorial-grid)**:
- Hero: `4_4` → texto centrado (mas sobrio)
- Trust-bar: `4_4` → logos
- Content: `1_2,1_2` → izquierda imagen grande, derecha eyebrow+h2+body+button
- Features: `1_2,1_2` → 2 blurbs grandes con imagen de fondo
- Team: `1_3,1_3,1_3` → 3 divi/person (o blurb con imagen circular)
- Stats: `1_4,1_4,1_4,1_4` → 4 contadores
- CTA: `4_4` → centrado

**Services (warm_minimal + glass-metric)**:
- Hero: `1_2,1_2` → izquierda texto, derecha imagen de servicio
- Features: `1_2,1_2` → 2 blurbs con icono
- Process: `1_4,1_4,1_4,1_4` → 4 steps con numero + titulo + descripcion
- Pricing: `1_3,1_3,1_3` → 3 divi/pricing
- Testimonials: `1_2,1_2` → 2 testimoniales con foto grande
- CTA: `4_4` → centrado

**Destinations (warm_minimal + liquid-glass)**:
- Hero: `4_4` → full-bleed image con overlay oscuro + texto centrado
- Gallery: `4_4` → divi/slider con 5 slides de destinos
- Features: `1_3,1_3,1_3` → 3 blurbs
- Testimonials: `1_3,1_3,1_3` → 3 testimonios
- CTA: `4_4` → centrado

**Contact (warm_minimal + minimal-card)**:
- Hero: `4_4` → minimal, solo h2 + subtitulo
- Content: `1_2,1_2` → izquierda divi/contact-form, derecha divi/map + info
- CTA: `4_4` → boton grande

**Regla de oro del LayoutComposer**:
- NUNCA repetir el mismo `column_structure` en mas de 2 secciones por pagina.
- Si una seccion tiene `image` en el brief, la imagen debe ocupar al menos 1/2 del ancho (`1_2` o `2_5` o `3_5`).
- Si una seccion tiene `testimonials`, usar `divi/testimonial` nativo, no blurbs con texto.
- Si una seccion tiene `pricing`, usar `divi/pricing` nativo.
- Si una seccion tiene `gallery`, usar `divi/gallery` o `divi/slider`.

### Capa 4: PremiumEffectLayer (existente, `_apply_premium_css` en `section.py`)

**Rol**: Aplicar glass, grain, orb, blur-reveal, stagger COMO CAPA FINAL sobre el layout ya compuesto.

**Regla**: Los efectos premium se aplican DESPUES de que LayoutComposer ha decidido la estructura. No sustituyen la estructura.

---

## 4. Flujo de ejecucion (pipeline completo)

```
brief.json (con campos semanticos reales)
  ↓
NarrativeComposer → composed_brief (8 secciones, ritmo claro/oscuro)
  ↓
SemanticModuleMapper → cada seccion tiene modulos Divi nativos reales (image, testimonial, pricing, etc.)
  ↓
UXProBridge.classify() → variant_hint → layout family
  ↓
LayoutComposer → column_structure asimetrico + modulos distribuidos en columnas
  ↓
DesignDirector.get_profile() → colors, fonts, spacing
  ↓
DecorationBuilder → background, border, boxShadow, animation
  ↓
PremiumEffectLayer → css.freeForm (grain, orb, blur-reveal, stagger)
  ↓
plan.json (rico: modulos nativos, layouts variados, efectos premium)
  ↓
build_page.php --deploy → WordPress
```

---

## 5. Formato del brief (obligatorio)

El brief DEBE incluir estos campos para que el pipeline funcione:

```json
{
  "title": "Home — Nomade Viajes",
  "slug": "home",
  "page_type": "home",
  "description": "...",
  "design_direction": {
    "mood": "warm_minimal",
    "color_temperature": "warm_on_dark",
    "typography_style": "serif_display_plus_sans_ui",
    "layout_rhythm": "editorial_grid",
    "spacing_density": "generous",
    "accent_material": "warm_gold",
    "motion_intensity": "subtle_parallax"
  },
  "sections": [
    {
      "section_type": "hero",
      "eyebrow": "NOMADE VIAJES",
      "title": "Descubre el Mundo con Nomade",
      "text": "Viajes que transforman. Experiencias que perduran.",
      "image": "https://images.unsplash.com/photo-1506929562872-bb421503ef21?w=1600&q=80",
      "btn_primary_text": "Explorar Destinos",
      "btn_primary_url": "/destinos"
    },
    {
      "section_type": "trust-bar",
      "items": [
        {"image": "https://picsum.photos/seed/natgeo/200/80", "alt": "National Geographic"},
        {"image": "https://picsum.photos/seed/lonely/200/80", "alt": "Lonely Planet"}
      ]
    },
    {
      "section_type": "features",
      "eyebrow": "POR QUÉ NOMADE",
      "title": "Más de 15 años creando viajes inolvidables",
      "items": [
        {
          "icon": "&#xe052;",
          "title": "Destinos Exclusivos",
          "text": "Rutas cuidadosamente diseñadas lejos del turismo masivo.",
          "image": "https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?w=800&q=80"
        }
      ]
    },
    {
      "section_type": "stats",
      "eyebrow": "NÚMEROS QUE HABLAN",
      "title": "Nuestra Trayectoria",
      "stats": [
        {"number": "150", "label": "Destinos"},
        {"number": "12", "label": "Países"},
        {"number": "98", "label": "Satisfacción"},
        {"number": "5000", "label": "Viajeros Felices"}
      ]
    },
    {
      "section_type": "testimonials",
      "eyebrow": "TESTIMONIOS",
      "title": "Lo Que Dicen Nuestros Viajeros",
      "testimonials": [
        {
          "name": "Carolina y Marco",
          "role": "Luna de Miel en Bali",
          "text": "Nomade transformó nuestra luna de miel en algo que siempre recordaremos.",
          "image": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=400&h=400&q=80"
        }
      ]
    },
    {
      "section_type": "pricing",
      "eyebrow": "PAQUETES",
      "title": "Elige Tu Aventura",
      "pricing": [
        {
          "name": "Explorador",
          "price": "$1,200",
          "period": "por persona",
          "features": ["7 días / 6 noches", "Guía nativo", "Alojamiento boutique", "Desayuno incluido"],
          "button": "Reservar",
          "button_url": "/contacto"
        },
        {
          "name": "Aventurero",
          "price": "$2,400",
          "period": "por persona",
          "features": ["10 días / 9 noches", "Guía privado", "Alojamiento 5 estrellas", "Todas las comidas", "Traslados VIP"],
          "highlight": true,
          "button": "Reservar",
          "button_url": "/contacto"
        },
        {
          "name": "Nómada",
          "price": "Custom",
          "period": "consultar",
          "features": ["Itinerario a la medida", "Equipo completo", "Soporte 24/7", "Acceso exclusivo"],
          "button": "Cotizar",
          "button_url": "/contacto"
        }
      ]
    },
    {
      "section_type": "cta",
      "eyebrow": "CONTACTO",
      "title": "Tu Próximo Viaje Comienza Aquí",
      "text": "Déjanos sorprenderte con destinos que ni imaginabas.",
      "btn_primary_text": "Planificar Mi Viaje",
      "btn_primary_url": "/contacto"
    }
  ]
}
```

**Reglas del brief**:
- `page_type` es obligatorio. Sin ello, LayoutComposer no puede elegir layouts distintos.
- `image` debe ser URL real (Unsplash/Pexels/picsum). No placeholders vacíos.
- `testimonials` debe incluir `image` (foto del autor) cuando sea posible.
- `pricing` debe incluir `features[]`, `price`, `period`, y `highlight` para la tabla destacada.
- Cada seccion debe tener `eyebrow` + `title`. Nunca solo `title`.

---

## 6. Reglas de implementacion (leyes inquebrantables)

1. **NO crear modulos custom PHP** — Solo usar los 103 modulos nativos de `workspace/data/modules/`.
2. **NO inyectar CSS en functions.php** — Usar `css.freeForm` como atributo top-level del bloque.
3. **NO usar shortcodes Divi 4** — Solo namespace `divi/*`.
4. **NO usar `divi/code`** — No custom HTML/JS.
5. **NO modificar build_page.php** — El PHP ya lee `css` y `decoration`. No necesita cambios.
6. **NO modificar Layout Engine** — El engine ya procesa `_type`, `css`, `decoration`. No necesita cambios.
7. **NO modificar design_director.py** — El perfil de mood se mantiene. Se agregan campos si es necesario, no se quitan.
8. **NO modificar build_design_system.py** — El design system es la fuente de tokens. No se toca.
9. **SIEMPRE verificar con volcado** — Cada deploy debe producir un archivo `.txt` en `content_state/local/` para auditoria.
10. **SIEMPRE correr tests** — `python -m pytest DAW_bundle/tests/` debe pasar 100% antes de considerar terminado.

---

## 7. Metricas de exito (verificables)

Desplegar 5 paginas y verificar en el volcado (post_content de WordPress):

### Metrica A: Diversidad de layouts
- [ ] Home tiene hero con `column_structure` != `4_4` (debe ser `2_5,3_5`, `1_2,1_2`, o `4_4` con imagen full-bleed)
- [ ] About tiene al menos 1 seccion con `column_structure: "1_2,1_2"` (imagen + texto)
- [ ] Services tiene seccion `pricing` con `divi/pricing` y `column_structure: "1_3,1_3,1_3"`
- [ ] Destinations tiene seccion `gallery` con `divi/slider` o `divi/gallery`
- [ ] Contact tiene seccion con `divi/contact-form` y `column_structure: "1_2,1_2"` (form + mapa)
- [ ] Ninguna pagina repite el mismo `column_structure` en mas de 2 secciones

### Metrica B: Diversidad de modulos
- [ ] Cada pagina usa al menos 6 modulos Divi nativos distintos (de los 103 disponibles)
- [ ] `divi/image` aparece en al menos 3 secciones (hero, content, team, gallery)
- [ ] `divi/testimonial` aparece en al menos 2 paginas
- [ ] `divi/pricing` aparece en services o home
- [ ] `divi/map` aparece en contact
- [ ] `divi/slider` o `divi/gallery` aparece en destinations
- [ ] `divi/contact-form` aparece en contact

### Metrica C: Efectos premium preservados
- [ ] Todas las paginas tienen `css.desktop.value.freeForm` en al menos 3 secciones
- [ ] `radial-gradient` (orb glow) presente en hero de home y CTA
- [ ] `feTurbulence` (grain) presente en secciones light
- [ ] `@keyframes revealUp` (blur-reveal) presente en secciones con stagger
- [ ] Stagger delays numericos progresivos (`0ms`, `100ms`, `200ms`, etc.)
- [ ] Glass cards con `backdropFilter: blur(...) saturate(...)` en features
- [ ] `boxShadow` multi-capa en cards

### Metrica D: Narrativa visual
- [ ] Alternancia claro/oscuro visible (dark hero → light features → dark stats → light testimonials → dark CTA)
- [ ] Tipografia escalada (H1 clamp(3rem,7vw,5.5rem) → H2 clamp(2rem,4vw,3rem) → body 16px)
- [ ] Bodoni Moda en headings, Jost en body (verificable en `bodyFont.fontFamily`)
- [ ] Eyebrows presentes en al menos 5 secciones por pagina
- [ ] No hay secciones vacias (sin modulos)

### Metrica E: Copy real
- [ ] Los briefs usan texto comercial real (beneficios, emocion, storytelling), no lorem ipsum ni placeholders genericos
- [ ] Cada boton tiene CTA especifica ("Planificar Mi Viaje", "Reservar Ahora", no "Click Here")
- [ ] Los testimonios incluyen nombre, rol, y cita especifica del viaje

---

## 8. Contraindicaciones (NO hacer — inflaria codigo sin resultado)

- **NO agregar mas moods** a `design_director.py`. `warm_minimal` ya tiene todos los campos premium.
- **NO agregar mas CSS manual** en `building.py`. Los 11 metodos de PremiumCSSBuilder son suficientes.
- **NO crear mas presets** en `build_design_system.py`. 58 presets ya cubren glass-card, btn-primary, stagger-reveal.
- **NO agregar mas handlers** en `vie/handlers/`. PATH A ya tiene 12 handlers. El LayoutComposer los reemplaza generivamente.
- **NO modificar el UXProBridge**. Ya clasifica correctamente. Solo hay que conectar su output al LayoutComposer.
- **NO crear una UI web para generar briefs**. Usar CLI y JSON.
- **NO escribir mas tests unitarios triviales**. Solo tests de composicion (`test_composition.py`) y E2E (`test_premium_pipeline.py`).

---

## 9. Archivos a crear/modificar

### Nuevos (obligatorios)

1. `vie/narrative_composer.py` — Expande briefs a 6-8 secciones, alternancia claro/oscuro, escalado visual.
2. `vie/semantic_module_mapper.py` — Mapea campos del brief a modulos Divi nativos (103 schemas).
3. `vie/layout_composer.py` — Selecciona column_structure asimetrico por page_type + variant_hint + catalogo de 877 templates.
4. `vie/catalog_ingestor.py` — Lee 877 templates y extrae patterns de layout y combinaciones de modulos.
5. `tests/test_composition.py` — Verifica que home != about != services en layout y modulos.

### Modificados (obligatorios)

6. `vie/section.py` — Reemplazar `_build_designer_*` monoliticos por `_compose_rows()` generico que use los 3 componentes nuevos. Preservar `_apply_stagger` y `_apply_premium_css`.
7. `vie/__init__.py` — Exportar NarrativeComposer, SemanticModuleMapper, LayoutComposer.
8. `vie/engine.py` — Integrar NarrativeComposer antes de SectionBuilder.
9. `site/nomade/briefs/home.json` — Agregar page_type, campos semanticos reales (imagenes, testimonios, pricing).
10. `site/nomade/briefs/about.json` — Agregar page_type, campos semanticos reales (imagenes, team, stats).
11. `site/nomade/briefs/services.json` — Agregar page_type, campos semanticos reales (imagenes, pricing, process).
12. `site/nomade/briefs/destinations.json` — Agregar page_type, campos semanticos reales (galeria, slider, imagenes).
13. `site/nomade/briefs/contact.json` — Agregar page_type, campos semanticos reales (mapa, formulario, info).

### Invariantes (NO tocar)

- `daw/constants.py` — FRONTEND_PRINCIPLES ya tiene glass/grain/orb/stagger.
- `vie/design_director.py` — DesignProfile y 5 moods ya estan completos.
- `vie/building.py` — PremiumCSSBuilder ya genera CSS premium.
- `divi-agentic-core/inc/core/class-layout-engine.php` — Layout Engine ya procesa `_type`, `css`, `decoration`.
- `divi-agentic-core/bin/build_page.php` — Build ya lee plans, resuelve tokens, despliega.
- `workspace/build_design_system.py` — Design system generado tiene 58 presets premium.

---

## 10. Ejecucion paso a paso

1. Implementar `vie/catalog_ingestor.py` (lector de 877 templates).
2. Implementar `vie/semantic_module_mapper.py` (mapeo a 103 modulos nativos).
3. Implementar `vie/layout_composer.py` (selector de layouts asimetricos).
4. Implementar `vie/narrative_composer.py` (expansion de briefs a 6-8 secciones).
5. Refactorizar `vie/section.py` para usar los 4 componentes nuevos en `_build_designer_section()`.
6. Actualizar `vie/engine.py` para llamar NarrativeComposer antes de SectionBuilder.
7. Reescribir los 5 briefs con copy real, imagenes reales, y campos semanticos completos.
8. Generar 5 plans con VIE: `python DAW_bundle/vie/cli.py --brief-file=...`.
9. Desplegar: `php DAW_bundle/divi-agentic-core/bin/build_page.php --def=... --deploy`.
10. Auditar volcados: guardar `post_content` de cada pagina en `content_state/local/`.
11. Correr tests: `python -m pytest DAW_bundle/tests/ -v`.
12. Verificar metricas de exito A-E en los volcados.
13. Si falla cualquier metrica, iterar desde paso 7 (briefs) o paso 3 (layout composer).

---

## 11. Fracaso y consecuencias

Si despues de ejecutar esta instruccion:
- Las 5 paginas siguen usando el mismo layout mecanico (4_4, 1_2,1_2, 1_4,1_4)
- No hay modulos nativos variados (image, testimonial, pricing, slider, map, contact-form)
- No hay layouts asimetricos (2_5+3_5, imagen superpuesta a texto, broken grid)
- Los efectos premium (glass, grain, orb) desaparecieron o se rompieron
- Los tests fallan

Entonces la implementacion ha fracasado. No hay justificacion tecnica valida. El problema es de ejecucion, no de arquitectura.

La arquitectura descrita aqui ES suficiente. Los activos del proyecto YA EXISTEN. La unica variable es la disciplina de implementacion.

---

## 12. Firma

Esta instruccion es el contrato de ejecucion. Cualquier desviacion requiere aprobacion explicita.
