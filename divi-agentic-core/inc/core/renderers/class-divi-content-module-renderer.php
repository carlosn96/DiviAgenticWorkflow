<?php
/**
 * Renderer: Divi Content Module
 *
 * Handles content-heavy Divi modules: blurb, number-counter, counter, circle-counter,
 * icon, toggle, accordion-item, slide, tab, video-slider-item, cta, testimonial,
 * team-member, pricing-table, fullwidth-header, countdown-timer.
 *
 * @package Divi_Agentic_Core
 */

namespace Divi_Agentic_Core\Core\Renderers;

require_once __DIR__ . '/class-divi-base-renderer.php';

/**
 * Class Divi_ContentModule_Renderer
 */
class Divi_ContentModule_Renderer extends Divi_Base_Renderer {

	/**
	 * @inheritDoc
	 */
	public function render( string $slug, array $data, string $content_key, string $children_html ): array {
		$attrs = $this->prepare_base_attrs( $data, $data['builderVersion'] ?? DIVI_BUILDER_VERSION );

		switch ( $slug ) {
			case 'divi/blurb':
				$this->render_blurb( $data, $attrs );
				break;

			case 'divi/number-counter':
			case 'divi/counter':
			case 'divi/circle-counter':
				$this->render_counter( $data, $attrs );
				break;

			case 'divi/icon':
				$this->render_icon( $data, $attrs );
				break;

			case 'divi/toggle':
				$this->render_toggle( $data, $attrs );
				break;

			case 'divi/accordion-item':
			case 'divi/slide':
			case 'divi/tab':
			case 'divi/video-slider-item':
				$this->render_child_content( $data, $attrs );
				break;

			case 'divi/cta':
				$this->render_cta( $data, $attrs );
				break;

			case 'divi/testimonial':
				$this->render_testimonial( $data, $attrs );
				break;

			case 'divi/team-member':
				$this->render_team_member( $data, $attrs );
				break;

			case 'divi/pricing-table':
				$this->render_pricing_table( $data, $attrs );
				break;

			case 'divi/fullwidth-header':
				$this->render_fullwidth_header( $data, $attrs );
				break;

			case 'divi/countdown-timer':
				$this->render_countdown_timer( $data, $attrs );
				break;
		}

		return [
			'attrs'      => $attrs,
			'inner'      => '',
			'inner_html' => '',
		];
	}

	/**
	 * Set title/content innerContent, handling flat and structured values.
	 *
	 * @param array $data Source data.
	 * @param array $attrs Output attrs (passed by reference).
	 * @param array $keys Keys to map.
	 */
	private function set_text_attrs( array $data, array &$attrs, array $keys ): void {
		foreach ( $keys as $key ) {
			if ( ! isset( $data[ $key ] ) ) {
				continue;
			}
			if ( is_array( $data[ $key ] ) && isset( $data[ $key ]['innerContent'] ) ) {
				$value = $data[ $key ]['innerContent']['desktop']['value'] ?? '';
			} else {
				$value = $data[ $key ];
			}
			$attrs[ $key ]['innerContent'] = [ 'desktop' => [ 'value' => $value ] ];
		}
	}

	/**
	 * Render blurb.
	 */
	private function render_blurb( array $data, array &$attrs ): void {
		$this->set_text_attrs( $data, $attrs, [ 'title', 'content' ] );

		// Divi 5 blurb expects title.innerContent.desktop.value as {text: "..."}
		if ( isset( $attrs['title']['innerContent']['desktop']['value'] ) && is_string( $attrs['title']['innerContent']['desktop']['value'] ) ) {
			$raw = $attrs['title']['innerContent']['desktop']['value'];
			$attrs['title']['innerContent']['desktop']['value'] = [ 'text' => $raw ];
		}

		if ( isset( $data['imageIcon'] ) ) {
			$attrs['imageIcon'] = $data['imageIcon'];
		} elseif ( isset( $data['icon'] ) ) {
			$icon_data = $data['icon'];
			if ( is_array( $icon_data ) ) {
				$icon_unicode = $icon_data['unicode'] ?? '';
				$icon_type    = $icon_data['type'] ?? 'divi';
				$icon_weight  = $icon_data['weight'] ?? '400';
			} else {
				$icon_unicode = $icon_data;
				$icon_type    = 'divi';
				$icon_weight  = '400';
			}
			$attrs['imageIcon']['innerContent'] = [
				'desktop' => [ 'value' => [
					'useIcon'   => 'on',
					'icon'      => [
						'unicode' => $icon_unicode,
						'type'    => $icon_type,
						'weight'  => $icon_weight,
					],
					'src'       => '',
					'animation' => 'off',
				] ],
			];
		}
	}

