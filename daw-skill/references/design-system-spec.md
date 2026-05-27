# DAW — Especificación de Design Systems

**Propósito**: Esta guía permite que cualquier persona — diseñador, desarrollador o agente — cree un archivo `workspace/design-system/<proyecto>.json` con la profundidad exacta que el DAW necesita para generar páginas de clase mundial.

> El DAW puede trabajar con cualquier design system que cumpla esta especificación. Sin cumplirla, el motor opera en "modo degradado" y el resultado visual será básico.

---

## Estructura Obligatoria del JSON

```json
{
  "name": "Nombre del Proyecto v1.0",
  "description": "Descripción corta del sistema de diseño",
  "tokens": {
    "color": { ... },
    "font":  { ... },
    "radius": { ... },
    "space": { ... }
  },
  "presets": {
    "section": { ... },
    "text": { ... },
    "module": { ... }
  }
}
```

---

## Sección `tokens`

### `tokens.color` — Mínimo 10 tokens semánticos

No uses nombres de colores literales (`red`, `blue`). Usa nombres **semánticos** que describen el *rol* del color.

| Token | Rol | Valores típicos por industria |
|-------|-----|-------------------------------|
| `surface-deep` | Fondo más oscuro. Hero, navbar oscura. | Editorial: `#001338` · Tech/SaaS: `#0D0D0D` · Salud: `#1A2B4A` |
| `surface-mid` | Fondo alternativo oscuro. Footer, CTA oscura. | `#1E3A5F` · `#1A1A2E` · `#222126` |
| `surface-light` | Fondo de secciones claras. | `#FAF8F5` (cálido) · `#F8FAFC` (frío) · `#F5F0EB` (beige) |
| `surface-white` | Fondo de tarjetas y módulos limpios. | `#FFFFFF` siempre |
| `accent` | Color de acento **solo para CTAs** y elementos de énfasis puntual. | `#DC2626` (rojo) · `#3B82F6` (azul) · `#10B981` (verde) |
| `accent-hover` | Versión oscurecida del acento para estado hover. | Oscurecer `accent` un 15-20% |
| `premium` | Tono de lujo/distinción. Eyebrows, separadores, detalles. | `#D4A747` (gold) · `#9B59B6` (violeta) · `#C0C0C0` (silver) |
| `text-primary` | Texto principal sobre fondos claros. | `#001338` · `#111111` · `#1A1A1A` |
| `text-secondary` | Texto secundario, captions, labels. | `#475569` · `#6B7280` · `#64748B` |
| `text-on-dark` | Texto sobre fondos oscuros (`surface-deep`, `surface-mid`). | `#F1F5F9` · `#EFEFEF` · `#E2E8F0` |

> [!IMPORTANT]
> **Regla de oro**: El color `accent` nunca se usa como fondo de secciones grandes. Solo en botones, badges, líneas decorativas y estados hover. Los fondos de secciones son siempre `surface-*`.

### `tokens.font` — Mínimo 2 tokens

| Token | Rol | Guía de selección |
|-------|-----|------------------|
| `display` | Fuente de titulares y héroe. Crea identidad e impacto. | Editorial/Lujo: serif como Playfair Display, Lora, Cormorant · Tech: sans-serif como Syne, Space Grotesk · Impacto: display como Bebas Neue |
| `ui` | Fuente de cuerpo, UI, botones. Debe ser muy legible. | DM Sans, Inter, Outfit, Plus Jakarta Sans |

**Formato exacto** (Google Fonts ready):
```json
"font": {
  "display": "'Playfair Display', Georgia, serif",
  "ui": "'DM Sans', system-ui, sans-serif"
}
```

### `tokens.radius` — Exactamente 4 tokens

```json
"radius": {
  "sm": "6px",
  "md": "12px",
  "lg": "20px",
  "full": "9999px"
}
```
> El `radius.lg` es el más importante. Tarjetas, contenedores, imágenes. Usar 16px mínimo. Diseños modernos usan 20-24px.

### `tokens.space` — Exactamente 7 tokens

