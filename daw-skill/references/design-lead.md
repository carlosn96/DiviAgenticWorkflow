# DAW Module: Design Lead — Research & Direction

## Rol
El Design Lead se activa **después** del plan semántico del Arquitecto (Phase 1) y **antes** del mapeo visual del Diseñador (Phase 2). Su función: investigar dirección visual moderna, validar el plan contra las 6 Leyes de Calidad, y hacer handoff formal al Diseñador con un Design Brief escrito.

> El DAW es autocontenido en el bundle local. Para consultas profundas sobre tendencias, paletas o patrones específicos, cargar el skill global `ui-ux-pro-max` (no referencia por path — se resuelve por nombre en la configuración del agente).

---

## ⛔ PREREQUISITO DE HANDOFF — 6 Leyes de Calidad Autónoma

> [!CAUTION]
> Estas 6 leyes se validan **ANTES** de escribir una sola línea de JSON. Si cualquier ley no se satisface en el plan, el Design Lead propone alternativa y re-valida. Son un bloqueante, no una sugerencia.

> [!WARNING]
> ⚠️ **Los presets citados en este documento (`section:hero-dark`, `text:display-xl`, `module:feature-card`, `transform:hover-lift`, …) NO existen en `divitheme.json` hoy** (`"presets": []`). Las Leyes expresan **intenciones de diseño**; el Diseñador las implementa con **decoration nativa + tokens `{{design:color:*}}`/`{{design:font:*}}`/`{{design:space:*}}`**, no con presets. Verificar siempre contra `site/<DAW_SITE>/design-system/divitheme.json` antes de usar cualquier preset.

Estas leyes se aplican **siempre**, sin importar el proyecto ni el design system cargado. Son el piso mínimo que separa un diseño profesional de uno genérico.

### Ley 1 — Contraste de Sección ⛔ BLOQUEANTE
Nunca 2 secciones consecutivas del mismo color de fondo. El ritmo visual **obligatorio** es alternar profundidad. Documentar la secuencia completa de fondos (tokens `{{design:color:*}}` de `_design_vars.json`, p.ej. `surface-deep`/`surface-light`/`surface-white`) antes del handoff:

```
Ejemplo correcto (tokens del design system):
  sec-1: {{design:color:surface-deep}}     ← oscuro
  sec-2: {{design:color:surface-light}}    ← claro
  sec-3: {{design:color:surface-white}}    ← blanco / tarjetas
  sec-4: {{design:color:surface-mid}}      ← oscuro alternativo
  sec-5: {{design:color:surface-light}}    ← claro cierre
```

El ojo necesita puntos de respiro y sorpresa. Una página toda blanca es invisible. Una página toda oscura es opresiva.

### Ley 2 — Titular Dominante ⛔ BLOQUEANTE
El H1 del hero **SIEMPRE** es dominante tipográficamente: un bloque `divi/heading` o `divi/text` con `headingFont.h1` (o `bodyFont`) a tamaño **≥ 2rem desktop mínimo (intención: ~XL/72px), escala responsive -35/40%** (tokens `{{design:font:*}}`/`{{design:color:*}}`). Si el design system no tiene una fuente `display`, usar la fuente `ui` con `weight: 800`. El titular es el primer punto de contacto visual — debe ser imposible de ignorar. (El lint `lint_page_def.php` Ley 2 valida ≥2rem en la primera sección.)

No se acepta un hero sin titular XL dominante. Si el plan semántico no lo incluye, agregar uno.

### Ley 3 — Espacio Negativo Mínimo ⛔ BLOQUEANTE
- Todas las secciones: `padding-top` y `padding-bottom` mínimo de `{{design:space:2xl}}` (96px).
- Todas las tarjetas y cards: `padding` interno mínimo de `{{design:space:lg}}` (40px).
- Sin excepciones. El espacio negativo es lo que hace que un diseño respire y se vea premium.

El Diseñador debe declarar estos valores en `decoration.spacing` de las secciones y módulos respectivos.

### Ley 4 — Micro-interacción en Todo Elemento Clickeable ⛔ BLOQUEANTE
Todo elemento interactivo documenta un estado hover antes del handoff al Diseñador. El Design Lead lista explícitamente qué elementos tienen hover y cómo:

