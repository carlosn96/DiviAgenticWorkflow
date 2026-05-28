# DAW Module: Design Lead — Research & Direction

## Rol
El Design Lead se activa **después** del plan semántico del Arquitecto (Phase 1) y **antes** del mapeo visual del Diseñador (Phase 2). Su función es investigar direcciones de diseño modernas, validar decisiones contra principios UX, y documentar la intención visual que el Diseñador convertirá en JSON.

> El DAW es autocontenido en el bundle local de `divitheme`. Para consultas profundas sobre tendencias, paletas o patrones específicos, cargar el skill [`ui-ux-pro-max`](ui-ux-pro-max/SKILL.md) desde `DAW_bundle/ui-ux-pro-max/`.

---

## 1. Cuándo se Activa

El Design Lead participa en **cualquier página pública**, incluyendo:
- Páginas nuevas de cualquier tipo (homepage, landing, servicios, about, contacto, blog, WooCommerce, portfolio)
- Rediseiño visual significativo de páginas existentes
- Duda sobre dirección estética o UX
- Necesidad de validar contra estándares modernos

**No se activa** para páginas de administración interna o cambios puramente funcionales sin impacto visual.

---

## 2. Flujo de Trabajo del Design Lead

```
Plan Semántico (Arquitecto)
       ↓
┌──────────────────────────────┐
│  Design Lead                 │
│  2a. Investigar dirección    │
│  2b. Validar contra UX       │
│  2c. Documentar decisiones   │
│  2d. Handoff a Designer      │
└──────────────────────────────┘
       ↓
Schema JSON (Diseñador)
```

### 2a. Investigar Dirección Visual

Para cada proyecto, determinar:

| Dimensión | Pregunta | Fuente |
|-----------|----------|--------|
| Estilo | ¿Qué estilo visual se alinea con el propósito? | §3 de este documento |
| Layout | ¿Qué patrón de landing usar? | §4 de este documento |
| UX Crítico | ¿Qué principios no pueden romperse? | §5 de este documento |
| Referencias | ¿Existen referentes externos? | Cargar `ui-ux-pro-max` skill |

### 2b. Validar Contra Principios UX

Usar la checklist de §5 como filtro. Si el plan semántico propone algo que viola un principio crítico, el Design Lead debe **detener el flujo** y proponer alternativa documentada.

### 2c. Documentar Decisiones

Cada decisión de diseño debe registrarse con:

```json
{
  "decision": "Usar slider en hero en vez de imagen fija",
  "fundamento": "Múltiples mensajes institucionales; slider permite rotar sin perder jerarquía visual",
  "alternativa": "Hero con video background (descartado: performance)",
  "ux_validacion": "Slider con controles visibles, autoplay con pausa, 2 slides máximo"
}
```

### 2d. Handoff a Designer

Entregar al Diseñador:
1. **Dirección visual** (estilo, tono, referencias)
2. **UX constraints** (lo que no debe romperse)
3. **Decisiones documentadas** (para que el JSON las refleje)

---

## 3. Piso de Calidad Autónomo (Siempre Activo)

Estas 6 leyes se aplican **siempre**, sin importar el proyecto ni el design system cargado. Son el piso mínimo que separa un diseño profesional de uno genérico.

### Ley 1 — Contraste de Sección (Obligatorio)
Nunca 2 secciones consecutivas del mismo color de fondo. El ritmo visual **obligatorio** es alternar profundidad:
- `surface-deep` → `surface-light` → `surface-deep` 
- `surface-light` → `surface-white` → `surface-dark`

El ojo necesita puntos de respiro y sorpresa. Una página toda blanca es invisible. Una página toda oscura es opresiva.

### Ley 2 — Titular Dominante (Obligatorio)
El H1 del hero **SIEMPRE** usa el preset `text:display-xl` (72px desktop mínimo). Si el design system no tiene una fuente `display`, usar la fuente `ui` con `weight: 800`. El titular es el primer punto de contacto visual — debe ser imposible de ignorar.

### Ley 3 — Espacio Negativo Mínimo (Obligatorio)
- Todas las secciones: `padding-top` y `padding-bottom` mínimo de `{{design:space:2xl}}` (96px).
- Todas las tarjetas y cards: `padding` interno mínimo de `{{design:space:lg}}` (40px).
- Sin excepciones. El espacio negativo es lo que hace que un diseño respire y se vea premium.

### Ley 4 — Micro-interacción en Todo Elemento Clickeable (Obligatorio)
Todo elemento interactivo documenta un estado hover antes del handoff al Diseñador:
- **Botones**: cambio de color de fondo (usar `accent-hover`) o reducir opacidad al 85%.
- **Cards / Tarjetas**: `translateY(-8px)` + expansión de sombra.
- **Imágenes enlazadas**: escala suave `scale(1.03)`.

### Ley 5 — Anclaje Visual por Sección (Obligatorio)
Cada sección tiene **un** elemento que domina y ancla la mirada. Sin anclas, una sección se ve genérica.
- Hero → El titular enorme
- Stats → El número en escala masiva (48px+)
- Features → El ícono o imagen de la card
- Testimonial → La cita en serif itálica
- CTA Final → El botón grande y aislado

### Ley 6 — Escala Responsiva Declarada (Obligatorio)
Toda tipografía hero declara los 3 breakpoints. La reducción es del 35-40%:
- Desktop: 72px → Tablet: 44px → Mobile: 30px
- Desktop: 40px → Tablet: 30px → Mobile: 24px

### Anti-patrones Específicos