```json
"space": {
  "xs": "8px",
  "sm": "16px",
  "md": "24px",
  "lg": "40px",
  "xl": "64px",
  "2xl": "96px",
  "3xl": "140px"
}
```
> Los tokens `xl`, `2xl` y `3xl` son los paddings de secciones. El DAW los usa para garantizar el espacio negativo que caracteriza los diseños premium.

---

## Sección `presets`

Los presets son **configuraciones complejas pre-fabricadas** que el Design Resolver inyecta en el schema antes de compilar. Evitan que el Diseñador tenga que repetir la misma configuración de decoration en cada bloque.

### `presets.section` — Los 5 Obligatorios

#### `hero-dark` — Hero sobre fondo oscuro profundo
```json
"hero-dark": {
  "decoration": {
    "background": {
      "desktop": { "value": { "color": "{{design:color:surface-deep}}" } }
    },
    "spacing": {
      "desktop": { "value": { "padding": { "top": "{{design:space:3xl}}", "bottom": "{{design:space:3xl}}", "right": "5%", "left": "5%" } } },
      "tablet":  { "value": { "padding": { "top": "{{design:space:2xl}}", "bottom": "{{design:space:2xl}}", "right": "5%", "left": "5%" } } },
      "phone":   { "value": { "padding": { "top": "{{design:space:xl}}", "bottom": "{{design:space:xl}}", "right": "5%", "left": "5%" } } }
    }
  }
}
```

#### `hero-image-dark` — Hero con imagen de fondo oscura + overlay de gradiente
```json
"hero-image-dark": {
  "decoration": {
    "spacing": {
      "desktop": { "value": { "padding": { "top": "{{design:space:3xl}}", "bottom": "{{design:space:3xl}}", "right": "5%", "left": "5%" } } },
      "tablet":  { "value": { "padding": { "top": "{{design:space:2xl}}", "bottom": "{{design:space:2xl}}", "right": "5%", "left": "5%" } } },
      "phone":   { "value": { "padding": { "top": "{{design:space:xl}}", "bottom": "{{design:space:xl}}", "right": "5%", "left": "5%" } } }
    }
  }
}
```

#### `trust-bar` — Sección de métricas/stats
```json
"trust-bar": {
  "decoration": {
    "background": {
      "desktop": { "value": { "color": "{{design:color:surface-deep}}" } }
    },
    "spacing": {
      "desktop": { "value": { "padding": { "top": "{{design:space:xl}}", "bottom": "{{design:space:xl}}", "right": "5%", "left": "5%" } } }
    }
  }
}
```

#### `cta-epic` — Llamado a la acción con alto impacto (fondo oscuro)
```json
"cta-epic": {
  "decoration": {
    "background": {
      "desktop": { "value": { "color": "{{design:color:surface-mid}}" } }
    },
    "spacing": {
      "desktop": { "value": { "padding": { "top": "{{design:space:3xl}}", "bottom": "{{design:space:3xl}}", "right": "5%", "left": "5%" } } }
    }
  }
}
```

#### `light` — Sección clara estándar
```json
"light": {
  "decoration": {
    "background": {
      "desktop": { "value": { "color": "{{design:color:surface-light}}" } }
    },
    "spacing": {
      "desktop": { "value": { "padding": { "top": "{{design:space:2xl}}", "bottom": "{{design:space:2xl}}", "right": "5%", "left": "5%" } } },
      "tablet":  { "value": { "padding": { "top": "{{design:space:xl}}", "bottom": "{{design:space:xl}}", "right": "5%", "left": "5%" } } },
      "phone":   { "value": { "padding": { "top": "{{design:space:lg}}", "bottom": "{{design:space:lg}}", "right": "5%", "left": "5%" } } }
    }
  }
}
```

#### `dark` — Sección oscura alternativa (CTA, footer superior)
```json
"dark": {
  "decoration": {
    "background": {
      "desktop": { "value": { "color": "{{design:color:surface-mid}}" } }
    },
    "spacing": {
      "desktop": { "value": { "padding": { "top": "{{design:space:2xl}}", "bottom": "{{design:space:2xl}}", "right": "5%", "left": "5%" } } },
      "tablet":  { "value": { "padding": { "top": "{{design:space:xl}}", "bottom": "{{design:space:xl}}", "right": "5%", "left": "5%" } } },
      "phone":   { "value": { "padding": { "top": "{{design:space:lg}}", "bottom": "{{design:space:lg}}", "right": "5%", "left": "5%" } } }
    }
  }
}
```

