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
 * Class Dgpc_Renderer
 */
class Dgpc_Renderer implements Block_Renderer_Interface {
	use Block_Helpers;

	/** @var string Divi builder version injected from dispatcher. */
	private string $builder_version;

	/**
	 * Constructor.
	 *
	 * @param string $builder_version Divi builder version.
	 */
	public function __construct( string $builder_version = '5.7.4' ) {
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
	 * Convert a font schema (VIE style) into the flat font.font structure
	 * expected by the dgpc/product-carousel block.
	 *
	 * @param mixed $font_data Raw font data from schema.
	 * @return array|null Normalized font data or null.
	 */
	private function normalize_dgpc_font( $font_data ): ?array {
		if ( ! is_array( $font_data ) || empty( $font_data ) ) {
			return null;
		}

		// Already in the expected shape?
		if ( isset( $font_data['font']['font']['desktop']['value'] ) ) {
			return $font_data;
		}

		// VIE shorthand: { "font": { "desktop": { "value": { ... } } } }
		if ( isset( $font_data['font']['desktop']['value'] ) ) {
			return [
				'font' => [
					'font' => [
						'desktop' => $font_data['font']['desktop'],
					],
				],
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

		// Typography sub-fields are stored as top-level font attrs
		// (title_text, price_text, description, sale, cart).
		$font_keys = [ 'title_text', 'price_text', 'description', 'sale', 'cart' ];
		foreach ( $font_keys as $key ) {
			if ( ! isset( $data[ $key ] ) ) {
				continue;
			}
			$normalized = $this->normalize_dgpc_font( $data[ $key ] );
			$attrs[ $key ] = $normalized ?? $data[ $key ];
		}

		return $attrs;
	}
}
