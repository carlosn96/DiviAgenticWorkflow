# Plan: Refactor Strategy/Renderer del Layout Engine

## 1. Mapa del monolito actual (`class-layout-engine.php`, 1515 lineas)

```
render_block() (linea 49) — UNA funcion que hace TODO:
├── Mapeo de nombres legacy -> divi/* (lineas 50-62)
├── Render de children recursivo (lineas 74-80)
├── Inicializacion de attrs base (lineas 82-85)
├── Branch dgpc/product-carousel (lineas 92-93) — early exit
├── Branch divi/* (lineas 94-1234) — el monolito:
│   ├── Auto-merge style keys (96-101)
│   ├── Deep-merge module{} (103-112)
│   ├── Custom CSS freeForm (114-135)
│   ├── Auto-wrap decoration (137-155) [BUGFIX APLICADO AQUI]
│   ├── htmlAttributes (157-174)
│   ├── GROUP 1: Structural (section/row/column) (213-327)
│   ├── GROUP 2: Text-like (329-410)
│   ├── GROUP 3: Image-like (418-430)
│   ├── GROUP 4: Button (433-582) — 150 lineas solo para button
│   ├── GROUP 5: Menu (584-569)
│   ├── GROUP 6: Video/Audio (598-608)
│   ├── GROUP 7: Divider (610-624)
│   ├── GROUP 8: Contact Form (626-663)
│   ├── GROUP 9: Blurb (665-699)
│   ├── GROUP 10-36: Otros modulos (701-1140)
│   ├── GROUP 37: WooCommerce (1143-1149)
│   ├── GROUP 98: Static decoration-only (1151-1165)
│   ├── GROUP 99: Fullwidth fallthrough (1167-1172)
│   └── METADATA-DRIVEN FALLBACK (1174-1233) — solo divi/counters lo usa hoy
├── Render de items hijos (1237-1268)
├── convert_gcid_to_variable_syntax (1270-1272)
├── Normalizacion gradient/background (1274-1296)
└── Serializacion final JSON (1298-1302)

Funciones auxiliares:
├── build_dgpc_product_carousel_attrs() (1317-1413) — handler dgpc aislado
├── parse_css_gradient() (1428-1494) — utilidad estatica
└── convert_gcid_to_variable_syntax() (1497-1515) — recursivo
```

### Problemas del monolito

- 37 grupos `elseif` en una sola funcion
- Button solo = 150 lineas (button es el mas complejo por legacy VIE)
- El auto-wrap de decoration se aplica solo a `divi/*`, no a `dgpc/*` ni `dac/*`
- El handler de `dgpc/product-carousel` hace early exit sin normalizacion
- Cualquier bug en el auto-wrap afecta TODOS los bloques
- Imposible testear un bloque aislado
- Imposible agregar un namespace nuevo sin tocar el monolito

### Datos reales del proyecto (viabilidad)

- **16 `divi/*` slugs** usados en `page-defs` activos (de ~82 manejados).
- **~39 `divi/*` slugs** usados en `content_state` real desplegado.
- **Solo 1 modulo** (`divi/counters`) cae hoy al fallback metadata-driven.
- **Flat keys** (`button_text`, `button_url`) dominan en `page-defs`; `content_state` ya usa `button.innerContent` estructurado.
- **`dgpc/product-carousel`** es el unico bloque `dgpc/*` y solo existe en `content_state`, no en `page-defs`.
- **`dac/*`** no se usa en ningun page-def ni content_state (modulos custom `plus-counter`, `daw-counters` son registrados pero no instanciados).

Ver conclusiones del agente de analisis: arquitectura original sobre-facturada; metadata fallback NO cubre "cualquier modulo Divi".
## 2. Arquitectura target (simplificada tras analisis)

```
inc/core/
├── class-layout-engine.php               ← Dispatcher delgado (~150 lineas)
├── renderers/
│   ├── interface-block-renderer.php      ← Contrato
│   ├── trait-block-helpers.php           ← Helpers puros compartidos
│   ├── class-dgpc-renderer.php           ← dgpc/product-carousel
│   ├── class-dac-renderer.php            ← stub para dac/* (sin uso hoy)
│   ├── class-divi-base-renderer.php      ← abstracta con helpers + auto-wrap
│   ├── class-divi-structural-renderer.php ← section, row, column, row-inner, group...
│   ├── class-divi-text-renderer.php      ← text, heading, code, shortcode-module
│   ├── class-divi-button-renderer.php    ← button (flat + structured passthrough)
│   ├── class-divi-media-renderer.php     ← image, gallery, video, audio, lottie, svg
│   ├── class-divi-form-renderer.php      ← contact-form, contact-field
│   ├── class-divi-content-module-renderer.php ← blurb, testimonial, team-member, pricing-table, cta, icon
│   ├── class-divi-container-renderer.php ← tabs, accordion, slider, icon-list, social-follow
│   ├── class-divi-dynamic-renderer.php   ← countdown, blog, search, map, dropdown, portfolio
│   ├── class-divi-woo-renderer.php       ← woocommerce-*, shop
│   └── class-divi-generic-renderer.php   ← fullwidth fallthrough, before-after, metadata real
├── trait-module-metadata.php             ← sin cambios
└── trait-module-metadata-attributes.php  ← sin cambios
```