#### `white` — Sección blanca limpia (testimonials, features)
```json
"white": {
  "decoration": {
    "background": {
      "desktop": { "value": { "color": "{{design:color:surface-white}}" } }
    },
    "spacing": {
      "desktop": { "value": { "padding": { "top": "{{design:space:2xl}}", "bottom": "{{design:space:2xl}}", "right": "5%", "left": "5%" } } },
      "tablet":  { "value": { "padding": { "top": "{{design:space:xl}}", "bottom": "{{design:space:xl}}", "right": "5%", "left": "5%" } } },
      "phone":   { "value": { "padding": { "top": "{{design:space:lg}}", "bottom": "{{design:space:lg}}", "right": "5%", "left": "5%" } } }
    }
  }
}
```

---

### `presets.text` — Los 6 Obligatorios

#### `eyebrow` — Etiqueta superior (antes del título)
```json
"eyebrow": {
  "headingFont": {
    "p": { "font": { "desktop": { "value": {
      "fontFamily": "{{design:font:ui}}",
      "weight": "700",
      "textTransform": "uppercase",
      "letterSpacing": "0.1em",
      "color": "{{design:color:premium}}",
      "size": "13px"
    } } } }
  }
}
```

#### `display-xl` — Titular hero masivo (H1 principal)
```json
"display-xl": {
  "headingFont": {
    "h1": { "font": {
      "desktop": { "value": { "fontFamily": "{{design:font:display}}", "color": "{{design:color:text-on-dark}}", "size": "72px", "weight": "700", "lineHeight": "1.05" } },
      "tablet":  { "value": { "size": "44px", "lineHeight": "1.1" } },
      "phone":   { "value": { "size": "32px", "lineHeight": "1.15" } }
    } }
  }
}
```

#### `headline` — H2 sobre fondo claro
```json
"headline": {
  "headingFont": {
    "h2": { "font": {
      "desktop": { "value": { "fontFamily": "{{design:font:display}}", "color": "{{design:color:text-primary}}", "size": "40px", "weight": "700" } },
      "tablet":  { "value": { "size": "30px" } },
      "phone":   { "value": { "size": "24px" } }
    } }
  }
}
```

#### `headline-light` — H2 sobre fondo oscuro
```json
"headline-light": {
  "headingFont": {
    "h2": { "font": {
      "desktop": { "value": { "fontFamily": "{{design:font:display}}", "color": "{{design:color:text-on-dark}}", "size": "40px", "weight": "700" } },
      "tablet":  { "value": { "size": "30px" } },
      "phone":   { "value": { "size": "24px" } }
    } }
  }
}
```

#### `lead` — Párrafo lead sobre fondo oscuro
```json
"lead": {
  "bodyFont": {
    "body": { "font": { "desktop": { "value": {
      "fontFamily": "{{design:font:ui}}",
      "color": "{{design:color:text-on-dark}}",
      "size": "18px",
      "lineHeight": "1.75"
    } } } }
  }
}
```

#### `lead-dark` — Párrafo lead sobre fondo claro
```json
"lead-dark": {
  "bodyFont": {
    "body": { "font": { "desktop": { "value": {
      "fontFamily": "{{design:font:ui}}",
      "color": "{{design:color:text-secondary}}",
      "size": "18px",
      "lineHeight": "1.75"
    } } } }
  }
}
```

---

### `presets.module` — Los Obligatorios Premium

> [!IMPORTANT]
> Todos los `presets.module` deben incluir un objeto de animación para garantizar una experiencia fluida al hacer scroll.

#### `card` — Tarjeta estándar (blurb, text con fondo)
```json
"card": {
  "decoration": {
    "background": { "desktop": { "value": { "color": "{{design:color:surface-white}}" } } },
    "border": { "desktop": { "value": {
      "radius": { "topLeft": "{{design:radius:lg}}", "topRight": "{{design:radius:lg}}", "bottomRight": "{{design:radius:lg}}", "bottomLeft": "{{design:radius:lg}}", "sync": "on" }
    } } },
    "boxShadow": { "desktop": { "value": {
      "horizontal": "0px", "vertical": "8px", "blur": "32px", "spread": "-4px", "color": "rgba(0,0,0,0.10)"
    } } },
    "spacing": { "desktop": { "value": {
      "padding": { "top": "{{design:space:lg}}", "right": "{{design:space:lg}}", "bottom": "{{design:space:lg}}", "left": "{{design:space:lg}}", "sync": "on" }
    } } }
  }
}
```

