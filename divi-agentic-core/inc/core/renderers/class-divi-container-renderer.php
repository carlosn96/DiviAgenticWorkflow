<?php
/**
 * Renderer: Divi Container
 *
 * Handles container/parent blocks: menu, row-inner, group, group-carousel,
 * global-layout, layout, placeholder, slider, video-slider, accordion,
 * tabs, social-media-follow, icon-list, fullwidth-slider, pricing-tables,
 * fullwidth-portfolio.
 *
 * @package Divi_Agentic_Core
 */

namespace Divi_Agentic_Core\Core\Renderers;

require_once __DIR__ . '/class-divi-base-renderer.php';

/**
 * Class Divi_Container_Renderer
 */
class Divi_Container_Renderer extends Divi_Base_Renderer {

	/**
	 * @inheritDoc
	 */
	public function render( string $slug, array $data, string $content_key, string $children_html ): array {
		$attrs = $this->prepare_base_attrs( $data, $data['builderVersion'] ?? '5.7.4' );
		$inner = '';
		$inner_html = '';

		switch ( true ) {
			case in_array( $slug, [ 'divi/menu', 'divi/fullwidth-menu' ], true ):
				if ( isset( $data['menu_id'] ) ) {
					$attrs['menu']['advanced']['menuId'] = [ 'desktop' => [ 'value' => $data['menu_id'] ] ];
				}
				if ( isset( $data['menu'] ) && is_array( $data['menu'] ) ) {
					$attrs['menu'] = array_merge( $attrs['menu'] ?? [], $data['menu'] );
				}
				break;

			case in_array( $slug, [
				'divi/row-inner', 'divi/group', 'divi/group-carousel',
				'divi/global-layout', 'divi/layout', 'divi/placeholder',
			], true ):
				$inner_html = $children_html;
				break;

			case in_array( $slug, [
				'divi/slider', 'divi/video-slider', 'divi/accordion',
				'divi/tabs', 'divi/social-media-follow', 'divi/icon-list',
				'divi/fullwidth-slider', 'divi/pricing-tables', 'divi/fullwidth-portfolio',
			], true ):
				$inner_html = $children_html;
				break;
		}

		return [
			'attrs'      => $attrs,
			'inner'      => $inner,
			'inner_html' => $inner_html,
		];
	}
}
