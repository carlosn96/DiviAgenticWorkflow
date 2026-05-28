# DAW: Diccionario Completo de Bloques Divi 5

Archivo maestro de referencia para las Fases 1 (Arquitecto) y 2 (Diseñador).

> **Índice rápido:** [`references/blocks-index.json`](references/blocks-index.json) — 16 KB con slug, nombre, categoría y children de los 102 bloques.
> **Atributos detallados (bajo demanda):** Ejecutar `php DAW_bundle/divi-agentic-core/bin/extract-module-meta.php <slug>` para ver el schema completo de cualquier bloque (tipos, defaults, settings groups, render paths). Ej: `php DAW_bundle/divi-agentic-core/bin/extract-module-meta.php slide`.
> **Engine runtime:** El trait `Module_Metadata` en `DAW_bundle/divi-agentic-core` lee `data/_all_modules_metadata.php` directamente para compilar bloques con paths de serialización correctos.

El Arquitecto consulta este diccionario para **discernir el tipo de componente correcto** según el elemento semántico que necesita. El Diseñador lo usa para **construir el JSON Schema** con los atributos exactos que cada bloque espera.

---

## Índice de Decisión Semántica

Usa esta tabla cuando tengas un elemento semántico y necesites saber qué bloque `divi/*` usar:

| Elemento semántico | Bloque Divi 5 | Alternativas |
| :--- | :--- | :--- |
| Titular principal (H1) | `divi/text` con `headingFont.h1` | `divi/heading` |
| Subtítulo / H2 | `divi/text` con `headingFont.h2` | `divi/heading` |
| Párrafo / cuerpo | `divi/text` con `bodyFont` | — |
| Eyebrow / overline | `divi/text` con `headingFont.h2` (gold, uppercase) | — |
| CTA / botón | `divi/button` (nativo) | `divi/code` con `<a>` HTML |
| Imagen única | `divi/image` | — |
| Imagen + texto (feature) | `divi/blurb` | `divi/text` con HTML |
| Contador numérico animado | `divi/number-counter` | `divi/circle-counter` |
| Ícono decorativo | `divi/icon` | `divi/code` con HTML |
| Línea divisoria | `divi/divider` | `divi/code` con `<hr>` |
| Video embed | `divi/video` | `divi/code` con iframe |
| Galería de imágenes | `divi/gallery` | — |
| Tarjeta / card | `divi/text` con `decoration` | `divi/blurb` si tiene icono |
| Acordeón / FAQ | `divi/accordion` con hijos `divi/accordion-item` | `divi/toggle` (ítem único) |
| Slideshow / carrusel | `divi/slider` con hijos `divi/slide` | — |
| Testimonial | `divi/testimonial` | `divi/text` con HTML |
| Team member | `divi/team-member` | `divi/text` con HTML |
| Pricing table | `divi/pricing-table` | — |
| Barra de búsqueda | `divi/search` | — |
| Mapa | `divi/map` | — |
| Sidebar / widgets | `divi/sidebar` | — |
| Menú de navegación | `divi/menu` | `divi/fullwidth-menu` |
| Formulario de contacto | `divi/contact-form` + `divi/contact-field` hijos | `divi/contact-form-7` |
| Blog grid | `divi/blog` | — |
| Login | `divi/login` | — |
| Social links | `divi/social-media-follow` + `divi/social-media-follow-network` hijos | — |
| Icon list | `divi/icon-list` + `divi/icon-list-item` hijos | — |
| Hero fullwidth | `divi/fullwidth-header` | `divi/section` con decoration + `divi/text` |
| Portafolio | `divi/portfolio` | `divi/filterable-portfolio` |
| Post dinámico (título/contenido) | `divi/post-title` / `divi/post-content` | — |
| HTML libre / shortcode | `divi/code` | `divi/shortcode-module` |
| Group / contenedor | `divi/group` | `divi/section` |

---

## 1. Bloques Estructurales

### divi/section
**Contenedor raíz de toda página. Cada página tiene 1+ sections.**