#### `feature-card` — Card de feature con hover elevación
```json
"feature-card": {
  "decoration": {
    "background": { "desktop": { "value": { "color": "{{design:color:surface-white}}" } } },
    "border": { "desktop": { "value": {
      "radius": { "topLeft": "{{design:radius:lg}}", "topRight": "{{design:radius:lg}}", "bottomRight": "{{design:radius:lg}}", "bottomLeft": "{{design:radius:lg}}", "sync": "on" }
    } } },
    "boxShadow": { "desktop": { "value": {
      "horizontal": "0px", "vertical": "8px", "blur": "32px", "spread": "-4px", "color": "rgba(0,0,0,0.08)"
    } } },
    "spacing": { "desktop": { "value": {
      "padding": { "top": "{{design:space:lg}}", "right": "{{design:space:lg}}", "bottom": "{{design:space:lg}}", "left": "{{design:space:lg}}", "sync": "on" }
    } } },
    "transform": {
      "hover": { "value": { "translateY": "-8px" } }
    },
    "animation": {
      "desktop": { "value": { "style": "slide", "direction": "bottom", "duration": "700ms", "delay": "100ms", "intensity": "10%" } }
    }
  }
}
```

#### `stat-item` — Stat grande con número y label
```json
"stat-item": {
  "decoration": {
    "border": { "desktop": { "value": {
      "top": { "width": "3px", "color": "{{design:color:premium}}", "style": "solid" }
    } } },
    "spacing": { "desktop": { "value": {
      "padding": { "top": "{{design:space:md}}", "bottom": "{{design:space:md}}" }
    } } },
    "animation": {
      "desktop": { "value": { "style": "slide", "direction": "bottom", "duration": "700ms", "delay": "0ms", "intensity": "20%" } }
    }
  }
}
```

#### `testimonial-card` — Tarjeta blanca con quote y estilo sutil
```json
"testimonial-card": {
  "decoration": {
    "background": { "desktop": { "value": { "color": "{{design:color:surface-white}}" } } },
    "border": { "desktop": { "value": {
      "radius": { "topLeft": "{{design:radius:md}}", "topRight": "{{design:radius:md}}", "bottomRight": "{{design:radius:md}}", "bottomLeft": "{{design:radius:md}}", "sync": "on" }
    } } },
    "spacing": { "desktop": { "value": {
      "padding": { "top": "{{design:space:lg}}", "right": "{{design:space:lg}}", "bottom": "{{design:space:lg}}", "left": "{{design:space:lg}}", "sync": "on" }
    } } },
    "animation": {
      "desktop": { "value": { "style": "fade", "duration": "800ms", "delay": "100ms" } }
    }
  }
}
```

#### `btn-primary` — Botón principal de acento
```json
"btn-primary": {
  "decoration": {
    "button": { "desktop": { "value": {
      "backgroundColor": "{{design:color:accent}}",
      "textColor": "{{design:color:surface-white}}",
      "borderRadius": "{{design:radius:full}}",
      "fontFamily": "{{design:font:ui}}",
      "fontWeight": "600",
      "padding": "14px 36px",
      "letterSpacing": "0.03em"
    } } }
  }
}
```

#### `btn-ghost` — Botón secundario fantasma
```json
"btn-ghost": {
  "decoration": {
    "button": { "desktop": { "value": {
      "backgroundColor": "transparent",
      "textColor": "{{design:color:text-on-dark}}",
      "borderColor": "{{design:color:text-on-dark}}",
      "borderWidth": "2px",
      "borderRadius": "{{design:radius:full}}",
      "fontFamily": "{{design:font:ui}}",
      "fontWeight": "600",
      "padding": "12px 34px",
      "letterSpacing": "0.03em"
    } } }
  }
}
```

