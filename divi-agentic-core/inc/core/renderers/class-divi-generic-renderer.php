<?php
/**
 * Renderer: Divi Generic
 *
 * Handles divider, map/fullwidth-map, blog, sidebar, login,
 * contact-form-7, icon-list-item, lottie, svg, map-pin, dropdown,
 * portfolio/filterable-portfolio, before-after-image, canvas-portal,
 * breadcrumbs, link, post-slider, signup, signup-custom-field,
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
		$attrs = $this->prepare_base_attrs( $data, $data['builderVersion'] ?? '5.7.4' );

		switch ( true ) {
			case $slug === 'divi/divider':
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
				if ( isset( $data['address'] ) ) {
					$attrs['map']['innerContent'] = [ 'desktop' => [ 'value' => $data['address'] ] ];
				}
				if ( isset( $data['mouse_wheel'] ) ) {
					$attrs['map']['advanced']['mouseWheel'] = [ 'desktop' => [ 'value' => $data['mouse_wheel'] ] ];
				}
				if ( isset( $data['mobile_dragging'] ) ) {
					$attrs['map']['advanced']['mobileDragging'] = [ 'desktop' => [ 'value' => $data['mobile_dragging'] ] ];
				}
				break;

			case $slug === 'divi/blog':
				$post_attrs = [];
				foreach ( [
					'type', 'number', 'categories', 'dateFormat', 'excerptLength', 'offset',
					'showExcerpt', 'showAuthor', 'showDate', 'showCategories', 'showComments',
					'useCurrentLoop',
				] as $key ) {
					if ( isset( $data[ $key ] ) ) {
						$post_attrs[ $key ] = $data[ $key ];
					}
				}
				if ( ! empty( $post_attrs ) ) {
					$attrs['post']['advanced'] = [];
					foreach ( $post_attrs as $k => $v ) {
						$attrs['post']['advanced'][ $k ] = [ 'desktop' => [ 'value' => $v ] ];
					}
				}
				if ( isset( $data['show_featured_image'] ) ) {
					$attrs['image']['advanced']['enable'] = [ 'desktop' => [ 'value' => $data['show_featured_image'] ] ];
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
				$label = $data['title'] ?? ( isset( $data['content'] ) && is_string( $data['content'] ) ? $data['content'] : null );
				if ( $label !== null ) {
					$attrs['title']['innerContent'] = [ 'desktop' => [ 'value' => $label ] ];
				}
				if ( isset( $data['icon'] ) ) {
					$attrs['icon'] = [ 'advanced' => [ 'icon' => [ 'desktop' => [ 'value' => $data['icon'] ] ] ] ];
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
				if ( isset( $data['address'] ) ) {
					$attrs['pin'] = [ 'innerContent' => [ 'desktop' => [ 'value' => $data['address'] ] ] ];
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

			case in_array( $slug, [
				'divi/before-after-image', 'divi/canvas-portal', 'divi/breadcrumbs',
				'divi/link', 'divi/post-slider', 'divi/signup-custom-field',
			], true ):
				if ( isset( $data['before_src'] ) && isset( $data['after_src'] ) ) {
					$attrs['image'] = [ 'innerContent' => [ 'desktop' => [ 'value' => [
						'before' => $data['before_src'],
						'after'  => $data['after_src'],
					] ] ] ];
				}
				break;

			case $slug === 'divi/timeline-item':
				foreach ( [ 'date', 'title', 'content', 'marker', 'spacer' ] as $tl_key ) {
					if ( isset( $data[ $tl_key ] ) ) {
						$attrs[ $tl_key ] = $data[ $tl_key ];
					}
				}
				break;

			case strpos( $slug, 'divi/fullwidth-' ) === 0:
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