	/**
	 * Render counter modules.
	 */
	private function render_counter( array $data, array &$attrs ): void {
		$title_value = $data['title'] ?? '';
		if ( is_array( $title_value ) ) {
			$title_value = $title_value['innerContent']['desktop']['value'] ?? ( $data['label'] ?? '' );
		}
		if ( '' === $title_value && isset( $data['label'] ) ) {
			$title_value = $data['label'];
		}
		$attrs['title']['innerContent'] = [ 'desktop' => [ 'value' => $title_value ] ];

		if ( isset( $data['enablePercentSign'] ) ) {
			$attrs['number']['advanced']['enablePercentSign'] = [ 'desktop' => [ 'value' => $data['enablePercentSign'] ] ];
		}

		$number_raw = $data['number'] ?? '0';
		if ( is_array( $number_raw ) ) {
			$number_val = $number_raw['innerContent']['desktop']['value'] ?? '0';
		} else {
			$number_val = $number_raw;
		}
		if ( is_string( $number_val ) && strpos( $number_val, '%' ) !== false ) {
			$number_val = str_replace( '%', '', $number_val );
			if ( ! isset( $data['enablePercentSign'] ) ) {
				$attrs['number']['advanced']['enablePercentSign'] = [ 'desktop' => [ 'value' => 'on' ] ];
			}
		}
		$attrs['number']['innerContent'] = [ 'desktop' => [ 'value' => $number_val ] ];

		$this->propagate_font( $data, $attrs, 'headingFont', 'number', 'font' );
		$this->propagate_font( $data, $attrs, 'bodyFont', 'title', 'font' );
	}

	/**
	 * Render icon module.
	 */
	private function render_icon( array $data, array &$attrs ): void {
		if ( isset( $data['icon'] ) ) {
			$attrs['icon']['innerContent'] = [
				'desktop' => [ 'value' => [
					'icon'    => $data['icon'],
					'link'    => $data['link'] ?? '',
					'linkUrl' => $data['link_url'] ?? '',
				] ],
			];
		}
	}

	/**
	 * Render toggle.
	 */
	private function render_toggle( array $data, array &$attrs ): void {
		$this->set_text_attrs( $data, $attrs, [ 'title', 'content' ] );
		if ( isset( $data['headingFont'] ) && is_array( $data['headingFont'] ) ) {
			$attrs['title']['decoration']['font']['font'] = $data['headingFont'];
			unset( $attrs['module']['headingFont'] );
		}
		if ( isset( $data['bodyFont'] ) ) {
			$attrs['content']['decoration']['bodyFont'] = $data['bodyFont'];
			unset( $attrs['module']['bodyFont'] );
		}
		foreach ( [ 'openToggle', 'closedToggle', 'openToggleIcon', 'closedToggleIcon' ] as $tk ) {
			if ( isset( $data[ $tk ] ) ) {
				$attrs[ $tk ] = $data[ $tk ];
			}
		}
	}

	/**
	 * Render child content modules (accordion-item, slide, tab, video-slider-item).
	 */
	private function render_child_content( array $data, array &$attrs ): void {
		$this->set_text_attrs( $data, $attrs, [ 'title', 'content' ] );
		foreach ( [ 'title', 'content' ] as $key ) {
			if ( isset( $data[ $key ] ) && is_array( $data[ $key ] ) ) {
				foreach ( [ 'advanced', 'decoration' ] as $k ) {
					if ( isset( $data[ $key ][ $k ] ) ) {
						$attrs[ $key ][ $k ] = $data[ $key ][ $k ];
					}
				}
			}
		}
		if ( isset( $data['src'] ) ) {
			$attrs['image']['innerContent'] = [ 'desktop' => [ 'value' => [ 'src' => $data['src'], 'alt' => $data['alt'] ?? '' ] ] ];
		}
		if ( isset( $data['button_text'] ) ) {
			$attrs['button']['innerContent'] = [ 'desktop' => [ 'value' => [
				'text'    => $data['button_text'],
				'linkUrl' => $data['button_url'] ?? '#',
			] ] ];
		}
		if ( isset( $data['button'] ) && is_array( $data['button'] ) ) {
			foreach ( [ 'advanced', 'decoration' ] as $k ) {
				if ( isset( $data['button'][ $k ] ) ) {
					$attrs['button'][ $k ] = $data['button'][ $k ];
				}
			}
		}
	}

