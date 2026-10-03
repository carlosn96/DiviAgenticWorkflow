<?php
/**
 * Renderer: Divi Generic
 *
 * Handles divider, map/fullwidth-map, blog, sidebar, login,
 * contact-form-7, icon-list-item, lottie, svg, map-pin, dropdown,
 * portfolio/filterable-portfolio, breadcrumbs, link, signup,
 * and all fullwidth-* generic fallthroughs.
 *
 * @package Divi_Agentic_Core
 */

namespace Divi_Agentic_Core\Core\Renderers;

require_once __DIR__ . '/class-divi-base-renderer.php';

/**
 * Class Divi_Generic_Renderer
 */
class Divi_Generic_Renderer extends Divi_Base_Renderer {

	/**
	 * @inheritDoc
	 */
	public function render( string $slug, array $data, string $content_key, string $children_html ): array {
		$attrs = $this->prepare_base_attrs( $data, $data['builderVersion'] ?? DIVI_BUILDER_VERSION );

		switch ( true ) {
			case $slug === 'divi/divider':
				if ( isset( $data['divider'] ) ) {
					$attrs['divider'] = $data['divider'];
				}
				$line_props = [];
				foreach ( [ 'show', 'color', 'style', 'position', 'weight' ] as $prop ) {
					if ( isset( $data[ $prop ] ) ) {
						$line_props[ $prop ] = $data[ $prop ];
					}
				}
				if ( ! empty( $line_props ) ) {
					$attrs['divider']['advanced']['line'] = [ 'desktop' => [ 'value' => $line_props ] ];
				}
				break;

			case in_array( $slug, [ 'divi/map', 'divi/fullwidth-map' ], true ):
				// Divi 5 map.innerContent.desktop.value is an object
				// {address, zoom, lat, lng}, not a plain string.
				$map_val = $attrs['map']['innerContent']['desktop']['value'] ?? [];
				if ( ! is_array( $map_val ) ) {
					$map_val = [];
				}
				foreach ( [ 'address', 'zoom', 'lat', 'lng' ] as $map_key ) {
					if ( isset( $data[ $map_key ] ) ) {
						$map_val[ $map_key ] = $data[ $map_key ];
					}
				}
				if ( ! empty( $map_val ) ) {
					$attrs['map']['innerContent'] = [ 'desktop' => [ 'value' => $map_val ] ];
				}
				if ( isset( $data['mouse_wheel'] ) ) {
					$attrs['map']['advanced']['mouseWheel'] = [ 'desktop' => [ 'value' => $data['mouse_wheel'] ] ];
				}
				if ( isset( $data['mobile_dragging'] ) ) {
					$attrs['map']['advanced']['mobileDragging'] = [ 'desktop' => [ 'value' => $data['mobile_dragging'] ] ];
				}
				break;

			case $slug === 'divi/blog':
				// NOTE: 'type' es la key de dispatch del Layout Engine (divi/blog),
				// NO el post type. El post type nativo por defecto es 'post'.
				// Para grids de CPTs usar la key 'post_type' en el schema.
				if ( isset( $data['post_type'] ) ) {
					$attrs['post']['advanced']['type'] = [ 'desktop' => [ 'value' => $data['post_type'] ] ];
				}
				foreach ( [
					'number', 'categories', 'dateFormat', 'excerptLength', 'offset',
					'showExcerpt', 'useCurrentLoop', 'excerptContent', 'excerptManual',
				] as $key ) {
					if ( isset( $data[ $key ] ) ) {
						$attrs['post']['advanced'][ $key ] = [ 'desktop' => [ 'value' => $data[ $key ] ] ];
					}
				}
				foreach ( [
					'showAuthor', 'showDate', 'showCategories', 'showComments',
				] as $key ) {
					if ( isset( $data[ $key ] ) ) {
						$attrs['meta']['advanced'][ $key ] = [ 'desktop' => [ 'value' => $data[ $key ] ] ];
					}
				}
				if ( isset( $data['show_featured_image'] ) ) {
					$attrs['image']['advanced']['enable'] = [ 'desktop' => [ 'value' => $data['show_featured_image'] ] ];
				}
				foreach ( [
					'readMore' => 'readMore.advanced.enable',
					'pagination' => 'pagination.advanced.enable',
					'overlay' => 'overlay.advanced.enable',
					'fullwidth' => 'fullwidth.advanced.enable',
				] as $input_key => $attr_path ) {
					if ( isset( $data[ $input_key ] ) ) {
						$parts = explode( '.', $attr_path );
						$ref = &$attrs;
						foreach ( $parts as $p ) {
							if ( ! isset( $ref[ $p ] ) ) {
								$ref[ $p ] = [];
							}
							$ref = &$ref[ $p ];
						}
						$ref = [ 'desktop' => [ 'value' => $data[ $input_key ] ] ];
					}
				}
				if ( isset( $data['blogGrid_columns'] ) ) {
					$attrs['blogGrid']['decoration']['layout']['desktop']['value']['display'] = 'grid';
					$attrs['blogGrid']['decoration']['layout']['desktop']['value']['gridColumnCount'] = $data['blogGrid_columns'];
				}

				// Responsive grid columns (native, per breakpoint).
				foreach ( [ 'tablet' => 'blogGrid_columns_tablet', 'phone' => 'blogGrid_columns_phone' ] as $bp => $flat ) {
					if ( isset( $data[ $flat ] ) ) {
						$attrs['blogGrid']['decoration']['layout'][ $bp ]['value']['display']         = 'grid';
						$attrs['blogGrid']['decoration']['layout'][ $bp ]['value']['gridColumnCount'] = $data[ $flat ];
					}
				}
				// Grid gap (native).
				foreach ( [ 'blogGrid_gap' => 'gap', 'blogGrid_columnGap' => 'columnGap', 'blogGrid_rowGap' => 'rowGap' ] as $flat => $key ) {
					if ( isset( $data[ $flat ] ) ) {
						$attrs['blogGrid']['decoration']['layout']['desktop']['value'][ $key ] = $data[ $flat ];
					}
				}
				// Full blogGrid passthrough (gap/columns at any breakpoint via nested structure).
				if ( isset( $data['blogGrid'] ) && is_array( $data['blogGrid'] ) ) {
					$attrs['blogGrid'] = array_replace_recursive( $attrs['blogGrid'] ?? [], $data['blogGrid'] );
				}
				// Post item (card) decoration passthrough — border is the native decoration of blog post items.
				if ( isset( $data['post'] ) && is_array( $data['post'] ) && isset( $data['post']['decoration'] ) ) {
					$attrs['post']['decoration'] = array_replace_recursive( $attrs['post']['decoration'] ?? [], $data['post']['decoration'] );
				}
				// Featured image decoration passthrough (fit/object-fit, sizing/aspect).
				if ( isset( $data['image'] ) && is_array( $data['image'] ) ) {
					$attrs['image'] = array_replace_recursive( $attrs['image'] ?? [], $data['image'] );
				}
				if ( isset( $data['overlayColor'] ) ) {
					$attrs['overlay']['decoration']['background']['desktop']['value']['color'] = $data['overlayColor'];
				}
				if ( isset( $data['masonryBg'] ) ) {
					$attrs['masonry']['decoration']['background']['desktop']['value']['color'] = $data['masonryBg'];
				}
				foreach ( [
					'titleFont' => 'title.decoration.font.font.desktop.value',
					'metaFont' => 'meta.decoration.font.font.desktop.value',
					'readMoreFont' => 'readMore.decoration.font.font.desktop.value',
					'paginationFont' => 'pagination.decoration.font.font.desktop.value',
				] as $input_key => $attr_path ) {
					if ( isset( $data[ $input_key ] ) && is_array( $data[ $input_key ] ) ) {
						$parts = explode( '.', $attr_path );
						$ref = &$attrs;
						foreach ( $parts as $p ) {
							if ( ! isset( $ref[ $p ] ) ) {
								$ref[ $p ] = [];
							}
							$ref = &$ref[ $p ];
						}
						$ref = array_merge( $ref, $data[ $input_key ] );
					}
				}
				if ( isset( $data['contentFont'] ) && is_array( $data['contentFont'] ) ) {
					$attrs['content']['decoration']['bodyFont']['body']['font']['desktop']['value'] = array_merge(
						$attrs['content']['decoration']['bodyFont']['body']['font']['desktop']['value'] ?? [],
						$data['contentFont']
					);
				}
				if ( isset( $data['overlayIcon'] ) || isset( $data['overlayIconColor'] ) ) {
					$icon = $attrs['overlayIcon']['decoration']['icon']['desktop']['value'] ?? [];
					if ( isset( $data['overlayIcon'] ) ) {
						$icon['unicode'] = $data['overlayIcon'];
						$icon['type'] = $icon['type'] ?? 'divi';
						$icon['weight'] = $icon['weight'] ?? '400';
					}
					if ( isset( $data['overlayIconColor'] ) ) {
						$icon['color'] = $data['overlayIconColor'];
					}
					$attrs['overlayIcon']['decoration']['icon']['desktop']['value'] = $icon;
				}
				break;

			case $slug === 'divi/sidebar':
				if ( isset( $data['area'] ) ) {
					$attrs['sidebar']['innerContent'] = [ 'desktop' => [ 'value' => [ 'area' => $data['area'] ] ] ];
				}
				if ( isset( $data['show_border'] ) ) {
					$attrs['sidebar']['advanced']['layout'] = [ 'desktop' => [ 'value' => [ 'showBorder' => $data['show_border'] ] ] ];
				}
				break;

			case $slug === 'divi/login':
				if ( isset( $data['content'] ) ) {
					$attrs['content']['innerContent'] = [ 'desktop' => [ 'value' => $data['content'] ] ];
				}
				if ( isset( $data['button_text'] ) ) {
					$attrs['button']['innerContent'] = [ 'desktop' => [ 'value' => [ 'text' => $data['button_text'] ] ] ];
				}
				break;

			case $slug === 'divi/contact-form-7':
				if ( isset( $data['form_id'] ) ) {
					$attrs['content']['innerContent'] = [ 'desktop' => [ 'value' => "[contact-form-7 id=\"{$data['form_id']}\"]" ] ];
				}
				break;

			case $slug === 'divi/icon-list-item':
				// Divi 5 stores the item label in content.innerContent (renders into
				// .et_pb_icon_list_text), and the item icon in icon.innerContent.
				$label = $data['content'] ?? $data['title'] ?? null;
				if ( is_array( $label ) && isset( $label['innerContent'] ) ) {
					$attrs['content'] = $label;
				} elseif ( $label !== null ) {
					$attrs['content']['innerContent'] = [ 'desktop' => [ 'value' => $label ] ];
				}

				$icon = $data['icon'] ?? null;
				if ( is_array( $icon ) && isset( $icon['innerContent'] ) ) {
					$val = $icon['innerContent']['desktop']['value'] ?? null;
					if ( is_array( $val ) && isset( $val['icon'] ) ) {
						$val = $val['icon'];
					}
					$icon['innerContent']['desktop']['value'] = $val;
					$attrs['icon'] = $icon;
				} elseif ( is_array( $icon ) && isset( $icon['unicode'] ) ) {
					$attrs['icon'] = [ 'innerContent' => [ 'desktop' => [ 'value' => $icon ] ] ];
				}
				break;

			case in_array( $slug, [ 'divi/lottie', 'divi/svg' ], true ):
				if ( isset( $data['src'] ) ) {
					$attrs['lottie'] = [ 'innerContent' => [ 'desktop' => [ 'value' => $data['src'] ] ] ];
				}
				if ( isset( $data['content'] ) ) {
					$attrs['content']['innerContent'] = [ 'desktop' => [ 'value' => $data['content'] ] ];
				}
				break;

			case $slug === 'divi/map-pin':
				// Divi 5 pin.innerContent.desktop.value is an object
				// {address, zoom, lat, lng}, not a plain string.
				$pin_val = $attrs['pin']['innerContent']['desktop']['value'] ?? [];
				if ( ! is_array( $pin_val ) ) {
					$pin_val = [];
				}
				foreach ( [ 'address', 'zoom', 'lat', 'lng' ] as $pin_key ) {
					if ( isset( $data[ $pin_key ] ) ) {
						$pin_val[ $pin_key ] = $data[ $pin_key ];
					}
				}
				if ( ! empty( $pin_val ) ) {
					$attrs['pin']['innerContent'] = [ 'desktop' => [ 'value' => $pin_val ] ];
				}
				if ( isset( $data['title'] ) ) {
					$attrs['title']['innerContent'] = [ 'desktop' => [ 'value' => $data['title'] ] ];
				}
				if ( isset( $data['content'] ) ) {
					$attrs['content']['innerContent'] = [ 'desktop' => [ 'value' => $data['content'] ] ];
				}
				break;

			case $slug === 'divi/dropdown':
				if ( isset( $data['title'] ) ) {
					$attrs['title']['innerContent'] = [ 'desktop' => [ 'value' => $data['title'] ] ];
				}
				if ( isset( $data['content'] ) ) {
					$attrs['content']['innerContent'] = [ 'desktop' => [ 'value' => $data['content'] ] ];
				}
				break;

			case in_array( $slug, [ 'divi/portfolio', 'divi/filterable-portfolio' ], true ):
				if ( isset( $data['number'] ) ) {
					$attrs['module']['advanced']['postsNumber'] = [ 'desktop' => [ 'value' => $data['number'] ] ];
				}
				break;

			case $slug === 'divi/signup':
				foreach ( [ 'title', 'content', 'button', 'field', 'success', 'formField' ] as $key ) {
					if ( isset( $data[ $key ] ) ) {
						$attrs[ $key ] = $data[ $key ];
					}
				}
				break;

			case $slug === 'divi/social-media-follow-network':
				if ( isset( $data['social_network'] ) || isset( $data['link'] ) ) {
					$attrs['socialNetwork']['innerContent'] = [
						'desktop' => [ 'value' => [
							'socialNetworkTitle'       => $data['social_network'] ?? '',
							'socialNetworkLink'        => $data['link'] ?? '',
							'socialNetworkSkypeUrl'    => $data['skype_url'] ?? '',
							'socialNetworkSkypeAction' => $data['skype_action'] ?? 'call',
						] ],
					];
				} elseif ( isset( $data['socialNetwork'] ) ) {
					$attrs['socialNetwork'] = $data['socialNetwork'];
				}
				if ( isset( $data['icon'] ) ) {
					$attrs['icon'] = $data['icon'];
				}
				break;

			case $slug === 'divi/breadcrumbs':
				foreach ( [ 'home', 'separator' ] as $bc_key ) {
					if ( isset( $data[ $bc_key ] ) ) {
						$attrs[ $bc_key ] = $data[ $bc_key ];
					}
				}
				foreach ( [ 'breadcrumbLink', 'breadcrumb', 'trail' ] as $bc_key ) {
					if ( isset( $data[ $bc_key ] ) ) {
						$attrs[ $bc_key ] = $data[ $bc_key ];
					}
				}
				break;

			case $slug === 'divi/link':
				$link_text = $data['text'] ?? ( is_string( $data['content'] ?? null ) ? $data['content'] : '' );
				$attrs['content'] = [
					'innerContent' => [ 'desktop' => [ 'value' => [
						'text'       => $link_text,
						'linkUrl'    => $data['link'] ?? $data['link_url'] ?? $data['url'] ?? '',
						'linkTarget' => $data['link_target'] ?? $data['target'] ?? 'off',
						'rel'        => $data['rel'] ?? [],
					] ] ],
					'decoration'   => [],
				];
				if ( isset( $data['font'] ) && is_array( $data['font'] ) ) {
					$attrs['content']['decoration']['font']['font'] = $data['font'];
				}
				if ( isset( $data['icon'] ) && is_array( $data['icon'] ) ) {
					$attrs['icon'] = [ 'innerContent' => $data['icon'] ];
				}
				break;

			case strpos( $slug, 'divi/fullwidth-' ) === 0:
				if ( isset( $data['content'] ) ) {
					$attrs['content']['innerContent'] = [ 'desktop' => [ 'value' => $data['content'] ] ];
				}
				break;
		}

		// Preserve nested blocks: modules routed through Generic may still be
		// container-like (e.g. map -> map-pin). Without this, children are dropped.
		return [
			'attrs'      => $attrs,
			'inner'      => '',
			'inner_html' => $children_html,
		];
	}
}
