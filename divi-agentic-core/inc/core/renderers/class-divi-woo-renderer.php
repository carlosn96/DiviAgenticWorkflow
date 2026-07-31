<?php
/**
 * Renderer: Divi WooCommerce
 *
 * Handles all divi/woocommerce-* blocks plus divi/shop.
 *
 * @package Divi_Agentic_Core
 */

namespace Divi_Agentic_Core\Core\Renderers;

require_once __DIR__ . '/class-divi-base-renderer.php';

/**
 * Class Divi_Woo_Renderer
 */
class Divi_Woo_Renderer extends Divi_Base_Renderer {

	/**
	 * Extra top-level attrs for woo blocks.
	 */
	private const EXTRA_ATTRS = [ 'elements', 'breadcrumb', 'ordering', 'product', 'posts', 'details' ];

	/**
	 * @inheritDoc
	 */
	public function render( string $slug, array $data, string $content_key, string $children_html ): array {
		$attrs = $this->prepare_base_attrs( $data, $data['builderVersion'] ?? DIVI_BUILDER_VERSION );

		if ( isset( $data['content'] ) ) {
			$attrs['content'] = $data['content'];
		}

		foreach ( self::EXTRA_ATTRS as $key ) {
			if ( isset( $data[ $key ] ) ) {
				$attrs[ $key ] = $data[ $key ];
			}
		}

		return [
			'attrs'      => $attrs,
			'inner'      => '',
			'inner_html' => '',
		];
	}
}