### Contrato del renderer

```php
interface Block_Renderer_Interface {
    /**
     * @return array{
     *   attrs: array<string, mixed>,
     *   inner: string,
     *   inner_html: string
     * }
     */
    public function render(string $slug, array $data, string $content_key, string $children_html): array;
}
```

`can_render()` se mantiene en el dispatcher via mapa de slugs por renderer para evitar colisiones de orden (ver riesgos).

### Dispatcher delgado

```php
class Layout_Engine {
    /** @var array<string, class-string<Block_Renderer_Interface>> */
    private array $renderer_map = [
        'dgpc/product-carousel' => Dgpc_Renderer::class,
        // structural
        'divi/section' => Divi_Structural_Renderer::class,
        'divi/row'     => Divi_Structural_Renderer::class,
        ...
        // fallback
        '*' => Divi_Generic_Renderer::class,
    ];

    private array $renderers = [];

    public function __construct() {
        // cache por tipo
    }

    private function render_block(string $block_name, array $data, string $content_key): string {
        $slug  = $this->resolve_slug($block_name);
        $class = $this->renderer_map[$slug] ?? $this->renderer_map['*'];
        $renderer = $this->renderers[$class] ??= new $class();

        $result = $renderer->render($slug, $data, $content_key, $children_html);
        $result['attrs'] = $this->post_process($result['attrs'], $slug);
        return $this->serialize($slug, $result);
    }
}
```

Mapa explícito en vez de `can_render()` ordenado evita colisiones y hace obvio a qué renderer va cada slug.

### Base comun (`Divi_Base_Renderer`)

Clase abstracta que heredan todos los renderers `divi/*`:
- Auto-merge de style_keys
- Deep-merge de `module{}`
- Auto-wrap de decoration (con bugfix aplicado)
- CSS freeForm
- htmlAttributes (`module_class`, `module_id`)
- Normalizaciones comunes post-render via trait `Block_Helpers`

No contiene `convert_gcid_to_variable_syntax` (eso es post-proceso global del dispatcher) para evitar que `dgpc` y `dac` queden sin el.

### Helpers puros (`trait-block-helpers.php`)

Todas las utilidades sin estado:
- `wrap_decoration(array $attrs): array` — auto-wrap del bugfix
- `merge_css_freeform(array $attrs, string $css): array`
- `build_html_attributes(array $data): array`
- `parse_css_gradient(string $css): ?array`
- `normalize_gradient_stops(array $attrs): array`
- `normalize_empty_background(array $attrs): array`
- `convert_gcid_to_variable_syntax(mixed $value): mixed` — centralizado

Cualquier renderer (incluido `dgpc`) puede usar el trait sin heredar de `Divi_Base_Renderer`.
## 3. Pasos de migracion incrementales

### Fase 0: Preparacion (sin romper nada)
1. Crear directorio `inc/core/renderers/`
2. Crear `interface-block-renderer.php`
3. Crear `trait-block-helpers.php` extrayendo utilidades compartidas:
   - `parse_css_gradient()`
   - `convert_gcid_to_variable_syntax()`
   - helpers de auto-wrap (sin activar aun en el monolito)
4. **NO** modificar `class-layout-engine.php` todavía.
5. **Verificar:** el monolito sigue funcionando sin cambios.

### Fase 1: Extraer helpers al monolito (compatibilidad)
1. Reemplazar `parse_css_gradient()` y `convert_gcid_to_variable_syntax()` en `class-layout-engine.php` por llamadas al trait `Block_Helpers`.
2. Asegurar que el resultado binario (temp JSON desplegado) sea identico al anterior para la pagina activa.
3. **Verificar:** deploy de `semana-biblica-2026-pro-combined.json` produce el mismo post_content.

### Fase 2: Renderer dgpc (aislar el carrusel)
1. Crear `class-dgpc-renderer.php` moviendo `build_dgpc_product_carousel_attrs()` del monolito.
2. El renderer usa `trait-block-helpers.php` para `convert_gcid_to_variable_syntax`.
3. Modificar dispatcher para que route `dgpc/*` al nuevo renderer.
4. Eliminar branch `dgpc/product-carousel` del monolito.
5. **Verificar:** deploy de pagina sin carrusel funciona igual; el carrusel (cuando se reinserte) no rompe.

