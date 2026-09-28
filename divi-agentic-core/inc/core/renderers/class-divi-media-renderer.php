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
		$attrs = $this->prepare_base_attrs( $data, $data['builderVersion'] ?? DIVI_BUILDER_VERSION );

		switch ( $slug ) {
			case 'divi/image':
			case 'divi/fullwidth-image':
				$inner_content = [];

				if ( isset( $data['image']['innerContent'] ) && is_array( $data['image']['innerContent'] ) ) {
					foreach ( [ 'desktop', 'tablet', 'phone' ] as $bp ) {
						if ( isset( $data['image']['innerContent'][ $bp ]['value'] ) ) {
							$bp_val = $data['image']['innerContent'][ $bp ]['value'];
							$src    = $bp_val['src'] ?? '';
							if ( is_string( $src ) && str_starts_with( $src, '/' ) && function_exists( 'home_url' ) ) {
								$src = home_url( $src );
							}
							$bp_img = [
								'src'       => $src,
								'alt'       => $bp_val['alt'] ?? ( $data['alt'] ?? '' ),
								'titleText' => $bp_val['titleText'] ?? ( $data['titleText'] ?? '' ),
							];
							foreach ( [ 'id', 'titleText', 'width', 'height', 'linkUrl', 'linkTarget', 'srcset', 'sizes' ] as $k ) {
								if ( isset( $bp_val[ $k ] ) ) {
									$bp_img[ $k ] = (string) $bp_val[ $k ];
								}
							}
							// Auto-resolve attachment metadata if missing
							if ( ( empty( $bp_img['id'] ) || empty( $bp_img['width'] ) ) && function_exists( 'attachment_url_to_postid' ) && ! empty( $src ) ) {
								$att_id = attachment_url_to_postid( $src );
								if ( $att_id ) {
									if ( empty( $bp_img['id'] ) ) {
										$bp_img['id'] = (string) $att_id;
									}
									$meta = wp_get_attachment_metadata( $att_id );
									if ( empty( $bp_img['width'] ) && ! empty( $meta['width'] ) ) {
										$bp_img['width'] = (string) $meta['width'];
									}
									if ( empty( $bp_img['height'] ) && ! empty( $meta['height'] ) ) {
										$bp_img['height'] = (string) $meta['height'];
									}
								}
							}
							$inner_content[ $bp ] = [ 'value' => $bp_img ];
						}
					}
				} elseif ( isset( $data['src'] ) ) {
					$breakpoints = [ 'desktop', 'tablet', 'phone' ];
					$src_map     = [];

					if ( is_array( $data['src'] ) ) {
						$src_map = $data['src'];
					} else {
						$src_map['desktop'] = $data['src'];
						if ( isset( $data['src_tablet'] ) || isset( $data['tablet']['src'] ) ) {
							$src_map['tablet'] = $data['src_tablet'] ?? $data['tablet']['src'];
						}
						if ( isset( $data['src_phone'] ) || isset( $data['phone']['src'] ) ) {
							$src_map['phone'] = $data['src_phone'] ?? $data['phone']['src'];
						}
					}

					foreach ( $breakpoints as $bp ) {
						if ( ! isset( $src_map[ $bp ] ) ) {
							continue;
						}
						$src = $src_map[ $bp ];
						if ( is_string( $src ) && str_starts_with( $src, '/' ) && function_exists( 'home_url' ) ) {
							$src = home_url( $src );
						}
						$bp_img = [
							'src' => $src,
							'alt' => $data['alt'] ?? '',
						];
						foreach ( [ 'id', 'titleText', 'width', 'height', 'linkUrl', 'linkTarget', 'srcset', 'sizes' ] as $k ) {
							if ( isset( $data[ $k ] ) ) {
								$bp_img[ $k ] = (string) $data[ $k ];
							}
						}
						// Auto-resolve attachment metadata if missing
						if ( ( empty( $bp_img['id'] ) || empty( $bp_img['width'] ) ) && function_exists( 'attachment_url_to_postid' ) && ! empty( $src ) ) {
							$att_id = attachment_url_to_postid( $src );
							if ( $att_id ) {
								$bp_img['id'] = (string) $att_id;
								$meta = wp_get_attachment_metadata( $att_id );
								if ( empty( $bp_img['width'] ) && ! empty( $meta['width'] ) ) {
									$bp_img['width'] = (string) $meta['width'];
								}
								if ( empty( $bp_img['height'] ) && ! empty( $meta['height'] ) ) {
									$bp_img['height'] = (string) $meta['height'];
								}
								if ( empty( $bp_img['titleText'] ) ) {
									$att_post = get_post( $att_id );
									if ( $att_post && ! empty( $att_post->post_title ) ) {
										$bp_img['titleText'] = $att_post->post_title;
									}
								}
							}
						}
						$inner_content[ $bp ] = [ 'value' => $bp_img ];
					}
				}

				if ( ! empty( $inner_content ) ) {
					$attrs['image']['innerContent'] = $inner_content;
				}

				foreach ( [ 'lightbox', 'overlay', 'overlayIcon' ] as $img_attr ) {
					if ( isset( $data[ $img_attr ] ) ) {
						$attrs['image']['advanced'][ $img_attr ] = [
							'desktop' => [ 'value' => $data[ $img_attr ] ],
						];
					}
				}

				// Build image.decoration: explicit $data['image']['decoration'] first,
				// then inherit border/boxShadow from top-level decoration (common pattern in page-defs).
				$img_dec = [];
				if ( isset( $data['image']['decoration'] ) ) {
					$img_dec = $data['image']['decoration'];
				}
				$inherited = false;
				if ( isset( $data['decoration'] ) ) {
					foreach ( [ 'border', 'boxShadow' ] as $dk ) {
						if ( isset( $data['decoration'][ $dk ] ) && ! isset( $img_dec[ $dk ] ) ) {
							$img_dec[ $dk ] = $data['decoration'][ $dk ];
							$inherited = true;
						}
					}
				}
				if ( ! empty( $img_dec ) ) {
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
					// Remove inherited border/boxShadow from module.decoration to avoid duplication
					if ( $inherited ) {
						foreach ( [ 'border', 'boxShadow' ] as $dk ) {
							unset( $attrs['module']['decoration'][ $dk ] );
						}
						if ( isset( $attrs['module']['decoration'] ) && empty( $attrs['module']['decoration'] ) ) {
							unset( $attrs['module']['decoration'] );
						}
					}
				}
				break;

			case 'divi/video':
				if ( isset( $data['video'] ) ) {
					$attrs['video'] = $data['video'];
				} elseif ( isset( $data['src'] ) ) {
					$val = [ 'src' => $data['src'] ];
					if ( ! empty( $data['webm'] ) ) {
						$val['webm'] = $data['webm'];
					}
					$attrs['video']['innerContent'] = [
						'desktop' => [ 'value' => $val ],
						'tablet'  => [ 'value' => $val ],
						'phone'   => [ 'value' => $val ],
					];
				}
				break;

			case 'divi/audio':
				if ( isset( $data['audio'] ) ) {
					$attrs['audio'] = $data['audio'];
				} elseif ( isset( $data['src'] ) ) {
					$attrs['audio']['innerContent'] = [
						'desktop' => [ 'value' => [
							'src' => $data['src'],
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
