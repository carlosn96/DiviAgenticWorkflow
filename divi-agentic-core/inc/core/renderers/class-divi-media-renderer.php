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
				// Support flat src or nested image.innerContent.desktop.value.src
				if ( isset( $data['image']['innerContent']['desktop']['value']['src'] ) ) {
					$img_data = $data['image']['innerContent']['desktop']['value'];
				} elseif ( isset( $data['src'] ) ) {
					$img_data = $data;
				}
				if ( isset( $img_data ) ) {
					$img = [
						'src' => $img_data['src'],
						'alt' => $img_data['alt'] ?? '',
					];
					foreach ( [ 'id', 'titleText', 'width', 'height', 'linkUrl' ] as $k ) {
						if ( isset( $img_data[ $k ] ) ) {
							$img[ $k ] = $img_data[ $k ];
						}
					}
					$attrs['image']['innerContent'] = [
						'desktop' => [ 'value' => $img ],
					];
				}

				foreach ( [ 'lightbox', 'overlay', 'overlayIcon' ] as $img_attr ) {
					if ( isset( $data[ $img_attr ] ) ) {
						$attrs['image']['advanced'][ $img_attr ] = [
							'desktop' => [ 'value' => $data[ $img_attr ] ],
						];
					}
				}

				if ( isset( $data['image']['decoration'] ) ) {
					$img_dec = $data['image']['decoration'];
					$dec_modes = [ 'desktop', 'tablet', 'phone', 'hover', 'sticky' ];
					foreach ( [ 'border', 'boxShadow' ] as $dk ) {
						if ( ! isset( $img_dec[ $dk ] ) ) { continue; }
						$cur = $img_dec[ $dk ];
						if ( ! is_array( $cur ) ) {
							$img_dec[ $dk ] = [ 'desktop' => [ 'value' => $cur ] ];
							continue;
						}
						$has_mode = ! empty( array_intersect( $dec_modes, array_keys( $cur ) ) );
						if ( ! $has_mode ) {
							$img_dec[ $dk ] = [ 'desktop' => [ 'value' => $cur ] ];
						}
					}
					$attrs['image']['decoration'] = $img_dec;
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
