<?php
/**
 * Renderer: Divi Button
 *
 * Handles divi/button including flat keys and module.decoration.button remap.
 *
 * @package Divi_Agentic_Core
 */

namespace Divi_Agentic_Core\Core\Renderers;

require_once __DIR__ . '/class-divi-base-renderer.php';

/**
 * Class Divi_Button_Renderer
 */
class Divi_Button_Renderer extends Divi_Base_Renderer {

	/**
	 * @inheritDoc
	 */
	public function render( string $slug, array $data, string $content_key, string $children_html ): array {
		$attrs = $this->prepare_base_attrs( $data, $data['builderVersion'] ?? '5.7.4' );

		if ( isset( $data['button_text'] ) ) {
			$attrs['button']['innerContent'] = [
				'desktop' => [ 'value' => [
					'text'       => $data['button_text'],
					'linkUrl'    => $data['button_url'] ?? '#',
					'linkTarget' => 'off',
					'rel'        => [],
				] ],
			];
		}

		// Map the custom preset attributes under module.decoration.button
		// to standard Divi 5 button attributes under button.decoration.
		if ( isset( $attrs['module']['decoration']['button'] ) ) {
			$btn_styles = $attrs['module']['decoration']['button'];
			unset( $attrs['module']['decoration']['button'] );

			if ( ! isset( $attrs['button']['decoration'] ) ) {
				$attrs['button']['decoration'] = [];
			}

			$target_dec = &$attrs['button']['decoration'];

			foreach ( [ 'desktop', 'tablet', 'phone', 'hover' ] as $state_key ) {
				if ( ! isset( $btn_styles[ $state_key ]['value'] ) ) {
					continue;
				}
				$vals = $btn_styles[ $state_key ]['value'];

				$breakpoint = 'desktop';
				$state      = 'value';

				if ( in_array( $state_key, [ 'desktop', 'tablet', 'phone' ], true ) ) {
					$breakpoint = $state_key;
					$state      = 'value';
				} elseif ( $state_key === 'hover' ) {
					$breakpoint = 'desktop';
					$state      = 'hover';
				}

				$val = $vals;

				// 1. Background Color.
				if ( isset( $val['backgroundColor'] ) ) {
					$target_dec['background'][ $breakpoint ][ $state ]['color'] = $val['backgroundColor'];
				}

				// 2. Text Color.
				$btn_color = $val['textColor'] ?? $val['color'] ?? null;
				if ( $btn_color !== null ) {
					$target_dec['font']['font'][ $breakpoint ][ $state ]['color'] = $btn_color;
				}

				// 2b. Hover state from VIE's hover-prefixed keys in desktop.value.
				if ( $state_key === 'desktop' ) {
					if ( isset( $val['hoverBackgroundColor'] ) ) {
						$target_dec['background']['desktop']['hover']['color'] = $val['hoverBackgroundColor'];
					}
					$hover_color = $val['hoverColor'] ?? $val['hoverTextColor'] ?? null;
					if ( $hover_color !== null ) {
						$target_dec['font']['font']['desktop']['hover']['color'] = $hover_color;
					}
				}

				// 3. Border Radius.
				if ( isset( $val['borderRadius'] ) ) {
					$rad = $val['borderRadius'];
					$target_dec['border'][ $breakpoint ][ $state ]['radius'] = [
						'topLeft'     => $rad,
						'topRight'    => $rad,
						'bottomRight' => $rad,
						'bottomLeft'  => $rad,
						'sync'        => 'on',
					];
				}

				// 4. Padding.
				if ( isset( $val['padding'] ) ) {
					$pad = $val['padding'];
					if ( is_string( $pad ) ) {
						$parts = preg_split( '/\s+/', trim( $pad ) );
						if ( count( $parts ) === 2 ) {
							$top_bottom = $parts[0];
							$left_right = $parts[1];
							$target_dec['spacing'][ $breakpoint ][ $state ]['padding'] = [
								'top'    => $top_bottom,
								'bottom' => $top_bottom,
								'left'   => $left_right,
								'right'  => $left_right,
							];
						} elseif ( count( $parts ) === 4 ) {
							$target_dec['spacing'][ $breakpoint ][ $state ]['padding'] = [
								'top'    => $parts[0],
								'right'  => $parts[1],
								'bottom' => $parts[2],
								'left'   => $parts[3],
							];
						} else {
							$target_dec['spacing'][ $breakpoint ][ $state ]['padding'] = [
								'top'    => $pad,
								'bottom' => $pad,
								'left'   => $pad,
								'right'  => $pad,
							];
						}
					} else {
						$target_dec['spacing'][ $breakpoint ][ $state ]['padding'] = $pad;
					}
				}

				// 5. Font Styles.
				$btn_family = $val['fontFamily'] ?? $val['font'] ?? null;
				if ( $btn_family !== null ) {
					$target_dec['font']['font'][ $breakpoint ][ $state ]['fontFamily'] = $btn_family;
				}
				if ( isset( $val['fontWeight'] ) ) {
					$target_dec['font']['font'][ $breakpoint ][ $state ]['fontWeight'] = $val['fontWeight'];
				}
				$btn_size = $val['fontSize'] ?? $val['size'] ?? null;
				if ( $btn_size !== null ) {
					$target_dec['font']['font'][ $breakpoint ][ $state ]['size'] = $btn_size;
				}
				if ( isset( $val['letterSpacing'] ) ) {
					$target_dec['font']['font'][ $breakpoint ][ $state ]['letterSpacing'] = $val['letterSpacing'];
				}
				if ( isset( $val['textTransform'] ) ) {
					$target_dec['font']['font'][ $breakpoint ][ $state ]['textTransform'] = $val['textTransform'];
				}

				// 6. Border Styles.
				if ( isset( $val['border'] ) && is_array( $val['border'] ) ) {
					$b_all = $val['border']['all'] ?? [];
					$target_dec['border'][ $breakpoint ][ $state ]['styles']['all'] = $b_all;
				} else {
					if ( isset( $val['borderColor'] ) || isset( $val['borderWidth'] ) || isset( $val['borderStyle'] ) ) {
						$b_color    = $val['borderColor'] ?? '';
						$b_width    = $val['borderWidth'] ?? '';
						$b_style    = $val['borderStyle'] ?? 'solid';
						$border_all = [];
						if ( $b_color !== '' ) {
							$border_all['color'] = $b_color;
						}
						if ( $b_width !== '' ) {
							$border_all['width'] = $b_width;
						}
						if ( $b_style !== '' ) {
							$border_all['style'] = $b_style;
						}
						if ( ! empty( $border_all ) ) {
							$target_dec['border'][ $breakpoint ][ $state ]['styles']['all'] = $border_all;
						}
					}
				}
			}
		}

		return [
			'attrs'      => $attrs,
			'inner'      => '',
			'inner_html' => '',
		];
	}
}