| Atributo | Tipo | Obligatorio | Descripción |
| :--- | :--- | :--- | :--- |
| `presets` | `string[]` | No | `["section:hero-image-dark"]`, `["section:light"]`, `["section:cta-epic"]` |
| `decoration` | object | No | Background, spacing, border, animation del contenedor |
| `background_image` | string | No | URL de imagen de fondo |
| `bg_gradient` | object | No | Shorthand para gradient overlay. Ej: `{ "type": "linear", "direction": "135deg", "overlaysImage": "on", "stops": [{ "color": "rgba(0,0,0,0.8)", "position": "0%" }, { "color": "rgba(0,0,0,0)", "position": "100%" }] }` |
| `bg_size` | string | No | "cover", "contain", "initial". (Solo si hay background_image) |
| `bg_position` | string | No | "center center", "center top", etc. (Solo si hay background_image) |
| `parallax` | string | No | `"on"` o `"off"` |
| `module_class` | string | No | Clases CSS adicionales |
| `rows` | array | Sí | Array de `divi/row` |

```json
{
  "presets": ["section:hero-dark"],
  "background_image": "{{SITE_URL}}/wp-content/uploads/hero.jpg",
  "rows": []
}
```

### divi/row
**Fila que contiene columnas. Puede tener column_structure responsivo.**

| Atributo | Tipo | Obligatorio | Descripción |
| :--- | :--- | :--- | :--- |
| `column_structure` | string o object | Sí | `"1_2,1_2"` o `{"desktop":"1_3,1_3,1_3","tablet":"1_2,1_2","phone":"4_4"}` |
| `decoration` | object | No | Layout, spacing, background |
| `columns` | array | Sí | Array de `divi/column` |

### divi/column
**Columna individual dentro de una row. El `type` determina el ancho.**

| Atributo | Tipo | Obligatorio | Descripción |
| :--- | :--- | :--- | :--- |
| `type` | string | Sí | `"1_2"`, `"1_3"`, `"2_3"`, `"1_4"`, `"3_4"`, `"4_4"`, `"1_1"` |
| `decoration` | object | No | Background, spacing, sizing individual |
| `modules` | array | Sí | Array de módulos (`divi/text`, `divi/image`, etc.) |

### divi/row-inner / divi/column-inner
**Sub-contenedores para anidar filas/columnas dentro de una columna.** Mismos atributos que row/column. Se usan cuando necesitas una sub-grid dentro de una columna.

---

## 2. Bloques de Contenido

### divi/text
**El bloque más versátil. Para texto enriquecido, títulos, párrafos, HTML.**

```json
{
  "module": "divi/text",
  "content": "<h1>T\u00edtulo <em>Principal</em></h1><p>Descripci\u00f3n.</p>",
  "headingFont": {
    "h1": { "font": { "desktop": { "value": { "fontFamily": "{{design:font:display}}", "color": "{{design:color:white}}", "size": "48px" } } } }
  },
  "bodyFont": {
    "body": { "font": { "desktop": { "value": { "fontFamily": "{{design:font:ui}}", "color": "{{design:color:text-secondary}}" } } } }
  },
  "decoration": { "background": { "desktop": { "value": { "color": "#FFFFFF" } } } }
}
```

| Atributo | Descripción |
| :--- | :--- |
| `content` | HTML del contenido |
| `headingFont` | Estilos de tipografía para headings (h1-h6) |
| `bodyFont` | Estilos de tipografía para body/párrafos |

### divi/code
**HTML libre. Úsalo cuando necesites markup que no encaja en otros bloques: botones con HTML inline, SVG, embeds, iframes.**

```json
{
  "module": "divi/code",
  "content": "<div class=\"custom-wrapper\"><a href=\"/tienda\" class=\"btn\">Explorar</a></div>"
}
```

### divi/heading
**Heading independiente. Similar a divi/text pero especializado para títulos.**