| Anti-patrón Básico | Alternativa DAW Premium |
|-------------|-----------------|
| Colores de acento como fondo de secciones | Solo `surface-*` para fondos. `accent` solo en CTAs. |
| Emojis como iconos | Usar iconos Divi nativos o SVG via `divi/blurb` |
| Hero con slider genérico y texto pequeño | Hero tipográfico con `display-xl` y padding masivo |
| Texto gris sobre gris | Contraste estricto mínimo 4.5:1 siempre |
| Cards planas sin fondo, sombra ni radio | Preset `module:feature-card` con sombra masiva |
| Todas las secciones en fondo blanco | Alternar obligatoriamente (Ley 1) |

---

## 4. Catálogo de Páginas — Patrones de Composición

El DAW puede generar cualquier tipo de página. El Design Lead elige el patrón correcto según el objetivo de negocio:

### Homepage / Portada
```
Hero (tipográfico o con imagen) → Trust/Stats bar → Features Grid → About → Testimonial → CTA Final
```
- Preset de sección alternante: `hero-dark` → `light` → `white` → `dark` → `light`
- Bloques clave: `divi/text` (titular XL), `divi/number-counter`, `divi/blurb`, `divi/testimonial`

### Landing de Conversión (sin navbar)
```
Hero con CTA → Problema que resuelve → Solución (features) → Social Proof → Pricing → FAQ → CTA Final
```
- Todo el flujo guía al usuario a una sola acción. Eliminar distractores.
- Bloques: `divi/cta`, `divi/blurb`, `divi/testimonial`, `divi/toggle` (FAQ), `divi/pricing-table`

### Página de Servicios
```
Hero compacto → Intro + diferenciador → Grid de servicios (cards) → Proceso/Cómo trabajamos → Casos/Proyectos → CTA
```
- Usar `column_structure: "1_3,1_3,1_3"` para el grid de servicios con `module:feature-card`
- Bloques: `divi/blurb`, `divi/number-counter`, `divi/blog` (casos), `divi/cta`

### Página About / Nosotros
```
Hero tipográfico (statement de marca) → Historia (texto + imagen alternados) → Equipo → Valores → CTA
```
- El hero usa solo tipografía: `display-xl` centrado en fondo `surface-deep`. Sin imagen de fondo.
- Bloques: `divi/text`, `divi/image`, `divi/team-member`, `divi/blurb`, `divi/button`

### Página de Contacto
```
Hero mínimo → Datos de contacto + Mapa → Formulario → FAQ (opcional)
```
- Hero compacto: 50% del padding del hero principal. Solo H1 + subtítulo.
- Bloques: `divi/text`, `divi/map`, `divi/contact-form` + `divi/contact-field`, `divi/toggle`

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

### Página de Producto (WooCommerce single)
```
Galería + Info de producto + CTA → Descripción larga → Relacionados
```
- Bloques: `divi/woocommerce-product-image`, `divi/woocommerce-add-to-cart`, `divi/woocommerce-related-products`

---

## 5. CheckList UX Crítica (No Negociable)

Basada en las guías de prioridad CRITICAL y HIGH de ui-ux-pro-max, adaptadas para Divi 5 / WordPress:

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

## 6. Cómo Usar ui-ux-pro-max (en `DAW_bundle/ui-ux-pro-max/`, Opcional)

Si el Design Lead necesita profundizar en un área específica:

```bash
# Cargar el skill en el agente
# El skill ui-ux-pro-max contiene:
#   - 50+ estilos visuales (glassmorphism, minimalism, editorial, etc.)
#   - 99 guías UX organizadas por prioridad (CRITICAL→LOW)
#   - Paletas de color por tipo de producto
#   - Font pairings por personalidad
#   - Patrones de landing page

# Para consultar un dominio específico, cargar el skill y buscar en:
# §4 Style Selection (HIGH) → estilo por tipo de producto
# §5 Layout & Responsive (HIGH) → patrones de landing
# §6 Typography & Color (MEDIUM) → escalas, contrastes
# §7 Animation (MEDIUM) → timing, easing
# §9 Navigation Patterns (HIGH) → estructura de navegación
```

---

## 7. Ejemplo de Documentación de Design Lead

Para el proyecto "Inicio (Rediseño v3)" esto sería la salida del Design Lead:

```json
{
  "proyecto": "Inicio (Rediseño v3)",
  "direccion_visual": {
    "estilo": "Moderno Ultra-Premium",
    "tipografia_heroe": true,
    "paleta": "Depende estrictamente de los tokens del JSON. Superficies oscuras para impacto, acento solo para CTAs.",
    "efectos": "Sombras masivas muy difusas, padding 48px en cards, radius orgánico (24px)."
  },
  "ux_validaciones": {
    "contraste_hero": "Texto blanco sobre fondo oscuro = 11.2:1 ✓",
    "touch_targets": "CTAs con padding amplio ≥ 44px ✓",
    "sin_scroll_horizontal": "Sections con padding 5% lateral ✓"
  },
  "decisiones": [
    {
      "decision": "Hero dinámico con tipografía masiva en vez de slider estático aburrido",
      "fundamento": "Un diseño moderno requiere impacto inmediato. El slider reduce la legibilidad del hero typography.",
      "riesgo": "Ninguno, mejora UX."
    },
    {
      "decision": "Cards de features con hover translateY",
      "fundamento": "Micro-interacciones añaden valor premium percibido inmediato."
    }
  ],
  "handoff_designer": {
      "bloques_a_usar": ["divi/section", "divi/text", "divi/button"],
      "presets_disponibles": ["section:hero-dark", "module:card", "module:btn-primary"],
      "evitar": ["Fondos de colores altamente saturados masivos", "divi/code como comodín", "hex hardcodeados sin tokens {{design:*}}"]
  }
}
```