### Fase 3: Base comun + Structural
1. Crear `class-divi-base-renderer.php` (abstracta) con helpers de attrs base.
2. Crear `class-divi-structural-renderer.php` para section/row/column/column-inner/row-inner.
3. Mover GROUP 1 al structural renderer.
4. **Verificar:** deploy de pagina con secciones funciona.

### Fase 4: Text + Button (los mas usados)
1. Crear `class-divi-text-renderer.php` (text, heading, code, shortcode-module).
2. Crear `class-divi-button-renderer.php` (button, con flat keys + structured passthrough).
3. **Verificar:** deploy con text/button funciona.

### Fase 5: Media + Form + ContentModule
1. `class-divi-media-renderer.php` (image, fullwidth-image, gallery, video, audio, lottie, svg).
2. `class-divi-form-renderer.php` (contact-form, contact-field, login, signup, contact-form-7).
3. `class-divi-content-module-renderer.php` (blurb, icon, testimonial, team-member, pricing-table, cta, fullwidth-header).
4. **Verificar.**

### Fase 6: Container + Dynamic + Woo + Generic
1. `class-divi-container-renderer.php` (tabs, tab, accordion, accordion-item, slider, slide, video-slider, video-slider-item, icon-list, icon-list-item, social-follow, social-follow-network, toggle, pricing-tables).
2. `class-divi-dynamic-renderer.php` (menu, fullwidth-menu, divider, search, blog, map, map-pin, dropdown, portfolio, filterable-portfolio, sidebar, post-title, post-content, post-nav, comments, login).
3. `class-divi-woo-renderer.php` (woocommerce-*, shop).
4. `class-divi-generic-renderer.php` (fullwidth fallthrough, before-after-image, canvas-portal, breadcrumbs, link, post-slider, signup, signup-custom-field, and true metadata fallback).
5. **Verificar.**

### Fase 7: Eliminar el monolito
1. Eliminar todos los `elseif` GROUP del `render_block()`.
2. Reducir `render_block()` a dispatcher puro con mapa de slugs.
3. **Verificacion final completa** con diff de post_content.
## 4. Riesgos y mitigaciones

| Riesgo | Impacto | Mitigacion |
|--------|---------|------------|
| Mapa de slugs incompleto o duplicado | Bloque rutea al renderer equivocado | Mapa unico en dispatcher, una sola fuente de verdad. Lista generada a partir de slugs actuales. |
| Base renderer no cubre todos los casos | Bloques pierden attrs | Extraer helpers primero (Fase 1) y validar binario identico antes de mover grupos. |
| Auto-wrap diferente entre renderers | Inconsistencia | Auto-wrap vive en `Divi_Base_Renderer`; `dgpc` reutiliza helpers puros via trait. |
| `dgpc` renderer pierde normalizacion | Carrusel sin `gcid` conversion | `convert_gcid_to_variable_syntax` centralizado en trait, aplicado en dispatcher post-render. |
| Generic renderer asume metadata fallback amplio | Modulos no manejados rompen | Metadata fallback solo para el 1 modulo real (`divi/counters`). Renderers especificos cubren slugs usados. |
| Perdida de `children_html`/`inner_html` dual | Contenedores vacios o duplicados | Contrato explicito `inner` + `inner_html`; dispatcher respeta `content_key` igual que hoy. |
| Sin tests automatizados | Regresiones manuales | Crear script de diff de post_content para page-defs activos y `content_state/local/inicio.txt`. |
| Orden de post-proceso cambia | Gradientes/gcid mal aplicados | Centralizar post-proceso en dispatcher (gcid, gradient, background) y no en renderers. |

## 5. Criterios de aceptacion

1. **Pagina 127774 desplegada sin error** (`array_keys()` desaparece).
2. **`dgpc/product-carousel` desplegable** con la estructura correcta de `innerContent.desktop.value`.
3. **Renderers testables aisladamente** (test unitario por renderer) y **diff binario** de post_content para page-defs activos.
4. **Monolito eliminado** — `render_block()` < 100 lineas.
5. **Namespace nuevo agregable** sin tocar codigo existente: registrar nuevo renderer en dispatcher + mapa de slugs.
6. **Verificacion por fase** — cada fase se valida con deploy y diff antes de la siguiente.
7. **Compatibilidad con `content_state`**: al menos `inicio.txt` (contiene `dgpc/product-carousel`) round-trip sin cambios estructurales.