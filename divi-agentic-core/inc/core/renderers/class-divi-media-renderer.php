<?php
/**
 * Renderer: Divi Media
 *
 * Handles image, fullwidth-image, gallery, video, audio, lottie, svg.
 *
 * @package Divi_Agentic_Core
 */

namespace Divi_Agentic_Core\Core\Renderers;

require_once __DIR__ . '/class-divi-base-renderer.php';

/**
 * Class Divi_Media_Renderer
 */
class Divi_Media_Renderer extends Divi_Base_Renderer {

	/**
	 * @inheritDoc
	 */
	public function render( string $slug, array $data, string $content_key, string $children_html ): array {
		$attrs = $this->prepare_base_attrs( $data, $data['builderVersion'] ?? '5.7.4' );

		switch ( $slug ) {
			case 'divi/image':
			case 'divi/fullwidth-image':
				if ( isset( $data['src'] ) ) {
					$attrs['image']['innerContent'] = [
						'desktop' => [ 'value' => [
							'src' => $data['src'],
							'alt' => $data['alt'] ?? '',
						] ],
					];
				}
				break;

			case 'divi/video':
			case 'divi/audio':
				if ( isset( $data['src'] ) ) {
					$attrs['video']['innerContent'] = [
						'desktop' => [ 'value' => [
							'video' => $data['src'],
							'webm'  => $data['webm'] ?? '',
						] ],
					];
				}
				break;

			case 'divi/gallery':
				if ( isset( $data['gallery_ids'] ) ) {
					$attrs['image']['advanced']['galleryIds'] = [ 'desktop' => [ 'value' => $data['gallery_ids'] ] ];
				}
				if ( isset( $data['fullwidth'] ) ) {
					$attrs['module']['advanced']['fullwidth'] = [ 'desktop' => [ 'value' => $data['fullwidth'] ] ];
				}
				break;

			case 'divi/lottie':
				if ( isset( $data['src'] ) ) {
					$attrs['lottie'] = [ 'innerContent' => [ 'desktop' => [ 'value' => $data['src'] ] ] ];
				}
				break;

			case 'divi/svg':
				if ( isset( $data['content'] ) ) {
					$attrs['content']['innerContent'] = [ 'desktop' => [ 'value' => $data['content'] ] ];
				}
				break;
		}

		return [
			'attrs'      => $attrs,
			'inner'      => '',
			'inner_html' => '',
		];
	}
}
