# Análisis: Por qué DAW produce diseño mediocre

## Comparación de tres versiones (mismo contenido, mismo motor Divi)

| Versión | URL | Técnica | Diseño |
|---------|-----|---------|--------|
| DAW-VIE genérico | `/nuestros-planteles` | Automática | Básico, olvidable |
| UX-PRO + frontend-design | `/nuestros-planteles-uxpro` | Semi-manual | Mejor color/tipo, pero aún genérico |
| **Diseño Real (manual)** | `/nuestros-planteles-diseno-real` | Manual | **Distintivo, memorable** |

---

## El problema raíz: DAW no tiene "dirección de diseño"

### 1. El brief solo describe contenido, nunca atmósfera

El brief actual dice:
- ❌ "section_type: hero"
- ❌ "title: Descubre Nuestros Campus"
- ❌ "text: Tres campus..."

Pero **nunca** dice:
- ✅ "atmósfera: biblioteca nocturna con luz cálida"
- ✅ "tipografía: serif elegante con sans utilitario"
- ✅ "color: azul marino profundo + dorado envejecido"
- ✅ "layout: hero centrado, about asimétrico, features oscuro"
- ✅ "motion: parallax sutil, fade progresivo"

### 2. El VIE aplica presets fijos predefinidos

El VIE tiene un catálogo de ~12 presets (`hero-dark`, `glass-card`, `cta-epic`, etc.) que son **siempre los mismos** sin importar el contenido. Esto es equivalente a usar una plantilla de Canva: técnicamente correcto, visualmente olvidable.

El resultado es siempre:
- Hero oscuro + gradiente radial azul genérico
- Features en grid 1-2-3 con glass cards idénticas
- CTA oscuro + botón primario
- Sin jerarquía visual dramática

### 3. No hay jerarquía visual, solo lista de secciones

Un buen diseño tiene **ritmo**:
- Hero grande y oscuro → impacto inicial
- Sección clara con aire → descanso visual
- Features oscuro con detalles sutiles → profundidad
- CTA minimalista → conversión limpia

DAW produce **lista plana**: todas las secciones tienen el mismo peso visual.

---

## Diferencias concretas: DAW-VIE vs Diseño Real

| Decisión de diseño | DAW-VIE genérico | Diseño Real (manual) |
|-------------------|-------------------|----------------------|
| **Paleta** | `#1C1917` + `#0071E3` (genérico Apple) | `#0A0E1A` + `#C9A962` + `#F4F1EA` (académico nocturno) |
| **Tipografía** | SF Pro Display (system) | Crimson Pro serif + Space Grotesk sans |
| **Hero** | 140px padding, gradiente radial | 180px padding, gradiente lineal dramático |
| **Separador título-texto** | Ninguno | Divider dorado de 80px |
| **Botón primary** | `btn-primary` preset (border-radius 3px) | Cuadrado, tracking 2px, uppercase |
| **Sección About** | 4_4 centrado genérico | 2/5 + 3/5 asimétrico, fondo cálido #F4F1EA |
| **Features** | `glass-card` preset + blurb + icono ET | Cards sutiles con borde dorado tenue + emoji + divider |
| **CTA** | 4_4 centrado oscuro | 1/3 + 2/3, botón outline transparente + borde dorado |
| **Shape divider** | Curve genérico | Wave sutil |

---

## Solución propuesta: Director de Diseño en el VIE

Para que DAW produzca diseños distintivos, necesitamos tres cambios:

### Paso 1: Brief con intención de diseño explícita

```json
{
  "title": "Nuestros Planteles",
  "design_direction": {
    "mood": "academic_night",
    "color_temperature": "warm_on_dark",
    "typography_style": "serif_display_plus_sans_ui",
    "layout_rhythm": "dramatic_asymmetric",
    "spacing_density": "generous",
    "accent_material": "gold_antique",
    "motion_intensity": "subtle_parallax"
  }
}
```

### Paso 2: Director de Diseño (nuevo módulo VIE)

El Director toma `design_direction` y decide:

| Intención | Decisión concreta |
|-----------|-------------------|
| `mood: academic_night` | bg `#0A0E1A`, overlay gradiente lineal, text `#F4F1EA` |
| `accent_material: gold_antique` | accent `#C9A962`, dividers dorados, bordes tenues |
| `typography: serif_display` | heading font `'Crimson Pro'`, body `'Space Grotesk'` |
| `layout: dramatic_asymmetric` | hero 4_4 centrado, about 2/5+3/5, cta 1/3+2/3 |
| `spacing: generous` | hero 180px, sections 140px, generous whitespace |
| `motion: subtle_parallax` | parallax on hero bg, fade-in on sections |

### Paso 3: Presets dinámicos (no presets fijos)

En vez de `presets: ["section:hero-dark"]`, el VIE genera **decoration blocks calculados** a partir del Director:

```json
{
  "background": { "color": "#0A0E1A", "overlay": { "gradient": "linear-gradient(...)" } },
  "spacing": { "padding": { "top": "180px", "bottom": "160px" } },
  "shapeDivider": { "bottom": { "style": "wave", "color": "#F4F1EA", "height": "80px" } }
}
```

---

## Estado actual

- ❌ DAW-VIE produce diseño funcional pero olvidable
- ❌ El brief no transmite dirección de diseño
- ❌ Los presets son fijos y genéricos
- ✅ El motor técnico (Divi + build_page.php) funciona perfectamente
- ✅ La arquitectura de 3 capas (daw/ + vie/ + handlers/) está lista para extenderse
- ✅ Se demostró que Divi puede renderizar diseño distintivo si se le da la dirección correcta

## Próximo paso recomendado

Implementar `vie/director.py` con las siguientes capacidades:
1. Leer `design_direction` del brief
2. Mapear intenciones a decisiones concretas (color, tipo, layout, spacing)
3. Generar decoration blocks dinámicos en vez de aplicar presets fijos
4. Permitir que `design_direction` sea opcional (fallback a genérico si no se especifica)
