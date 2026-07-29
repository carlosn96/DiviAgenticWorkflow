<?php
/**
 * Renderer: Divi Text
 *
 * Handles text-like blocks: text, heading, code, fullwidth-code, shortcode-module.
 *
 * @package Divi_Agentic_Core
 */

namespace Divi_Agentic_Core\Core\Renderers;

require_once __DIR__ . '/class-divi-base-renderer.php';

/**
 * Class Divi_Text_Renderer
 */
class Divi_Text_Renderer extends Divi_Base_Renderer {

	/**
	 * @inheritDoc
	 */
	public function render( string $slug, array $data, string $content_key, string $children_html ): array {
		$attrs = $this->prepare_base_attrs( $data, $data['builderVersion'] ?? DIVI_BUILDER_VERSION );

		if ( isset( $data['content'] ) ) {
			if ( is_string( $data['content'] ) ) {
				// Raw string: wrap in standard structure.
				$attrs['content']['innerContent'] = [
					'desktop' => [ 'value' => $data['content'] ],
				];
			} elseif ( isset( $data['content']['innerContent'] ) ) {
				// Already structured (from build_page.php deep_merge): use as-is.
				$attrs['content'] = $data['content'];
			} else {
				// Fallback: assume array with keys to merge.
				$attrs['content']['innerContent'] = [
					'desktop' => [ 'value' => $data['content'] ],
				];
			}
		}

		// Font data → content.decoration (Divi 5 stores fonts here).
		// Inline style injection via regex is REMOVED because it corrupts HTML tags.
		// Font rendering is handled by generate_font_css() → freeForm CSS below.
		if ( $slug === 'divi/text' || $slug === 'divi/heading' ) {
			$hf = $data['headingFont'] ?? $attrs['module']['headingFont'] ?? null;
			if ( $hf ) {
				$attrs['content']['decoration']['headingFont'] = $hf;
				unset( $attrs['module']['headingFont'] );
			}
			$bf = $data['bodyFont'] ?? $attrs['module']['bodyFont'] ?? null;
			if ( $bf ) {
				$attrs['content']['decoration']['bodyFont'] = $bf;
				unset( $attrs['module']['bodyFont'] );
			}
		}

		// divi/heading needs title.innerContent + headingLevel for Divi 5.
		if ( $slug === 'divi/heading' && isset( $data['content'] ) ) {
			$heading_text  = $data['content'];
			$heading_level = $data['level'] ?? 'h2';
			if ( preg_match( '/<h([1-6])>/', $heading_text, $m ) ) {
				$heading_level = 'h' . $m[1];
				$heading_text  = strip_tags( $heading_text );
			} elseif ( isset( $data['title']['level'] ) ) {
				$heading_level = $data['title']['level'];
			}
			$attrs['title']['innerContent']                                = [ 'desktop' => [ 'value' => $heading_text ] ];
			$attrs['title']['decoration']['font']['font']['desktop']['value']['headingLevel'] = $heading_level;
		}

		// VIE puts font in module.decoration.font → Divi 5 paths:
		//   divi/text    → content.decoration.bodyFont
		//   divi/heading → title.decoration.font.font
		$font_src = $attrs['module']['decoration']['font'] ?? null;
		if ( $font_src ) {
			if ( $slug === 'divi/text' ) {
				$attrs['content']['decoration']['bodyFont'] = $font_src;
			} elseif ( $slug === 'divi/heading' ) {
				// Unwrap extra nesting: schema has decoration.font.font,
				// but title.decoration.font.font expects {desktop:{value:{...}}}
				$attrs['title']['decoration']['font']['font'] = $font_src['font'] ?? $font_src;
			}
			unset( $attrs['module']['decoration']['font'] );
			// Remove empty decoration so Divi doesn't skip style processing
			if ( empty( $attrs['module']['decoration'] ) ) {
				unset( $attrs['module']['decoration'] );
			}
		}

		return [
			'attrs'      => $attrs,
			'inner'      => '',
			'inner_html' => '',
		];
	}

