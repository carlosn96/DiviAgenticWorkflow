<?php
/**
 * Renderer: Divi Dynamic
 *
 * Handles dynamic template blocks: post-title, post-content, post-nav,
 * comments, fullwidth-post-title, fullwidth-post-content.
 *
 * @package Divi_Agentic_Core
 */

namespace Divi_Agentic_Core\Core\Renderers;

require_once __DIR__ . '/class-divi-base-renderer.php';

/**
 * Class Divi_Dynamic_Renderer
 */
class Divi_Dynamic_Renderer extends Divi_Base_Renderer {

	/**
	 * Extra top-level attrs to pass through for dynamic blocks.
	 */
	private const EXTRA_ATTRS = [ 'title', 'meta', 'textWrapper', 'image', 'content', 'elements', 'featuredImage' ];

	/**
	 * @inheritDoc
	 */
	public function render( string $slug, array $data, string $content_key, string $children_html ): array {
		$attrs = $this->prepare_base_attrs( $data, $data['builderVersion'] ?? DIVI_BUILDER_VERSION );

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