---

## Guía de Decisiones de Diseño

### ¿Qué fuente `display` elegir?

| Industria | Recomendación | Motivo |
|-----------|--------------|--------|
| Editorial / Religioso / Lujo | Playfair Display, Cormorant, Lora | Transmite tradición, autoridad y distinción |
| Tecnología / SaaS / Startup | Space Grotesk, Syne, Plus Jakarta Sans | Moderno, geométrico, dinámico |
| Salud / Bienestar / ONG | Nunito, Raleway, Poppins | Amigable, accesible, cercano |
| Moda / Lifestyle / Belleza | Josefin Sans, Bodoni Moda, DM Serif | Elegante, aspiracional |
| Educación / Corporativo | Merriweather, Source Serif, Inter | Confiable, serio, legible |
| Restaurante / Comida | Playfair Display, Dancing Script | Artesanal, cálido, apetitoso |

### ¿Cómo asignar `surface-deep` sin que choque con `accent`?

- Si `accent` es **cálido** (rojo, naranja, amarillo): `surface-deep` debe ser **azul profundo o negro puro** (complementario frío).
- Si `accent` es **frío** (azul, verde, violeta): `surface-deep` puede ser **gris carbón o azul profundo oscuro**.
- Evitar: `accent` naranja con `surface-deep` naranja oscuro — se mezclan y pierden contraste.

### ¿Cuántos presets necesito para cada tipo de proyecto?

| Tipo de Proyecto | Presets Mínimos de Sección | Presets Mínimos de Módulo |
|-----------------|--------------------------|--------------------------|
| Homepage/Landing | hero-dark, light, dark, white | card, feature-card, btn-primary |
| E-commerce | hero-cinematic, light, dark | card, btn-primary, stat-item |
| Blog/Editorial | hero-dark, light, white | card, btn-ghost, lead |
| Portfolio | hero-cinematic, dark, white | feature-card, btn-primary |
| SaaS/App | hero-dark, light, dark, white | feature-card, stat-item, btn-primary, btn-ghost |

---

## Template Completo de Referencia

Copia este template y personaliza los valores para cualquier proyecto:

```json
{
  "name": "Mi Proyecto v1.0",
  "description": "Design System para [descripción del proyecto]",
  "tokens": {
    "color": {
      "surface-deep":  "#001338",
      "surface-mid":   "#1E3A5F",
      "surface-light": "#FAF8F5",
      "surface-white": "#FFFFFF",
      "accent":        "#DC2626",
      "accent-hover":  "#B91C1C",
      "premium":       "#D4A747",
      "text-primary":  "#001338",
      "text-secondary":"#475569",
      "text-on-dark":  "#F1F5F9"
    },
    "font": {
      "display": "'Playfair Display', Georgia, serif",
      "ui":      "'DM Sans', system-ui, sans-serif"
    },
    "radius": {
      "sm":   "6px",
      "md":   "12px",
      "lg":   "20px",
      "full": "9999px"
    },
    "space": {
      "xs":  "8px",
      "sm":  "16px",
      "md":  "24px",
      "lg":  "40px",
      "xl":  "64px",
      "2xl": "96px",
      "3xl": "140px"
    }
  },
  "presets": {
    "section": {
      "hero-dark": { "...": "ver spec arriba" },
      "hero-cinematic": { "...": "ver spec arriba" },
      "light": { "...": "ver spec arriba" },
      "dark": { "...": "ver spec arriba" },
      "white": { "...": "ver spec arriba" }
    },
    "text": {
      "eyebrow": { "...": "ver spec arriba" },
      "display-xl": { "...": "ver spec arriba" },
      "headline": { "...": "ver spec arriba" },
      "headline-light": { "...": "ver spec arriba" },
      "lead": { "...": "ver spec arriba" },
      "lead-dark": { "...": "ver spec arriba" }
    },
    "module": {
      "card": { "...": "ver spec arriba" },
      "feature-card": { "...": "ver spec arriba" },
      "stat-item": { "...": "ver spec arriba" },
      "btn-primary": { "...": "ver spec arriba" },
      "btn-ghost": { "...": "ver spec arriba" }
    }
  }
}
```