```json
{
  "module": "divi/heading",
  "content": "T\u00edtulo de la secci\u00f3n",
  "headingFont": {
    "h2": { "font": { "desktop": { "value": { "fontFamily": "{{design:font:display}}", "size": "36px" } } } }
  }
}
```

### divi/image
**Imagen con src y alt. Soporta decoration (bordes, sombras).**

```json
{
  "module": "divi/image",
  "src": "{{SITE_URL}}/wp-content/uploads/imagen.jpg",
  "alt": "Descripci\u00f3n de la imagen",
  "decoration": { "border": { "desktop": { "value": { "radius": { "sync": "on", "topLeft": "8px", "topRight": "8px", "bottomRight": "8px", "bottomLeft": "8px" } } } } }
}
```

### divi/button
**Botón nativo Divi con estilos desde decoration.button.**

```json
{
  "module": "divi/button",
  "button_text": "Explorar tienda",
  "button_url": "/tienda",
  "decoration": {
    "button": { "desktop": { "value": { "backgroundColor": "{{design:color:red}}", "textColor": "#FFFFFF", "borderRadius": "50px" } } }
  }
}
```

### divi/video
**Video embed (YouTube URL o MP4).**

```json
{
  "module": "divi/video",
  "src": "https://www.youtube.com/watch?v=VIDEO_ID",
  "webm": ""
}
```

### divi/audio
**Audio embed.** Mismos atributos que video.

### divi/icon
**Ícono decorativo standalone.**

```json
{
  "module": "divi/icon",
  "icon": "&#x1F4D6;",
  "link": "",
  "link_url": ""
}
```

### divi/divider
**Línea separadora. Sin contenido textual.**

```json
{
  "module": "divi/divider",
  "show": "on"
}
```

### divi/gallery
**Galería de imágenes (grid o slider).**

```json
{
  "module": "divi/gallery",
  "gallery_ids": [123, 456, 789],
  "fullwidth": "off"
}
```

---

## 3. Bloques Interactivos

### divi/toggle
**Sección expandible individual (acordeón de 1 ítem).**

```json
{
  "module": "divi/toggle",
  "title": "Pregunta frecuente",
  "content": "<p>Respuesta detallada aqu\u00ed.</p>"
}
```

### divi/accordion
**Contenedor padre de múltiples accordion-item.**

```json
{
  "module": "divi/accordion",
  "children": [
    { "module": "divi/accordion-item", "title": "Pregunta 1", "content": "<p>Respuesta 1</p>" },
    { "module": "divi/accordion-item", "title": "Pregunta 2", "content": "<p>Respuesta 2</p>" }
  ]
}
```

### divi/accordion-item
**Item individual de acordeón.** Usar dentro de `children` de `divi/accordion`.

| Atributo | Descripción |
| :--- | :--- |
| `title` | Texto del título del panel |
| `content` | HTML del contenido expandible |
| `src` | Imagen opcional |

### divi/tabs / divi/tab
**Contenedor de tabs con hijos tab.**

```json
{
  "module": "divi/tabs",
  "children": [
    { "module": "divi/tab", "title": "Tab 1", "content": "<p>Contenido 1</p>" },
    { "module": "divi/tab", "title": "Tab 2", "content": "<p>Contenido 2</p>" }
  ]
}
```

### divi/dropdown
**Desplegable interactivo.**

```json
{
  "module": "divi/dropdown",
  "title": "Opci\u00f3n",
  "content": "<p>Contenido desplegable</p>"
}
```

### divi/contact-form
**Formulario de contacto con campos hijos.**

```json
{
  "module": "divi/contact-form",
  "email_to": "correo@ejemplo.com",
  "success_message": "Gracias por contactarnos",
  "submit_text": "Enviar mensaje",
  "children": [
    { "module": "divi/contact-field", "field_type": "text", "field_label": "Nombre", "required": true },
    { "module": "divi/contact-field", "field_type": "email", "field_label": "Correo", "required": true }
  ]
}
```

