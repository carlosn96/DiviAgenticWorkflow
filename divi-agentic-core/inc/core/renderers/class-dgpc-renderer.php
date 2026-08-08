<?php
/**
 * Renderer: DGPCommerce
 *
 * Handles all `dgpc/*` third-party blocks (currently only product-carousel).
 *
 * @package Divi_Agentic_Core
 */

namespace Divi_Agentic_Core\Core\Renderers;

require_once __DIR__ . '/interface-block-renderer.php';
require_once __DIR__ . '/trait-block-helpers.php';

/**
 * ARCHIVO DE REFERENCIA PARA ATRIBUTOS DE FUENTE DGPC
 *
 * El plugin DGPC (DiviGear Product Carousel) tiene una tabla de conversion
 * oficial en:
 *   wp-content/plugins/dg-product-carousel/Builder/Server/modules-json/
 *     product-carousel/conversion-outline.json
 *
 * Esa tabla mapea las claves de fuente de Divi 4 a las rutas de atributos
 * de Divi 5. El mapa canonico es:
 *
 *   D4 font key   → Ruta D5
 *   ────────────     ─────────────
 *   title (schema key)       → title_text.decoration.font
 *   price (schema key)       → price_text.decoration.font
 *   description (schema key) → description_text.decoration.font
 *   sale (schema key)        → sale_text.decoration.font
 *   cart (schema key)        → cart_button.decoration.font
 *
 * FORMATO DE DATOS DE FUENTE EN D5:
 *   La ruta D5 (e.g. cart_button.decoration.font) debe contener un objeto
 *   fuente en el formato canonico de Divi 5 (single-nested font):
 *     { font: { desktop: { value: { fontFamily, color, size, textAlign, ... } } } }
 *   normalize_dgpc_font() acepta tanto este formato como el legacy
 *   double-nested {font:{font:{desktop:{value:{...}}}}} y siempre
 *   retorna single-nested.
 *   El contenedor exterior { decoration: { font: ... } } lo agrega este
 *   renderer en el bucle font_map mas abajo.
 *
 * ERROR CORREGIDO (2026-07-28):
 *   Antes este bucle almacenaba los datos de fuente directamente como
 *   atributos top-level (e.g. attrs['cart'] = { font: { font: ... } }),
 *   SIN el wrapper decoration.font y SIN renombrar cart → cart_button.
 *   Divi 5 no aplicaba los estilos porque los datos quedaban en la ruta
 *   incorrecta. Ahora se usa font_map + wrapper decoration.font.
 */

/**
 * Class Dgpc_Renderer
 */
class Dgpc_Renderer implements Block_Renderer_Interface {
	use Block_Helpers;

	/** @var string|null Divi builder version injected from dispatcher. */
	private ?string $builder_version = null;

	/**
	 * Constructor.
	 *
	 * @param string $builder_version Divi builder version.
	 */
	public function __construct( string $builder_version = DIVI_BUILDER_VERSION ) {
		$this->builder_version = $builder_version;
	}

	/**
	 * Render a DGPCommerce block.
	 *
	 * @param string $slug          Block slug.
	 * @param array  $data         Raw schema data.
	 * @param string $content_key  Ignored (dgpc blocks do not render Divi children).
	 * @param string $children_html Ignored.
	 *
	 * @return array{attrs: array, inner: string, inner_html: string}
	 */
	public function render( string $slug, array $data, string $content_key, string $children_html ): array {
		$attrs = $this->build_product_carousel_attrs( $data );

		return [
			'attrs'      => $attrs,
			'inner'      => '',
			'inner_html' => '',
		];
	}

	/**
	 * Normalize font data to Divi 5 canonical format.
	 *
	 * Divi 5 font groups store values as {font:{desktop:{value:{...}}}}.
	 * This function accepts either that canonical form or the legacy
	 * double-nested {font:{font:{desktop:{value:{...}}}}} and always
	 * returns the single-nested D5 form.
	 *
	 * @param mixed $font_data Raw font data from schema.
	 * @return array|null Normalized font data or null.
	 */
	private function normalize_dgpc_font( $font_data ): ?array {
		if ( ! is_array( $font_data ) || empty( $font_data ) ) {
			return null;
		}

		// D5 canonical: {font:{desktop:{value:{...}}}}
		if ( isset( $font_data['font']['desktop']['value'] ) ) {
			return $font_data;
		}

		// Legacy double-nested: {font:{font:{desktop:{value:{...}}}}}
		// Unwrap to remove the extra font layer.
		if ( isset( $font_data['font']['font']['desktop']['value'] ) ) {
			return [
				'font' => $font_data['font']['font'],
			];
		}

		return null;
	}

