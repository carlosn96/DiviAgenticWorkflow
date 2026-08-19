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

		// Merge headingFont into the native title.decoration.font.font path
		// (same unwrap pattern as divi/heading) so Divi emits CSS for the blurb title.
		$hf = $data['headingFont'] ?? null;
		if ( is_array( $hf ) ) {
			$level = $data['titleLevel'] ?? ( $data['title']['level'] ?? 'h4' );
			$level_font = $hf[ $level ] ?? ( $hf['h1'] ?? $hf );
			if ( is_array( $level_font ) ) {
				$font_src = $level_font['font'] ?? $level_font;
				foreach ( [ 'desktop', 'tablet', 'phone' ] as $bp ) {
					if ( isset( $font_src[ $bp ]['value'] ) && is_array( $font_src[ $bp ]['value'] ) ) {
						foreach ( $font_src[ $bp ]['value'] as $k => $v ) {
							$attrs['title']['decoration']['font']['font'][ $bp ]['value'][ $k ] = $v;
						}
					}
				}
				$attrs['title']['decoration']['font']['font']['desktop']['value']['headingLevel'] = $level;
			}
			unset( $attrs['module']['headingFont'] );
		}

		// Body font → content.decoration.bodyFont (native Divi 5 path for blurb content)
		$bf = $data['bodyFont'] ?? null;
		if ( is_array( $bf ) ) {
			$attrs['content']['decoration']['bodyFont'] = $bf;
			unset( $attrs['module']['bodyFont'] );
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

		// icon_advanced → imageIcon.advanced (color, placement, size, etc.)
		$adv = $data['icon_advanced'] ?? $data['iconAdvanced'] ?? null;
		if ( $adv && is_array( $adv ) ) {
			if ( isset( $adv['desktop']['value'] ) && is_array( $adv['desktop']['value'] ) ) {
				foreach ( $adv['desktop']['value'] as $key => $val ) {
					$attrs['imageIcon']['advanced'][ $key ] = [ 'desktop' => [ 'value' => $val ] ];
				}
			}
			$map = [ 'color' => 'color', 'size' => 'size', 'placement' => 'placement' ];
			foreach ( $map as $src => $dst ) {
				if ( isset( $adv['desktop']['value'][ $src ] ) ) {
					$attrs['imageIcon']['advanced'][ $dst ] = [ 'desktop' => [ 'value' => $adv['desktop']['value'][ $src ] ] ];
				}
			}
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
			// Divi 5 expects icon.innerContent.desktop.value = { unicode, type, weight }.
			// Support both a ready object and the {icon:{unicode,type,weight}} wrapper.
			$icon_val = $data['icon'];
			if ( is_array( $icon_val ) && isset( $icon_val['icon'] ) && is_array( $icon_val['icon'] ) ) {
				$icon_val = $icon_val['icon'];
			}
			if ( is_string( $icon_val ) ) {
				$icon_val = [ 'unicode' => $icon_val, 'type' => 'fa', 'weight' => '900' ];
			}
			$attrs['icon']['innerContent'] = [ 'desktop' => [ 'value' => $icon_val ] ];
		}
		$adv = $data['iconAdvanced'] ?? $data['icon_advanced'] ?? null;
		if ( $adv && isset( $adv['desktop']['value'] ) && is_array( $adv['desktop']['value'] ) ) {
			foreach ( $adv['desktop']['value'] as $key => $val ) {
				$attrs['icon']['advanced'][ $key ] = [ 'desktop' => [ 'value' => $val ] ];
			}
		}
	}

	/**
	 * Render toggle.
	 */
	private function render_toggle( array $data, array &$attrs ): void {
		$this->set_text_attrs( $data, $attrs, [ 'title', 'content' ] );

		// Copy title.decoration from raw data if present (native block format)
		if ( isset( $data['title']['decoration'] ) ) {
			$attrs['title']['decoration'] = $data['title']['decoration'];
		}

		// headingFont → title.decoration.font.font (native Divi 5 path).
		// Normalize: unwrap a `{h5:{font:{desktop:{value:{...}}}}}` wrapper into the
		// flat `{desktop:{value:{..., headingLevel}}}` shape the toggle schema expects.
		if ( isset( $data['headingFont'] ) && is_array( $data['headingFont'] ) ) {
			$hf = $data['headingFont'];
			$flat = $this->normalize_font_group( $hf, 'h5' );
			$attrs['title']['decoration']['font']['font'] = $flat;
			unset( $attrs['module']['headingFont'] );
		}

		// Copy content.decoration from raw data if present (native block format)
		if ( isset( $data['content']['decoration'] ) ) {
			$attrs['content']['decoration'] = $data['content']['decoration'];
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

		// Allow disabling the Divi module preset (e.g. '__ET_DISABLED_PRESET__')
		// so module-specific icon/color overrides aren't beaten by the default preset.
		if ( isset( $data['_module_preset'] ) ) {
			$attrs['_module_preset'] = $data['_module_preset'];
			unset( $data['_module_preset'] );
		}
	}

	/**
	 * Normalize a font-group input into the flat `{bp:{value:{...}}}` shape Divi expects.
	 *
	 * Accepts:
	 *   A) flat  { "desktop": { "value": {...} }, "phone": { "value": {...} } }
	 *   B) level { "h5": { "font": { "desktop": { "value": {...} } } } }
	 *   C) font  { "font": { "desktop": { "value": {...} } } }
	 *
	 * @param array  $font_group Input font group.
	 * @param string $default_level Fallback heading level (e.g. 'h5').
	 * @return array Flat breakpoint-keyed font object.
	 */
	private function normalize_font_group( array $font_group, string $default_level ): array {
		$level_font = $font_group[ $default_level ] ?? null;
		if ( is_array( $level_font ) && isset( $level_font['font'] ) ) {
			$font_src = $level_font['font'];
		} else {
			$font_src = $font_group['font'] ?? $font_group;
		}

		$font_src = $this->normalize_flat_font( $font_src );

		if ( ! isset( $font_src['desktop']['value']['headingLevel'] ) ) {
			if ( ! isset( $font_src['desktop'] ) ) {
				$font_src['desktop'] = [ 'value' => [] ];
			}
			if ( ! is_array( $font_src['desktop']['value'] ) ) {
				$font_src['desktop']['value'] = [];
			}
			$font_src['desktop']['value']['headingLevel'] = $default_level;
		}

		return $font_src;
	}

	/**
	 * Ensure a font source is breakpoint-keyed: {bp:{value:{...}}}.
	 *
	 * @param mixed $font Font source.
	 * @return array Flat breakpoint-keyed font object.
	 */
	private function normalize_flat_font( $font ): array {
		if ( ! is_array( $font ) ) {
			return [ 'desktop' => [ 'value' => [] ] ];
		}
		$modes = [ 'desktop', 'tablet', 'phone' ];
		$has_mode = ! empty( array_intersect( $modes, array_keys( $font ) ) );
		if ( ! $has_mode ) {
			$flat = [];
			foreach ( $modes as $bp ) {
				$flat[ $bp ] = [ 'value' => $font ];
			}
			return $flat;
		}
		$flat = $font;
		foreach ( $modes as $bp ) {
			if ( ! isset( $flat[ $bp ] ) ) {
				continue;
			}
			if ( ! is_array( $flat[ $bp ] ) ) {
				$flat[ $bp ] = [ 'value' => $flat[ $bp ] ];
			} elseif ( ! isset( $flat[ $bp ]['value'] ) || ! is_array( $flat[ $bp ]['value'] ) ) {
				$flat[ $bp ] = [ 'value' => $flat[ $bp ]['value'] ?? [] ];
			}
		}
		return $flat;
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

		// Pass through toggle/accordion icon overrides (native Divi 5 attrs).
		foreach ( [ 'openToggle', 'closedToggle', 'openToggleIcon', 'closedToggleIcon' ] as $tk ) {
			if ( isset( $data[ $tk ] ) ) {
				$attrs[ $tk ] = $data[ $tk ];
			}
		}

		// Allow disabling the Divi module preset so module icon/color overrides win.
		if ( isset( $data['_module_preset'] ) ) {
			$attrs['_module_preset'] = $data['_module_preset'];
			unset( $data['_module_preset'] );
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