### divi/contact-field
| Atributo | Descripción |
| :--- | :--- |
| `field_type` | `"text"`, `"email"`, `"textarea"`, `"checkbox"`, `"radio"`, `"select"` |
| `field_label` | Texto de la etiqueta |
| `required` | `true` o `false` |
| `placeholder` | Texto de placeholder |

### divi/contact-form-7
**Integración con CF7.** Solo necesita el ID del formulario.

```json
{
  "module": "divi/contact-form-7",
  "form_id": "123"
}
```

### divi/menu / divi/fullwidth-menu
**Menú de navegación desde un menú de WordPress.**

```json
{
  "module": "divi/menu",
  "menu_id": 2
}
```

### divi/social-media-follow
**Contenedor de redes sociales.**

```json
{
  "module": "divi/social-media-follow",
  "children": [
    { "module": "divi/social-media-follow-network", "social_network": "facebook", "link": "https://facebook.com/marca" },
    { "module": "divi/social-media-follow-network", "social_network": "instagram", "link": "https://instagram.com/marca" }
  ]
}
```

### divi/social-media-follow-network
| Atributo | Descripción |
| :--- | :--- |
| `social_network` | `"facebook"`, `"twitter"`, `"instagram"`, `"youtube"`, `"linkedin"`, `"whatsapp"`, etc. |
| `link` | URL del perfil |
| `skype_url` | (opcional) |
| `skype_action` | `"call"` o `"chat"` |

---

## 4. Bloques de Diseño Visual

### divi/blurb
**Ícono/imagen + título + descripción.** Ideal para features, servicios, tarjetas con icono.

```json
{
  "module": "divi/blurb",
  "title": "Editorial",
  "content": "<p>M\u00e1s de 5,000 t\u00edtulos.</p>",
  "icon": "&#x1F4D6;",
  "decoration": {
    "background": { "desktop": { "value": { "color": "#FFFFFF" } } },
    "border": { "desktop": { "value": { "radius": { "sync": "on", "topLeft": "16px", "topRight": "16px", "bottomRight": "16px", "bottomLeft": "16px" } } } }
  }
}
```

| Atributo | Descripción |
| :--- | :--- |
| `title` | Texto del título |
| `content` | HTML de la descripción |
| `icon` | Clase CSS o entidad HTML del ícono |
| `src` | URL de imagen (alternativa al icono) |

### divi/number-counter
**Contador numérico animado.** Para estadísticas, métricas, datos.

```json
{
  "module": "divi/number-counter",
  "title": "A\u00f1os de experiencia",
  "number": "50+",
  "headingFont": {
    "h3": { "font": { "desktop": { "value": { "color": "{{design:color:ink}}", "size": "36px", "weight": "700" } } } }
  }
}
```

### divi/circle-counter
**Contador circular animado.** Mismos atributos que number-counter.

### divi/cta
**Call to Action.** Título + descripción + botón.

```json
{
  "module": "divi/cta",
  "title": "\u00bfListo para empezar?",
  "content": "<p>Cont\u00e1ctanos hoy.</p>",
  "button_text": "Cont\u00e1ctanos",
  "button_url": "/contacto"
}
```

### divi/testimonial
**Testimonial con cita, autor y foto.**

```json
{
  "module": "divi/testimonial",
  "content": "<p>Excelente servicio y atenci\u00f3n.</p>",
  "author": "Mar\u00eda Garc\u00eda",
  "src": "{{SITE_URL}}/uploads/foto.jpg"
}
```

### divi/team-member
**Tarjeta de miembro del equipo.**

```json
{
  "module": "divi/team-member",
  "name": "Juan P\u00e9rez",
  "position": "Director Editorial",
  "content": "<p>Biograf\u00eda del miembro.</p>",
  "src": "{{SITE_URL}}/uploads/juan.jpg"
}
```

### divi/pricing-table
**Tabla de precios.** Título, contenido (features), pricing y botón.

