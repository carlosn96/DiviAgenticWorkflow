<?php

namespace Divi_Agentic_Core\Core\Renderers;

require_once __DIR__ . '/interface-block-renderer.php';
require_once __DIR__ . '/trait-block-helpers.php';

class Dgbm_Renderer implements Block_Renderer_Interface {
	use Block_Helpers;

	public function render( string $slug, array $data, string $content_key, string $children_html ): array {
		$shortcode = $this->build_shortcode( $data );

		return [
			'attrs'      => [],
			'inner'      => '',
			'inner_html' => $shortcode,
		];
	}

	private function build_shortcode( array $data ): string {
		$keys = [
			'use_current_loop', 'post_type', 'posts_number',
			'include_categories', 'orderby', 'offset_number',
			'related_posts', 'title_tag',
			'show_thumbnail', 'show_excerpt', 'use_post_excerpt',
			'show_excerpt_length', 'show_categories', 'show_author',
			'show_date', 'meta_date', 'show_comments',
			'show_pagination', 'show_more', 'read_more_text',
			'layout', 'item_in_desktop', 'item_in_tablet', 'item_in_mobile',
			'space_between', 'space_between_tablet', 'space_between_phone',
			'space_between_last_edited',
			'layout_styles', 'equal_height',
			'equal_height_column', 'vertical_align',
			'image_as_background', 'image_width', 'image_size',
			'side_overlap_setting', 'side_overlap',
			'side_overlap_phone', 'side_overlap_last_edited',
			'image_overlay', 'overlay_color',
			'use_overlay_icon', 'select_overlay_icon', 'overlay_icon_color',
			'image_scale_on_hover',
			'use_meta_icon',
			'default_position_alignment', 'top_position_alignment',
			'bottom_position_alignment',
			'default_position_bg', 'top_position_bg', 'bottom_position_bg',
			'button_alignment', 'button_bg_color', 'button_fullwidth',
			'button_at_bottom', 'use_button_icon', 'button_icon',
			'pagination_background',
			'author_location', 'author_background_color',
			'date_location', 'date_background_color',
			'category_location', 'category_background_color',
			'comment_location', 'comment_background_color',
			'background_color',
			'use_background_color_gradient',
			'background_color_gradient_start', 'background_color_gradient_end',
			'background_color_gradient_direction',
			'box_shadow_style', 'box_shadow_horizontal', 'box_shadow_vertical',
			'box_shadow_blur', 'box_shadow_spread', 'box_shadow_color',
			'box_shadow_style_container', 'box_shadow_style_content',
			'box_shadow_color_content',
			'border_radii',
			'post_item_border_radii',
			'border_radii_category',
			'border_width_all_read_more', 'border_color_all_read_more',
			'border_width_all_category', 'border_color_all_category',
			'border_color_all_post_item', 'border_color_bottom_post_item',
			'border_width_left_post_item', 'border_color_left_post_item',
			'border_color_left_post_item__hover_enabled', 'border_color_left_post_item__hover',
			'container_margin', 'container_padding',
			'article_margin', 'article_padding',
			'image_margin', 'content_margin', 'content_padding',
			'content_padding_tablet', 'content_padding_phone', 'content_padding_last_edited',
			'title_margin', 'title_margin_tablet', 'title_margin_last_edited',
			'meta_default_margin', 'meta_default_padding',
			'meta_top_margin', 'meta_top_padding',
			'meta_bottom_margin', 'meta_bottom_padding',
			'text_margin',
			'button_wrapper_margin', 'button_margin', 'button_padding',
			'pagination_margin', 'pagination_padding',
			'author_margin', 'author_padding',
			'date_margin', 'date_padding',
			'category_margin', 'category_padding',
			'comment_margin', 'comment_padding',
			'title_font', 'title_text_align', 'title_text_color', 'title_font_size',
			'title_font_size_tablet', 'title_font_size_phone', 'title_font_size_last_edited',
			'title_line_height', 'title_line_height_tablet', 'title_line_height_last_edited',
			'title_text_color__hover_enabled', 'title_text_color__hover',
			'meta_font', 'meta_text_color',
			'content_font', 'content_text_align', 'content_text_color', 'content_line_height',
			'read_more_font', 'read_more_text_color',
			'pagination_font', 'pagination_text_color',
			'author_font', 'author_text_color', 'author_letter_spacing',
			'date_font', 'date_text_color', 'date_font_size',
			'category_font', 'category_text_color', 'category_font_size',
			'comment_font',
			'author_background_color__hover', 'author_background_color__hover_enabled',
			'date_background_color__hover', 'date_background_color__hover_enabled',
			'date_text_color__hover', 'date_text_color__hover_enabled',
			'content_margin__hover', 'content_margin__hover_enabled',
			'content_padding__hover_enabled',
			'button_bg_color__hover',
		];

		$atts = [];
		foreach ( $keys as $key ) {
			if ( ! isset( $data[ $key ] ) ) {
				continue;
			}
			$val = $this->extract_flat_value( $data[ $key ] );
			if ( $val !== null && $val !== '' ) {
				$atts[] = $key . '="' . esc_attr( $val ) . '"';
			}
		}

		foreach ( [ 'blog_type', 'type_attr' ] as $alias ) {
			if ( isset( $data[ $alias ] ) ) {
				$val = $this->extract_flat_value( $data[ $alias ] );
				if ( $val !== null ) {
					$atts[] = 'type="' . esc_attr( $val ) . '"';
				}
				break;
			}
		}

		return '[dgbm_blog_module ' . implode( ' ', $atts ) . '][/dgbm_blog_module]';
	}

	private function extract_flat_value( $val ): ?string {
		if ( is_string( $val ) ) {
			return $val;
		}
		if ( is_numeric( $val ) ) {
			return (string) $val;
		}
		if ( is_bool( $val ) ) {
			return $val ? 'on' : 'off';
		}
		if ( is_array( $val ) ) {
			if ( isset( $val['innerContent']['desktop']['value'] ) ) {
				$inner = $val['innerContent']['desktop']['value'];
				if ( is_array( $inner ) ) {
					return implode( ',', $inner );
				}
				return (string) $inner;
			}
		}
		return null;
	}
}
