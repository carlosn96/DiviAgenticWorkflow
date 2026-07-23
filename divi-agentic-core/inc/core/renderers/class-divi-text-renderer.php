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

		// In Divi 5, text fonts belong to content.decoration, not module.
		if ( $slug === 'divi/text' || $slug === 'divi/heading' ) {
			$hf = $data['headingFont'] ?? $attrs['module']['headingFont'] ?? null;
			if ( $hf ) {
				$attrs['content']['decoration']['headingFont'] = $hf;
				unset( $attrs['module']['headingFont'] );
				if ( isset( $data['content'] ) && is_string( $data['content'] ) ) {
					$html = $data['content'];
					foreach ( $hf as $tag => $font_data ) {
						if ( isset( $font_data['font']['desktop']['value']['color'] ) ) {
							$color  = $font_data['font']['desktop']['value']['color'];
							$tag_re = '/<' . $tag . '([^>]*)>/i';
							$html   = preg_replace_callback( $tag_re, function ( $m ) use ( $color ) {
								if ( strpos( $m[1], 'style=' ) !== false ) {
									return preg_replace( '/style="([^"]*)"/', 'style="color:' . $color . ';$1"', $m[0] );
								} else {
									return '<' . $tag . $m[1] . ' style="color:' . $color . ';">';
								}
							}, $html );
						}
					}
					$attrs['content']['innerContent'] = [ 'desktop' => [ 'value' => $html ] ];
				}
			}
			$bf = $data['bodyFont'] ?? $attrs['module']['bodyFont'] ?? null;
			if ( $bf ) {
				$attrs['content']['decoration']['bodyFont'] = $bf;
				unset( $attrs['module']['bodyFont'] );
				if ( isset( $data['content'] ) && is_string( $data['content'] ) ) {
					if ( isset( $bf['body']['font']['desktop']['value']['color'] ) ) {
						$color = $bf['body']['font']['desktop']['value']['color'];
						$html  = $attrs['content']['innerContent']['desktop']['value'] ?? $data['content'];
						$tags  = [ 'p', 'span', 'div', 'li' ];
						foreach ( $tags as $tag ) {
							$tag_re = '/<' . $tag . '([^>]*)>/i';
							$html   = preg_replace_callback( $tag_re, function ( $m ) use ( $color ) {
								if ( strpos( $m[1], 'style=' ) !== false ) {
									return preg_replace( '/style="([^"]*)"/', 'style="color:' . $color . ';$1"', $m[0] );
								} else {
									return '<' . $tag . $m[1] . ' style="color:' . $color . ';">';
								}
							}, $html );
						}
						$attrs['content']['innerContent'] = [ 'desktop' => [ 'value' => $html ] ];
					}
				}
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

		// VIE puts font in module.decoration.font, but Divi 5 expects:
		//   divi/text    → content.decoration.bodyFont
		//   divi/heading → title.decoration.font.font
		$font_src = $attrs['module']['decoration']['font'] ?? null;
		if ( $font_src ) {
			if ( $slug === 'divi/text' ) {
				$attrs['content']['decoration']['bodyFont'] = $font_src;
			} elseif ( $slug === 'divi/heading' ) {
				$attrs['title']['decoration']['font']['font'] = $font_src;
			}
			unset( $attrs['module']['decoration']['font'] );
		}

		// Override native module text color from headingFont to prevent "light" default (white).
		if ( $slug === 'divi/text' || $slug === 'divi/heading' ) {
			$hf = $data['headingFont'] ?? $attrs['module']['headingFont'] ?? null;
			if ( $hf ) {
				foreach ( $hf as $tag => $font_data ) {
					if ( isset( $font_data['font']['desktop']['value']['color'] ) ) {
						$color = $font_data['font']['desktop']['value']['color'];
						$attrs['module']['advanced']['text']['text']['desktop']['value']['color'] = $color;
						break;
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