	/**
	 * Generate CSS from bodyFont/headingFont attributes.
	 *
	 * @param string $slug  Module slug.
	 * @param array  $attrs Current block attributes.
	 * @return string Generated CSS or empty string.
	 */
	private function generate_font_css( string $slug, array $attrs ): string {
		$css      = '';
		$order_class = '%%order_class%%';

		if ( $slug === 'divi/text' || $slug === 'divi/heading' ) {
			$module_class = $attrs['module']['advanced']['htmlAttributes']['desktop']['value']['class'] ?? '';

			// Heading font (h1-h6 inside .et_pb_text_inner)
			$hf = $attrs['content']['decoration']['headingFont'] ?? null;
			if ( $hf ) {
				foreach ( $hf as $tag => $font_data ) {
					if ( ! isset( $font_data['font'] ) ) continue;
					$sel = $module_class ? ".{$module_class} .et_pb_text_inner {$tag}" : "{$order_class} .et_pb_text_inner {$tag}";
					foreach ( $this->build_font_css_rules( $font_data['font'] ) as $rule ) {
						$css .= $rule['media'] ? "{$rule['media']}{{$sel} {{$rule['declarations']}}}" : "{$sel} {{$rule['declarations']}}";
					}
				}
			}

			// Body font (p, li, etc. inside .et_pb_text_inner)
			$bf = $attrs['content']['decoration']['bodyFont'] ?? null;
			if ( $bf && isset( $bf['body']['font'] ) ) {
				$sel = $module_class ? ".{$module_class} .et_pb_text_inner" : "{$order_class} .et_pb_text_inner";
				foreach ( $this->build_font_css_rules( $bf['body']['font'] ) as $rule ) {
					$css .= $rule['media'] ? "{$rule['media']}{{$sel} {{$rule['declarations']}}}" : "{$sel} {{$rule['declarations']}}";
				}
			}

			// divi/heading title font (from decoration.font → title.decoration.font.font)
			if ( $slug === 'divi/heading' ) {
				$tf = $attrs['title']['decoration']['font']['font']['font'] ?? $attrs['title']['decoration']['font']['font'] ?? null;
				if ( $tf ) {
					// Unwrap extra font nesting if present
					$font_obj = isset( $tf['font'] ) ? $tf['font'] : $tf;
					$sel = $module_class ? ".{$module_class} .et_pb_heading_container h1, .{$module_class} .et_pb_heading_container h2, .{$module_class} .et_pb_heading_container h3, .{$module_class} .et_pb_heading_container h4, .{$module_class} .et_pb_heading_container h5, .{$module_class} .et_pb_heading_container h6" : "{$order_class} .et_pb_heading_container h1, {$order_class} .et_pb_heading_container h2, {$order_class} .et_pb_heading_container h3, {$order_class} .et_pb_heading_container h4, {$order_class} .et_pb_heading_container h5, {$order_class} .et_pb_heading_container h6";
					foreach ( $this->build_font_css_rules( $font_obj ) as $rule ) {
						$css .= $rule['media'] ? "{$rule['media']}{{$sel} {{$rule['declarations']}}}" : "{$sel} {{$rule['declarations']}}";
					}
				}
			}
		}

		return $css;
	}

	/**
	 * Build CSS declarations array from a font object across breakpoints.
	 *
	 * @param array $font Font object with {desktop/tablet/phone: {value: {fontFamily, size, weight, color, lineHeight, ...}}}.
	 * @return array{declarations: string, media: string}[] Array of [declarations, media].
	 */
	private function build_font_css_rules( array $font ): array {
		$breakpoints = [
			'desktop' => '',
			'tablet'  => '@media (max-width:980px)',
			'phone'   => '@media (max-width:767px)',
		];
		$rules = [];
		foreach ( $breakpoints as $bp => $media ) {
			$value = $font[ $bp ]['value'] ?? null;
			if ( ! $value ) continue;

			$declarations = '';
			if ( isset( $value['fontFamily'] ) ) {
				$ff = $value['fontFamily'];
				if ( strpos( $ff, ' ' ) !== false && strpos( $ff, '"' ) === false && strpos( $ff, "'" ) === false ) {
					$ff = '"' . $ff . '"';
				}
				$declarations .= 'font-family:' . $ff . ' !important;';
			}
			if ( isset( $value['size'] ) ) {
				$declarations .= 'font-size:' . $value['size'] . ' !important;';
			}
			if ( isset( $value['weight'] ) ) {
				$declarations .= 'font-weight:' . $value['weight'] . ' !important;';
			}
			if ( isset( $value['color'] ) ) {
				$declarations .= 'color:' . $value['color'] . ' !important;';
			}
			if ( isset( $value['lineHeight'] ) ) {
				$declarations .= 'line-height:' . $value['lineHeight'] . ' !important;';
			}
			if ( isset( $value['letterSpacing'] ) ) {
				$declarations .= 'letter-spacing:' . $value['letterSpacing'] . ' !important;';
			}
			if ( isset( $value['textAlign'] ) ) {
				$declarations .= 'text-align:' . $value['textAlign'] . ' !important;';
			}
			if ( isset( $value['textTransform'] ) ) {
				$declarations .= 'text-transform:' . $value['textTransform'] . ' !important;';
			}
			if ( isset( $value['fontStyle'] ) ) {
				$declarations .= 'font-style:' . $value['fontStyle'] . ' !important;';
			}

			if ( ! $declarations ) continue;
			$rules[] = [ 'declarations' => $declarations, 'media' => $media ];
		}
		return $rules;
	}
}