| Tipo de elemento | Comportamiento hover |
|---|---|
| Botones primarios | `decoration.button.hover` (color más oscuro / `{{design:color:*}}`) + `decoration.transform.hover` |
| Cards / Tarjetas | `decoration.transform.hover` (translateY -8px + sombra expandida) |
| Cards de features | `decoration.transform.hover` (translateY + sombra) — sin presets |
| Cards glass | `decoration.transform.hover` (translateY + sombra) — sin presets |
| Imágenes enlazadas | `decoration.transform.hover` (scale 1.03) |

Si el plan semántico incluye tarjetas o botones sin hover documentado, el Design Lead los agrega antes del handoff.

### Ley 5 — Anclaje Visual por Sección ⛔ BLOQUEANTE
Cada sección tiene **un** elemento que domina y ancla la mirada. El Design Lead lo identifica explícitamente para cada sección:

| Tipo de sección | Elemento ancla |
|---|---|
| Hero | El titular XL (`headingFont.h1` ≥ 2rem desktop) |
| Stats / Números | El número en escala masiva (≥ 48px, `{{design:color:*}}` acento) |
| Features | El ícono o imagen de la card |
| Testimonial | La cita en serif itálica (bodyFont serif, tamaño grande) |
| CTA Final | El botón grande y aislado, con espacio negativo masivo alrededor |
| About / Content | La imagen o elemento visual dominante en la columna visual |

Si una sección no tiene ancla identificada, el Diseñador no sabe qué debe dominar. Definirlo aquí.

### Ley 6 — Escala Responsiva Declarada ⛔ BLOQUEANTE
Toda tipografía hero declara los 3 breakpoints explícitamente. La reducción es del 35-40%:

```
H1 hero:    desktop: 72px → tablet: 44px → mobile: 30px
H2 sección: desktop: 40px → tablet: 30px → mobile: 24px
H3 card:    desktop: 24px → tablet: 20px → mobile: 18px
```

El Diseñador implementa estos valores en `headingFont.desktop/tablet/phone.value.size`. Sin estos valores declarados, el JSON produce tipografía no responsive.

---

## Anti-patrones Específicos (Vetados)

| Anti-patrón | Alternativa DAW Premium |
|-------------|------------------------|
| Colores de acento como fondo de secciones | Fondos vía tokens `{{design:color:surface-*}}` (Ley 1). `accent` solo en CTAs y elementos de énfasis |
| Emojis como iconos | Usar iconos Divi nativos `&#xe03a;` via `divi/blurb` o SVG en `divi/image` |
| Hero con slider genérico y texto pequeño | Hero tipográfico con `divi/heading`/`divi/text` XL (≥2rem) y padding masivo |
| Texto gris sobre gris | Contraste estricto mínimo 4.5:1. Verificar con tokens `{{design:color:*}}` |
| Cards planas sin fondo, sombra ni radio | decoration nativa: `background` (surface-white) + `border` radio + `shadow` (no existen presets `module:feature-card`/`glass-card` en `divitheme.json`) |
| Todas las secciones en fondo blanco | Alternancia obligatoria (Ley 1) |
| `divi/text` con headingFont.h1 para el H1 | Correcto si usa `divi/text` con `headingFont.h1` + decoration (es el patrón real). NO usar `divi/code` con `<h1>` inline — el bloque correcto es `divi/heading` o `divi/text` con `headingFont` |

---

## 1. Cuándo se Activa

El Design Lead participa en **cualquier página pública**, incluyendo:
- Páginas nuevas de cualquier tipo (homepage, landing, servicios, about, contacto, blog, WooCommerce, portfolio)
- Rediseño visual significativo de páginas existentes
- Duda sobre dirección estética o UX
- Necesidad de validar contra estándares modernos

**No se activa** para páginas de administración interna o cambios puramente funcionales sin impacto visual.

---

## 2. Flujo de Trabajo del Design Lead