	/**
	 * Render CTA.
	 */
	private function render_cta( array $data, array &$attrs ): void {
		$this->set_text_attrs( $data, $attrs, [ 'title', 'content' ] );

		// Preserve fully-qualified button attrs (decoration, etc.).
		if ( isset( $data['button'] ) && is_array( $data['button'] ) ) {
			$attrs['button'] = array_replace_recursive( $attrs['button'] ?? [], $data['button'] );
		}

		if ( isset( $data['button_text'] ) ) {
			$attrs['button']['innerContent'] = [ 'desktop' => [ 'value' => [
				'text'    => $data['button_text'],
				'linkUrl' => $data['button_url'] ?? '#',
			] ] ];
		}
		// Map flat button styling (button.desktop.value.*) to Divi 5 nested path
		// (button.decoration.button.desktop.value.*) expected by divi/cta.
		if ( isset( $attrs['button'] ) && is_array( $attrs['button'] ) ) {
			$btn_decoration = [];
			foreach ( [ 'desktop', 'tablet', 'phone', 'hover' ] as $state_key ) {
				if ( ! isset( $attrs['button'][ $state_key ]['value'] ) ) {
					continue;
				}
				$vals = $attrs['button'][ $state_key ]['value'];
				if ( 'hover' === $state_key ) {
					$btn_decoration['button']['desktop']['hover'] = $vals;
				} else {
					$btn_decoration['button'][ $state_key ]['value'] = $vals;
				}
			}
			if ( ! empty( $btn_decoration ) ) {
				$attrs['button']['decoration'] = $btn_decoration;
			}
			// Remove flat state keys so they don't conflict.
			foreach ( [ 'desktop', 'tablet', 'phone', 'hover' ] as $state_key ) {
				unset( $attrs['button'][ $state_key ] );
			}
		}
	}

	/**
	 * Render testimonial.
	 */
	private function render_testimonial( array $data, array &$attrs ): void {
		$this->set_text_attrs( $data, $attrs, [ 'content' ] );

		// Map bodyFont/headingFont from module level → content.decoration.bodyFont
		foreach ( [ 'bodyFont' => 'bodyFont', 'headingFont' => 'headingFont' ] as $src => $dst ) {
			if ( isset( $attrs['module'][ $src ] ) ) {
				$attrs['content']['decoration'][ $dst ] = $attrs['module'][ $src ];
				unset( $attrs['module'][ $src ] );
			}
		}

		// Preserve decoration/advanced on content and author
		foreach ( [ 'content', 'author' ] as $key ) {
			if ( isset( $data[ $key ] ) && is_array( $data[ $key ] ) ) {
				foreach ( [ 'decoration', 'advanced' ] as $sub ) {
					if ( isset( $data[ $key ][ $sub ] ) ) {
						$attrs[ $key ][ $sub ] = $data[ $key ][ $sub ];
					}
				}
			}
		}
		// Author: support plain string or structured with innerContent
		if ( isset( $data['author'] ) ) {
			if ( is_string( $data['author'] ) ) {
				$attrs['author']['innerContent'] = [ 'desktop' => [ 'value' => $data['author'] ] ];
			} elseif ( is_array( $data['author'] ) && isset( $data['author']['innerContent'] ) ) {
				$attrs['author']['innerContent'] = $data['author']['innerContent'];
			}
		}
		// Portrait: support flat src or nested portrait.src
		if ( isset( $data['portrait']['src'] ) ) {
			$portrait_src = $data['portrait'];
		} elseif ( isset( $data['src'] ) ) {
			$portrait_src = $data;
		}
		if ( isset( $portrait_src ) ) {
			$portrait_value = [ 'src' => $portrait_src['src'], 'alt' => $portrait_src['alt'] ?? '' ];
			foreach ( [ 'id', 'titleText', 'width', 'height' ] as $meta_key ) {
				if ( isset( $portrait_src[ $meta_key ] ) ) {
					$portrait_value[ $meta_key ] = $portrait_src[ $meta_key ];
				}
			}
			$attrs['portrait']['innerContent'] = [ 'desktop' => [ 'value' => $portrait_value ] ];
		}
		if ( isset( $data['quoteIcon'] ) ) {
			$attrs['quoteIcon'] = $data['quoteIcon'];
		}
	}

	/**
	 * Render team member.
	 */
	private function render_team_member( array $data, array &$attrs ): void {
		foreach ( [ 'name', 'position' ] as $key ) {
			if ( isset( $data[ $key ] ) ) {
				$attrs[ $key ] = [ 'innerContent' => [ 'desktop' => [ 'value' => $data[ $key ] ] ] ];
			}
		}
		$this->set_text_attrs( $data, $attrs, [ 'content' ] );
		if ( isset( $data['src'] ) ) {
			$attrs['image']['innerContent'] = [ 'desktop' => [ 'value' => [ 'src' => $data['src'], 'alt' => $data['alt'] ?? '' ] ] ];
		}
	}

