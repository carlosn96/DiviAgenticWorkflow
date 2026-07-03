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
	 * @inheritDoc
	 */
	public function render( string $slug, array $data, string $content_key, string $children_html ): array {
		$attrs = $this->prepare_base_attrs( $data, $data['builderVersion'] ?? '5.7.4' );

		if ( isset( $data['content'] ) ) {
			$attrs['content']['innerContent'] = [ 'desktop' => [ 'value' => $data['content'] ] ];
		}

		return [
			'attrs'      => $attrs,
			'inner'      => '',
			'inner_html' => '',
		];
	}
}