```
Plan Semántico (Arquitecto)
       ↓
┌──────────────────────────────────────────────────┐
│  Design Lead                                     │
│  2a. Investigar dirección visual                 │
│  2b. Validar 6 Leyes (BLOQUEANTE)                │
│  2c. Documentar decisiones                       │
│  2d. Escribir Design Brief → handoff al Designer │
└──────────────────────────────────────────────────┘
       ↓
Schema JSON (Diseñador) — solo si el Design Brief está escrito
```

### 2a. Investigar Dirección Visual

Para cada proyecto, determinar:

| Dimensión | Pregunta | Fuente |
|-----------|----------|--------|
| Estilo | ¿Qué estilo visual se alinea con el propósito? | §3 de este documento |
| Layout | ¿Qué patrón de landing usar? | §4 de este documento |
| UX Crítico | ¿Qué principios no pueden romperse? | Las 6 Leyes al inicio de este documento |
| Referencias | ¿Existen referentes externos? | Cargar `ui-ux-pro-max` skill |

### 2b. Validar las 6 Leyes

Completar el checklist de las 6 Leyes (sección de PREREQUISITO). Si cualquier ley falla, **detener el flujo**, proponer alternativa documentada, y re-validar.

### 2c. Documentar Decisiones

Cada decisión de diseño no trivial debe registrarse con:

```json
{
  "decision": "Usar slider en hero en vez de imagen fija",
  "fundamento": "Múltiples mensajes institucionales; slider permite rotar sin perder jerarquía visual",
  "alternativa": "Hero con video background (descartado: performance)",
  "ux_validacion": "Slider con controles visibles, autoplay con pausa, 2 slides máximo"
}
```

### 2d. Handoff a Designer — Design Brief

El Design Brief es el artefacto de salida de la Fase 2. Es **obligatorio** escribirlo antes de pasar a la Fase 3. Formato mínimo:

```
=== DESIGN BRIEF: <nombre de página> ===

Estilo visual: <editorial / modern / premium / minimal / dramatic>
Tono: <descripciones breves del tono visual>

ALTERNANCIA DE FONDOS (Ley 1 ✓):
  sec-1: <token de fondo — {{design:color:surface-deep}} / surface-light / surface-white, alternando>
  sec-2: <token de fondo distinto>
  ...

> **Variable-availability gate (antes de definir tokens en el brief):** los tokens (`{{design:color:*}}`, `{{design:font:*}}`, `{{design:space:*}}`) SOLO existen si `wp brand sync` los registró como gcids/gvids. Verificar: `.\wp agentic global_colors status` y `.\wp agentic global_colors list`. Si el bucket necesario está vacío (sin colores/espacios/fuentes), **preguntar al usuario**: *(a)* generar el sistema de variables (recomendado — `wp brand sync` ya lo hace desde `_design_vars.json`) o *(b)* construir con valores inline. Nunca inventar nombres de token (`{{design:color:navy-700}}`) que no estén en `_design_vars.json` — se resolverían como literal inválido. Nombres exactos en `site/<DAW_SITE>/brand/_design_vars.json` (keys snake_case → kebab-case).

TITULAR HERO (Ley 2 ✓):
  Bloque: divi/heading (headingFont.h1, tamaño XL desktop ~72px con escala responsive)
  Contenido: "<texto del titular>"

ESPACIO NEGATIVO (Ley 3 ✓):
  Secciones: padding mínimo {{design:space:2xl}} (96px)
  Cards: padding mínimo {{design:space:lg}} (40px)

HOVER DOCUMENTADO (Ley 4 ✓):
  - Botones primarios: decoration hover en button.decoration (color más oscuro) + transform
  - Cards de features: decoration hover (sombra expandida + translateY)
  - [otros elementos interactivos]

ANCLAS VISUALES (Ley 5 ✓):
  - sec-1 hero: titular XL (headingFont.h1 ≥ 2rem)
  - sec-2 features: íconos de blurb
  - [ancla por sección]

ESCALA RESPONSIVA (Ley 6 ✓):
  H1: desktop 72px / tablet 44px / mobile 30px
  H2: desktop 40px / tablet 30px / mobile 24px

DECISIONES:
  - <decisión>: <fundamento>

RESTRICCIONES PARA EL DISEÑADOR:
  - <lista de lo que no debe hacerse>
```