```json
{
  "module": "divi/pricing-table",
  "title": "Plan Premium",
  "content": "<ul><li>Feature 1</li><li>Feature 2</li></ul>",
  "pricing": { "price": "$299", "currency": "MXN", "sum": "/mes" },
  "button_text": "Contratar",
  "button_url": "/checkout"
}
```

### divi/icon-list / divi/icon-list-item
**Lista con íconos.** Para features, checklists, beneficios.

```json
{
  "module": "divi/icon-list",
  "children": [
    { "module": "divi/icon-list-item", "title": "Env\u00edo gratis", "icon": "&#x2714;" },
    { "module": "divi/icon-list-item", "title": "Soporte 24/7", "icon": "&#x2714;" }
  ]
}
```

### divi/search
**Barra de búsqueda.**

```json
{
  "module": "divi/search",
  "show_button": "on",
  "exclude_pages": "off",
  "exclude_posts": "off"
}
```

### divi/map
**Mapa de Google Maps.** Requiere API key configurada en Divi.

```json
{
  "module": "divi/map",
  "address": "Av. Insurgentes Sur 123, CDMX",
  "mouse_wheel": "on",
  "mobile_dragging": "on"
}
```

### divi/sidebar
**Área de widgets.**

```json
{
  "module": "divi/sidebar",
  "area": "sidebar-1",
  "show_border": "on"
}
```

### divi/login
**Formulario de login.**

```json
{
  "module": "divi/login",
  "content": "<p>Inicia sesi\u00f3n para acceder.</p>",
  "button_text": "Entrar"
}
```

### divi/countdown-timer
**Cuenta regresiva.**

```json
{
  "module": "divi/countdown-timer",
  "title": "Oferta termina en:"
}
```

---

## 5. Sliders

### divi/slider
**Contenedor de slideshow.** Los hijos son `divi/slide`.

```json
{
  "module": "divi/slider",
  "children": [
    {
      "module": "divi/slide",
      "title": "Slide 1",
      "content": "<p>Descripci\u00f3n del slide.</p>",
      "src": "{{SITE_URL}}/uploads/slide1.jpg",
      "button_text": "M\u00e1s info",
      "button_url": "/pagina"
    }
  ]
}
```

### divi/slide
**Item individual de slider.**

| Atributo | Descripción |
| :--- | :--- |
| `title` | Título del slide |
| `content` | HTML del contenido |
| `src` | URL de imagen de fondo |
| `button_text` | Texto del botón CTA |
| `button_url` | URL del botón |

---

## 6. Bloques Dinámicos

### divi/blog
**Grid de posts de WordPress.**

```json
{
  "module": "divi/blog",
  "type": "post",
  "number": 6,
  "categories": [5, 12],
  "showExcerpt": "on",
  "showAuthor": "off",
  "showDate": "on",
  "showCategories": "on",
  "showComments": "off",
  "show_featured_image": "on"
}
```

### divi/post-title
**Título dinámico del post actual.** No necesita contenido estático.

### divi/post-content
**Contenido dinámico del post actual.** No necesita contenido estático.

### divi/comments
**Comentarios del post actual.** No necesita contenido.

---

## 7. Bloques Fullwidth

Usar cuando el diseño requiere ancho completo (full viewport). Compatibles con decoration y mismos atributos que sus versiones no-fullwidth.

| Bloque fullwidth | Equivalente regular |
| :--- | :--- |
| `divi/fullwidth-code` | `divi/code` |
| `divi/fullwidth-image` | `divi/image` |
| `divi/fullwidth-menu` | `divi/menu` |
| `divi/fullwidth-map` | `divi/map` |
| `divi/fullwidth-slider` | `divi/slider` |
| `divi/fullwidth-header` | Hero header (único, sin equivalente) |
| `divi/fullwidth-post-title` | `divi/post-title` |
| `divi/fullwidth-post-content` | `divi/post-content` |

### divi/fullwidth-header
**Hero de ancho completo con título, subtítulo, contenido, botones y logo.**

