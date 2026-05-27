# Manifiesto Arquitectónico y Catálogo de Componentes (v3.0)

Define cómo la IA traduce la intención institucional en realidad técnica.

## 1. Principios de Diseño: Autoridad y Confianza

El diseño debe proyectar una institución secular, premium y autoritaria.
- **DNA Visual**: Minimalismo, bordes técnicos (0px o 12px), tipografía Inter/Roboto.
- **Inyección Nativa**: Todo estilo debe inyectarse en los atributos de Divi para ser editable desde el Visual Builder. **PROHIBIDO** el CSS inline no rastreable.

## 2. Sistema de Tokens Dinámicos

Los tokens permiten que el diseño sea consistente y se actualice globalmente:

| Token | Uso | Valor por Defecto |
|-------|-----|-------------------|
| `{{token:primary}}` | Color de marca principal | Azul Profundo (`#002147`) |
| `{{token:secondary}}` | Acentos y detalles técnicos | Dorado (`#ca8a04`) |
| `{{token:accent}}` | Alertas y CTAs de alta prioridad | Rojo (`#e02b20`) |
| `{{token:bg_deep}}` | Fondos de sección oscuros | Tinta (`#1c1917`) |

## 3. Diccionario de Presets Institucionales

El `Layout_Engine` utiliza estos presets para inyectar valores exactos en el objeto `decoration` de cada bloque:

| Preset | Aplicación | Especificaciones de Inyección |
|--------|------------|------------------------------|
| `hero` | Secciones principales | Padding 120px, Bg `{{token:bg_deep}}`, Width 100%. |
| `card` | Contenedores de info | Bg `#ffffff`, Radius `12px`, Shadow (`10px/30px/rgba(0,33,71,0.08)`). |
| `glass` | Overlays en fondos oscuros | Bg `rgba(255,255,255,0.03)`, Blur `15px`, Saturate `150%`, Border `1px`. |
| `sp5-btn-primary` | Botones de CTA principal | Bg `{{token:secondary}}` (Dorado), Radius `8px`, Padding `14px/28px`, Shadow dorada. |

## 4. Registro de Clases `sp5-` (Comportamiento y Estilo)

Clases adicionales que el sistema aplica para funciones que Divi no maneja por atributos:

- **Layout**: `sp5-hero`, `sp5-dark`, `sp5-glass`.
- **Tipografía**: `sp5-display` (H1 impactante), `sp5-eyebrow` (Etiqueta superior), `sp5-lead` (Introducción).
- **Componentes**: `sp5-btn-primary`, `sp5-btn-ghost`, `sp5-badge`.
- **Animación**: `sp5-fade-up` (Entrada), `sp5-reveal` (Revelado).

## 5. Especificaciones Técnicas (JSON Schema)

El motor de layout procesa la clave `decoration` con esta jerarquía:

### Estructura de Fondo (`background`)
```json
"background": {
  "color": "{{token:primary}}",
  "image": { "url": "...", "parallax": { "enabled": "on" } }
}
```

### Estructura de Bordes y Sombras (`border`, `boxShadow`)
```json
"border": {
  "radius": { "topLeft": "12px", "topRight": "12px" },
  "width": { "top": "1px" },
  "color": { "top": "{{token:secondary}}" }
}
```

## 6. Procedimiento de Saneamiento Visual
El sistema aplica automáticamente:
- **Reseteo de Caché**: `et_core_clear_wp_cache()`.
- **Sincronización**: Eliminación de `et_pb_css_synced` para forzar la regeneración del CSS estático de Divi 5 tras cada inyección.