---

## 3. Checklist UX Crítica (No Negociable)

Basada en las guías de prioridad CRITICAL y HIGH de ui-ux-pro-max, adaptadas para Divi 5 / WordPress. Se verifica durante 2b (validación de leyes) y se confirma en el Design Brief.

### Accesibilidad (CRÍTICO)
- [ ] Contraste de color: texto body sobre fondo claro ≥ 4.5:1
- [ ] Contraste de color: texto sobre fondo oscuro (hero) ≥ 4.5:1
- [ ] Los botones CTAs tienen contraste suficiente contra su fondo
- [ ] No usar color como único indicador de estado
- [ ] Los enlaces son distinguibles del texto body (no solo por color)

### Touch e Interacción (CRÍTICO)
- [ ] Botones CTAs tienen padding suficiente (≥ 44px altura)
- [ ] Los slides/toggles son operables por click/tap (no solo hover)
- [ ] Hay feedback visual en hover (botones: cambio de opacidad/color)
- [ ] Slider tiene dots + arrows de navegación visibles

### Tipografía y Color (ALTA)
- [ ] Body text usa 16px+ en mobile (evita zoom automático iOS)
- [ ] Línea de texto: 60-75 caracteres por línea máximo
- [ ] Escala tipográfica coherente: h1(48)→h2(36)→h3→body(18/16)
- [ ] Jerarquía visual clara: tamaño + peso + espaciado
- [ ] Los tokens semánticos están documentados y son consistentes

### Layout (ALTA)
- [ ] Sin scroll horizontal en mobile
- [ ] Espaciado entre secciones consistente (60-80px)
- [ ] Cards tienen jerarquía visual clara (sombra/borde/fondo)
- [ ] Los CTAs primarios son visualmente dominantes sobre secundarios

---

## 4. Catálogo de Páginas — Patrones de Composición

El DAW puede generar cualquier tipo de página. El Design Lead elige el patrón correcto según el objetivo de negocio:

### Homepage / Portada
```
Hero (tipográfico o con imagen) → Trust/Stats bar → Features Grid → About → Testimonial → CTA Final
```
- Preset de sección alternante: `hero-dark` → `light` → `white` → `dark` → `light`
- Bloques clave: `divi/heading` (titular XL), `divi/number-counter`, `divi/blurb`, `divi/testimonial`

### Landing de Servicio / Producto
```
Hero con CTA → Beneficios → Social Proof (testimonios) → Pricing o FAQ → CTA Final
```
- Bloques: `divi/cta`, `divi/blurb`, `divi/testimonial`, `divi/toggle` (FAQ), `divi/pricing-table`

### About / Acerca de
```
Hero tipográfico → Misión/Valores → Equipo → Stats → CTA
```
- Bloques: `divi/heading`, `divi/image`, `divi/team-member`, `divi/blurb`, `divi/button`

### Contacto
```
Hero mínimo → Formulario + Mapa → FAQ → CTA
```
- Bloques: `divi/heading`, `divi/map`, `divi/contact-form` + `divi/contact-field`, `divi/toggle`

### Blog / Archivo de Publicaciones
```
Hero mínimo → Grid de Posts → CTA Suscripción
```
- Bloques: `divi/blog` (type: grid, show_excerpt: on), `divi/cta`

### Tienda WooCommerce
```
Hero promo (banner de oferta) → Grid de Productos → Destacados → CTA
```
- Bloques: `divi/woocommerce-products`, `divi/shop`, `divi/cta`

### Portfolio / Proyectos
```
Hero tipográfico → Grid Filtrable de Proyectos → CTA Contacto
```
- Bloques: `divi/filterable-portfolio` o `divi/gallery`, `divi/button`

### Landing Evento / Webinar
```
Hero con countdown → Speakers → Agenda → Formulario de registro → FAQ
```
- Bloques: `divi/countdown-timer`, `divi/team-member`, `divi/toggle`, `divi/contact-form`

---

## 5. Cómo Usar ui-ux-pro-max (skill global — fuera del bundle, Opcional)

