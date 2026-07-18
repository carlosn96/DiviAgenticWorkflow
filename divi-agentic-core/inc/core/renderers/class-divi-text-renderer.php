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
			if ( isset( $data['headingFont'] ) ) {
				$attrs['content']['decoration']['headingFont'] = $data['headingFont'];
				unset( $attrs['module']['headingFont'] );
			}
			if ( isset( $data['bodyFont'] ) ) {
				$attrs['content']['decoration']['bodyFont'] = $data['bodyFont'];
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

		return [
			'attrs'      => $attrs,
			'inner'      => '',
			'inner_html' => '',
		];
	}
}