	/**
	 * Render pricing table.
	 */
	private function render_pricing_table( array $data, array &$attrs ): void {
		foreach ( [ 'title', 'subtitle', 'price', 'content', 'excluded' ] as $key ) {
			if ( isset( $data[ $key ] ) ) {
				$attrs[ $key ]['innerContent'] = [ 'desktop' => [ 'value' => $data[ $key ] ] ];
			}
		}

		if ( isset( $data['currencyFrequency'] ) ) {
			$cf_raw = $data['currencyFrequency'];
			if ( is_array( $cf_raw ) ) {
				$attrs['currencyFrequency']['innerContent'] = [ 'desktop' => [ 'value' => $cf_raw ] ];
			} else {
				$attrs['currencyFrequency']['innerContent'] = [ 'desktop' => [ 'value' => [
					'currency' => [ 'innerContent' => [ 'desktop' => [ 'value' => $cf_raw ] ] ],
					'per'      => [ 'innerContent' => [ 'desktop' => [ 'value' => '' ] ] ],
				] ] ];
			}
		}

		if ( isset( $data['featured'] ) ) {
			if ( ! isset( $attrs['module']['advanced'] ) ) {
				$attrs['module']['advanced'] = [];
			}
			$attrs['module']['advanced']['featured'] = [ 'desktop' => [ 'value' => $data['featured'] ] ];
		}

		if ( isset( $data['button_text'] ) || isset( $data['button_url'] ) ) {
			$attrs['button']['innerContent'] = [ 'desktop' => [ 'value' => [
				'text'    => $data['button_text'] ?? 'Select',
				'linkUrl' => $data['button_url'] ?? '#',
			] ] ];
		} elseif ( isset( $data['button'] ) && is_array( $data['button'] ) ) {
			$attrs['button'] = $data['button'];
		}
	}

	/**
	 * Render fullwidth header.
	 */
	private function render_fullwidth_header( array $data, array &$attrs ): void {
		$this->set_text_attrs( $data, $attrs, [ 'title', 'content' ] );
		if ( isset( $data['subtitle'] ) ) {
			$attrs['subtitle'] = [ 'innerContent' => [ 'desktop' => [ 'value' => $data['subtitle'] ] ] ];
		}
		if ( isset( $data['button_text'] ) ) {
			$attrs['button']['innerContent'] = [ 'desktop' => [ 'value' => [
				'text'    => $data['button_text'],
				'linkUrl' => $data['button_url'] ?? '#',
			] ] ];
		}
		if ( isset( $data['logo_src'] ) ) {
			$attrs['logo']['innerContent'] = [ 'desktop' => [ 'value' => [ 'src' => $data['logo_src'], 'alt' => $data['logo_alt'] ?? '' ] ] ];
		}
	}

	/**
	 * Render countdown timer.
	 */
	private function render_countdown_timer( array $data, array &$attrs ): void {
		if ( isset( $data['title'] ) ) {
			if ( is_array( $data['title'] ) ) {
				$attrs['title']['innerContent'] = [ 'desktop' => [ 'value' => $data['title']['innerContent']['desktop']['value'] ?? '' ] ];
				if ( isset( $data['title']['decoration'] ) ) {
					$attrs['title']['decoration'] = $data['title']['decoration'];
				}
			} else {
				$attrs['title']['innerContent'] = [ 'desktop' => [ 'value' => $data['title'] ] ];
			}
		}
		if ( isset( $data['content'] ) && is_array( $data['content'] ) ) {
			$attrs['content']['innerContent'] = [ 'desktop' => [ 'value' => $data['content']['innerContent']['desktop']['value'] ?? '' ] ];
			foreach ( [ 'advanced', 'decoration' ] as $k ) {
				if ( isset( $data['content'][ $k ] ) ) {
					$attrs['content'][ $k ] = $data['content'][ $k ];
				}
			}
		}
		foreach ( [ 'number', 'label', 'separator' ] as $attr ) {
			if ( isset( $data[ $attr ] ) && is_array( $data[ $attr ] ) ) {
				foreach ( $data[ $attr ] as $k => $v ) {
					if ( $k !== 'innerContent' && ! isset( $attrs[ $attr ][ $k ] ) ) {
						$attrs[ $attr ][ $k ] = $v;
					}
				}
			}
		}
	}

	/**
	 * Propagate a font key (headingFont/bodyFont) to a target attribute's decoration font.
	 */
	private function propagate_font( array $data, array &$attrs, string $source_key, string $target_attr, string $font_key ): void {
		if ( ! isset( $data[ $source_key ] ) || ! is_array( $data[ $source_key ] ) ) {
			return;
		}
		$font_data = current( $data[ $source_key ] );
		if ( isset( $font_data['font'] ) ) {
			$attrs[ $target_attr ]['decoration'][ $font_key ]['font'] = array_merge(
				$attrs[ $target_attr ]['decoration'][ $font_key ]['font'] ?? [],
				$font_data['font']
			);
		} else {
			$attrs[ $target_attr ]['decoration'][ $font_key ]['font'] = array_merge(
				$attrs[ $target_attr ]['decoration'][ $font_key ]['font'] ?? [],
				$font_data
			);
		}
		unset( $attrs['module'][ $source_key ] );
	}
}