Si el Design Lead necesita profundizar en un área específica:

```
El skill ui-ux-pro-max contiene:
  - 50+ estilos visuales (glassmorphism, minimalism, editorial, etc.)
  - 99 guías UX organizadas por prioridad (CRITICAL→LOW)
  - Paletas de color por tipo de producto
  - Font pairings por personalidad
  - Patrones de landing page

Para consultar un dominio específico:
  §4 Style Selection (HIGH) → estilo por tipo de producto
  §5 Layout & Responsive (HIGH) → patrones de landing
  §6 Typography & Color (MEDIUM) → escalas, contrastes
  §7 Animation (MEDIUM) → timing, easing
  §9 Navigation Patterns (HIGH) → estructura de navegación
```

---

## 6. Ejemplo de Design Brief Completo

```
=== DESIGN BRIEF: Inicio (Rediseño v3) ===

Estilo visual: Moderno Ultra-Premium
Tono: Austero, erudito, confianza institucional sin frivolidad

ALTERNANCIA DE FONDOS (Ley 1 ✓):
  sec-1: section hero oscuro (surface-deep)       (hero tipográfico oscuro)
  sec-2: barra de stats, oscuro suave             (surface-mid)
  sec-3: features grid, claro cálido              (surface-light)
  sec-4: about / imagen, blanco limpio            (surface-white)
  sec-5: testimonials, oscuro                     (surface-deep)
  sec-6: CTA final, impacto máximo                (accent)

TITULAR HERO (Ley 2 ✓):
  Bloque: divi/heading o divi/text (headingFont.h1), tamaño XL (≥2rem desktop)
  Contenido: "Bibliotheca San Pablo"

ESPACIO NEGATIVO (Ley 3 ✓):
  Secciones: decoration.spacing padding top/bottom 96px
  Cards feature-card: decoration.spacing padding 40px

HOVER DOCUMENTADO (Ley 4 ✓):
  - Botones: button.decoration hover (accent_hover) + transform
  - Feature cards: decoration hover sombra expandida + translateY
  - Testimonial cards: decoration hover scale 1.03

ANCLAS VISUALES (Ley 5 ✓):
  - Hero: titular masivo (72px)
  - Stats bar: números en escala grande (48px+)
  - Features: íconos Divi en cada blurb
  - Testimonials: cita en serif itálica
  - CTA: botón aislado con padding masivo

ESCALA RESPONSIVA (Ley 6 ✓):
  H1 (hero): desktop 72px / tablet 42px / mobile 28px
  H2 (headline): desktop 40px / tablet 30px / mobile 22px

DECISIONES:
  - Hero dinámico tipográfico en vez de slider: impacto inmediato, performance.
  - Cards con hover translateY: micro-interacciones de calidad percibida.

RESTRICCIONES PARA EL DISEÑADOR:
  - No hex hardcodeados. Todo {{design:color:*}}.
  - No divi/placeholder en ninguna sección.
  - No catálogo como fuente de estructura (solo proporciones si se consulta).
  - No et_pb_*.
```

---

## 7. Design Quality Gate (Brand Level)

Las 6 Leyes validan **página** (layout, alternancia, hover, anclas). El brand level (colores, fuentes, escalas, radios) se valida automáticamente vía `Design_Validator` antes de `wp brand sync`:

| Check | Regla |
|-------|-------|
| Contraste WCAG AAA | Body text ≥ 7:1, large text ≥ 4.5:1 |
| Heading scale | Progresión armónica ratio ~1.25 |
| Spacing scale | Progresión armónica ratio ~1.5 |
| Radius scale | Progresión armónica ratio ~2.0 |
| Font pairing | Dos fuentes de misma categoría = fail |
| Valores requeridos | Presentes y con formato válido |

```powershell
# Verificar antes de sincronizar
wp brand validate <slug>

# Sync respeta el gate — falla si validate no pasa
wp brand sync <slug>

# Bypass explícito
wp brand sync <slug> --force
```

El Design Lead no necesita correr esto manualmente. `Brand_Sync_Handler` lo ejecuta automáticamente. Si falla, el sync se aborta con instrucciones.
