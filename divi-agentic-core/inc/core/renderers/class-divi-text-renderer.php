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
		if ( $slug === 'divi/text' ) {
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
			$heading_level = $data['level'] ?? 'h2';
			if ( is_array( $data['content'] ) && isset( $data['content']['innerContent'] ) ) {
				// Dynamic / structured content: pass through untouched, keep level from attr.
				$attrs['title']['innerContent'] = $data['content']['innerContent'];
				if ( isset( $data['title']['level'] ) ) {
					$heading_level = $data['title']['level'];
				}
			} else {
				$heading_text = is_string( $data['content'] ) ? $data['content'] : '';
				if ( preg_match( '/<h([1-6])>/', $heading_text, $m ) ) {
					$heading_level = 'h' . $m[1];
					$heading_text  = strip_tags( $heading_text );
				} elseif ( isset( $data['title']['level'] ) ) {
					$heading_level = $data['title']['level'];
				}
				$attrs['title']['innerContent'] = [ 'desktop' => [ 'value' => $heading_text ] ];
			}

			// Merge headingFont into the native title.decoration.font.font path
			// so Divi generates CSS for size/weight/color/fontFamily per breakpoint
			// instead of only headingLevel.
			$hf = $data['headingFont'] ?? null;
			if ( is_array( $hf ) ) {
				$level_font = $hf[ $heading_level ] ?? ( $hf['h1'] ?? $hf );
				if ( is_array( $level_font ) ) {
					$font_src = $level_font['font'] ?? $level_font;
					foreach ( [ 'desktop', 'tablet', 'phone' ] as $bp ) {
						if ( isset( $font_src[ $bp ]['value'] ) && is_array( $font_src[ $bp ]['value'] ) ) {
							foreach ( $font_src[ $bp ]['value'] as $k => $v ) {
								$attrs['title']['decoration']['font']['font'][ $bp ]['value'][ $k ] = $v;
							}
						}
					}
				}
				unset( $attrs['module']['headingFont'] );
			}

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

		// Generate CSS from fonts, sub-fonts (link, strong, ul, ol), and spacing extensions (scrollMarginTop).
		$generated_css = $this->generate_font_css( $slug, $attrs );
		if ( ! empty( $generated_css ) ) {
			$existing_css = $attrs['css']['desktop']['value']['freeForm'] ?? '';
			$attrs['css']['desktop']['value']['freeForm'] = $existing_css ? $existing_css . "\n" . $generated_css : $generated_css;
		}

		return [
			'attrs'      => $attrs,
			'inner'      => '',
			'inner_html' => '',
		];
	}

	/**
	 * Generate CSS from bodyFont/headingFont attributes and spacing extensions.
	 *
	 * @param string $slug  Module slug.
	 * @param array  $attrs Current block attributes.
	 * @return string Generated CSS or empty string.
	 */
	private function generate_font_css( string $slug, array $attrs ): string {
		$css         = '';
		$order_class = '%%order_class%%';

		if ( $slug === 'divi/text' || $slug === 'divi/heading' ) {
			$module_class = $attrs['module']['advanced']['htmlAttributes']['desktop']['value']['class'] ?? '';
			$base_sel     = $module_class ? ".{$module_class}" : $order_class;

			// Link hover pseudo-class (only if explicitly set, since Divi 5 does not provide a dedicated hover field for link in bodyFont)
			$bf = $attrs['content']['decoration']['bodyFont'] ?? null;
			if ( $bf ) {
				$link_font = $bf['body']['link'] ?? $bf['link']['font'] ?? $bf['link'] ?? null;
				if ( $link_font ) {
					$link_font_data = isset( $link_font['font'] ) ? $link_font['font'] : $link_font;
					$hover_data     = $link_font['hover']['value'] ?? $link_font_data['hover']['value'] ?? null;
					if ( $hover_data ) {
						$hover_rules = $this->build_font_css_rules( [ 'desktop' => [ 'value' => $hover_data ] ] );
						foreach ( $hover_rules as $rule ) {
							$sel_h = "{$base_sel} .et_pb_text_inner a:hover";
							$css  .= $rule['media'] ? "{$rule['media']}{{$sel_h} {{$rule['declarations']}}}" : "{$sel_h} {{$rule['declarations']}}";
						}
					}
				}
			}


			// 4. Scroll margin top (sticky header offset)
			$smt = $attrs['module']['decoration']['spacing']['desktop']['value']['scrollMarginTop']
				?? $attrs['decoration']['spacing']['desktop']['value']['scrollMarginTop']
				?? $attrs['module']['decoration']['spacing']['desktop']['value']['scroll_margin_top']
				?? $attrs['decoration']['spacing']['desktop']['value']['scroll_margin_top']
				?? null;
			if ( $smt ) {
				$css .= "{$base_sel} { scroll-margin-top: {$smt} !important; }";
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
			// Style alias (italic, normal, oblique)
			if ( isset( $value['style'] ) && in_array( $value['style'], [ 'italic', 'normal', 'oblique' ], true ) ) {
				$declarations .= 'font-style:' . $value['style'] . ' !important;';
			}
			// Text decoration
			$td = $value['textDecoration'] ?? ( ( isset( $value['style'] ) && in_array( $value['style'], [ 'underline', 'line-through', 'none', 'overline' ], true ) ) ? $value['style'] : null );
			if ( $td !== null ) {
				$declarations .= 'text-decoration:' . $td . ' !important;';
			}
			// Text decoration color / line color
			$tdc = $value['textDecorationColor'] ?? $value['lineColor'] ?? null;
			if ( $tdc !== null ) {
				$declarations .= 'text-decoration-color:' . $tdc . ' !important;';
			}
			// Underline offset
			$tuo = $value['textUnderlineOffset'] ?? $value['underlineOffset'] ?? null;
			if ( $tuo !== null ) {
				$declarations .= 'text-underline-offset:' . $tuo . ' !important;';
			}
			// Decoration thickness / line thickness
			$tdt = $value['textDecorationThickness'] ?? $value['lineThickness'] ?? null;
			if ( $tdt !== null ) {
				$declarations .= 'text-decoration-thickness:' . $tdt . ' !important;';
			}
			// List styling & list margins
			if ( isset( $value['listStyleType'] ) ) {
				$declarations .= 'list-style-type:' . $value['listStyleType'] . ' !important;';
			}
			if ( isset( $value['paddingLeft'] ) ) {
				$declarations .= 'padding-left:' . $value['paddingLeft'] . ' !important;';
			}
			if ( isset( $value['marginBottom'] ) ) {
				$declarations .= 'margin-bottom:' . $value['marginBottom'] . ' !important;';
			}
			if ( isset( $value['marginTop'] ) ) {
				$declarations .= 'margin-top:' . $value['marginTop'] . ' !important;';
			}

			if ( ! $declarations ) continue;
			$rules[] = [ 'declarations' => $declarations, 'media' => $media ];
		}
		return $rules;
	}
}