```json
{
  "module": "divi/fullwidth-header",
  "title": "T\u00edtulo del Proyecto",
  "subtitle": "Subt\u00edtulo de la marca",
  "content": "<p>Descripci\u00f3n del hero.</p>",
  "button_text": "Explorar",
  "button_url": "/tienda",
  "logo_src": "{{SITE_URL}}/uploads/logo.png",
  "logo_alt": "Logo Proyecto"
}
```

---

## 8. Contenedores Especiales

### divi/group
**Contenedor ligero sin semántica de section.** Útil para agrupar módulos visualmente.

### divi/group-carousel
**Grupo en carrusel.**

### divi/global-layout / divi/layout
**Layouts reutilizables.** Decoración solamente.

---

## 9. Bloques WooCommerce (26)

Usar cuando se construyen páginas de tienda / producto. Todos soportan decoration pero su contenido es dinámico (heredo del producto actual).

| Bloque | Qué muestra |
| :--- | :--- |
| `divi/shop` | Grid de productos |
| `divi/woocommerce-product-title` | Título del producto |
| `divi/woocommerce-product-price` | Precio |
| `divi/woocommerce-product-gallery` | Galería de imágenes |
| `divi/woocommerce-product-add-to-cart` | Botón de compra |
| `divi/woocommerce-product-description` | Descripción corta |
| `divi/woocommerce-product-rating` | Calificación (estrellas) |
| `divi/woocommerce-product-reviews` | Reseñas |
| `divi/woocommerce-product-meta` | SKU, categorías, etiquetas |
| `divi/woocommerce-product-stock` | Stock disponible |
| `divi/woocommerce-product-tabs` | Tabs (descripción + reviews) |
| `divi/woocommerce-product-upsell` | Upsell products |
| `divi/woocommerce-related-products` | Productos relacionados |
| `divi/woocommerce-breadcrumb` | Breadcrumb de tienda |
| `divi/woocommerce-cart-notice` | Notificación de carrito |
| `divi/woocommerce-cart-products` | Productos en carrito |
| `divi/woocommerce-cart-totals` | Totales del carrito |
| `divi/woocommerce-checkout-billing` | Datos de facturación |
| `divi/woocommerce-checkout-shipping` | Datos de envío |
| `divi/woocommerce-checkout-order-details` | Resumen del pedido |
| `divi/woocommerce-checkout-payment-info` | Información de pago |

---

## 10. Bloques Misceláneos

| Bloque | Uso |
| :--- | :--- |
| `divi/lottie` | Animaciones Lottie (`src`: URL del JSON) |
| `divi/svg` | SVG inline (`content`: código SVG) |
| `divi/before-after-image` | Comparación de imágenes (`before_src`, `after_src`) |
| `divi/shortcode-module` | Shortcode de WordPress / terceros (`content`: shortcode) |
| `divi/breadcrumbs` | Breadcrumbs |
| `divi/link` | Enlace decorativo |
| `divi/placeholder` | Placeholder visual (solo decoration) |
| `divi/portfolio` | Grid de proyectos |
| `divi/filterable-portfolio` | Portfolio filtrable |
| `divi/canvas-portal` | Portal canvas 3D |

---

## Guía de Decisión para el Arquitecto

Cuando estés en Fase 1 y tengas que decidir qué bloque usar para cada elemento semántico, sigue esta jerarquía:

```
Elemento semántico → ¿Hay un bloque nativo? → Sí → Usar ese bloque
                   → No → ¿Se puede componer con decoration? → Sí → divi/text con decoration + headingFont/bodyFont
                   → No → divi/code con HTML inline
```

**NO USAR `divi/code` como comodín.** Solo cuando no exista un bloque nativo mejor. `divi/code` es HTML plano sin edición visual en Divi.

**Prioridad de elección:**
1. Bloque nativo específico (`divi/blurb`, `divi/number-counter`, etc.)
2. `divi/text` con decoration + headingFont + bodyFont
3. `divi/code` solo como último recurso