	/**
	 * Build attributes for the DGPCommerce Product Carousel block.
	 *
	 * This is a non-native Divi 5 block that stores its own settings as
	 * top-level attrs (plus a module{} wrapper for decoration/advanced/meta).
	 *
	 * @param array $data Raw block data.
	 * @return array Block attributes.
	 */
	private function build_product_carousel_attrs( array $data ): array {
		$attrs = [
			'builderVersion' => $data['builderVersion'] ?? $this->builder_version,
			'module'         => [],
		];

		// Decoration/advanced/meta are kept inside module{} as Divi 5 does for
		// third-party blocks (see inicio.txt content_state).
		foreach ( [ 'decoration', 'advanced', 'meta' ] as $key ) {
			if ( isset( $data[ $key ] ) && ! empty( $data[ $key ] ) ) {
				$attrs['module'][ $key ] = $data[ $key ];
			}
		}

		// Module-level CSS class / ID from schema.
		$module_class = $data['module_class'] ?? '';
		$module_id    = $data['module_id'] ?? '';
		if ( ! empty( $module_class ) || ! empty( $module_id ) ) {
			$html_attrs = [];
			if ( ! empty( $module_class ) ) {
				$html_attrs['class'] = $module_class;
			}
			if ( ! empty( $module_id ) ) {
				$html_attrs['id'] = $module_id;
			}
			if ( ! isset( $attrs['module']['advanced'] ) ) {
				$attrs['module']['advanced'] = [];
			}
			$attrs['module']['advanced']['htmlAttributes'] = [
				'desktop' => [ 'value' => $html_attrs ],
			];
		}

		// Custom CSS at block level (freeForm).
		if ( isset( $data['css'] ) ) {
			$css = $data['css'];
			if ( is_string( $css ) ) {
				$attrs['css'] = [ 'desktop' => [ 'value' => [ 'freeForm' => $css ] ] ];
			} elseif ( is_array( $css ) ) {
				foreach ( [ 'desktop', 'tablet', 'phone' ] as $bp ) {
					if ( isset( $css[ $bp ] ) ) {
						$bp_css = $css[ $bp ];
						if ( is_string( $bp_css ) ) {
							$attrs['css'][ $bp ] = [ 'value' => [ 'freeForm' => $bp_css ] ];
						} elseif ( is_array( $bp_css ) ) {
							$attrs['css'][ $bp ] = $bp_css;
						}
					}
				}
			}
		}

		// Carousel-specific settings are stored as top-level attrs.
		// Keys correspond to the module.json attribute names. The schema uses
		// the canonical Divi 5 shape {"innerContent":{"desktop":{"value":...}}}
		// which must be PRESERVED so the D4 module hydrates $this->props.
		$carousel_keys = [
			'type', 'include_categories', 'posts_number', 'orderby',
			'add_to_cart', 'product_description', 'description_full',
			'show_items_desktop', 'show_items_tablet', 'show_items_mobile',
			'multislide', 'item_spacing', 'transition_duration', 'centermode',
			'loop', 'autoplay', 'hoverpause', 'autoplay_speed', 'arrow_nav',
			'dot_nav', 'dot_alignment', 'equal_height', 'item_vertical_align',
			'effect', 'coverflow_rotate', 'slide_shadow',
			'overlay', 'ovarlay_color', 'sale_badge_backgeound',
			'cart_button_position', 'cart_button_alignment',
			'add_to_cart_on_bottom', 'cart_button_full',
			'cart_background', 'cart_background_hover',
			'review_color', 'review_bg_color',
			'use_prev_icon', 'prev_icon', 'use_next_icon', 'next_icon',
			'nav_font_size', 'arrow_color', 'arrow_background',
			'arrow_circle', 'arrow_on_hover', 'arrow_inside',
			'dots_color', 'dots_active_color', 'dot_circle',
			'image_hover_scale', 'title_on_top', 'hide_the_title',
			'price_on_top', 'hide_the_price',
			'background_hover_set', 'background_hover',
			'title_hover', 'title_hover_color',
			'price_hover', 'price_hover_color',
			'description_hover', 'description_hover_color',
			'content_margin', 'content_spacing',
			'content_margin_top', 'content_spacing_top',
			'add_to_cart_margin', 'add_to_cart_padding',
			'background_color', 'border_radii',
		];
		foreach ( $carousel_keys as $key ) {
			if ( ! isset( $data[ $key ] ) ) {
				continue;
			}
			// Preserve the innerContent wrapper shape — Divi 5 needs it to
			// hydrate the D4 module's $this->props. Unwrapping to a flat
			// value breaks the D4 render pipeline.
			$attrs[ $key ] = $data[ $key ];
		}

		// The product carousel's "type" attribute (e.g. product_category)
		// collides with the structural "type" key used by the Layout Engine
		// to identify the block slug. Schema authors use "type_attr" or
		// "carousel_type" to disambiguate; map them back to "type".
		foreach ( [ 'type_attr', 'carousel_type' ] as $alias ) {
			if ( isset( $data[ $alias ] ) ) {
				$attrs['type'] = $data[ $alias ];
				break;
			}
		}

		// Typography sub-fields — map D4 font keys (from schema) to D5 attr paths
		// conversion-outline.json: {title→title_text, price→price_text, description→description_text, sale→sale_text, cart→cart_button}
		// D5 expects {key: {decoration: {font: {font: {desktop: {value: ...}}}}}}
		// Output at attr[key] = {key: {decoration: {font: $normalized}}}
		// where $normalized is always {font:{desktop:{value:{...}}}}
		$font_map = [
			'title'       => 'title_text',
			'price'       => 'price_text',
			'description' => 'description_text',
			'sale'        => 'sale_text',
			'cart'        => 'cart_button',
		];
		foreach ( $font_map as $d4_key => $d5_key ) {
			if ( ! isset( $data[ $d4_key ] ) ) {
				continue;
			}
			$normalized = $this->normalize_dgpc_font( $data[ $d4_key ] );
			if ( $normalized !== null ) {
				$attrs[ $d5_key ] = [ 'decoration' => [ 'font' => $normalized ] ];
			} else {
				$attrs[ $d5_key ] = $data[ $d4_key ];
			}
		}

		return $attrs;
	}
}
