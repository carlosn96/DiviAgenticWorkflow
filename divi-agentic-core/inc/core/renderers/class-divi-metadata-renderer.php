<?php
/**
 * Renderer: Divi Metadata
 *
 * Metadata-driven renderer for Divi 5 modules that have no dedicated
 * family renderer. Maps schema attributes to their canonical Divi 5
 * serialization paths using the official metadata files:
 *
 *   - data/_all_modules_metadata.php                 (types, settings, innerContent groups)
 *   - data/_all_modules_default_render_attributes.php (canonical default shapes)
 *
 * Modules handled here (dispatched from Layout_Engine::resolve_divi_renderer):
 * charts, tooltip, table-of-contents, instagram-feed, gravity-forms,
 * imagely-gallery, before-after-image, signup-custom-field, canvas-portal,
 * payment-button, counters, post-filter, post-filter-item, post-slider,
 * fullwidth-post-slider.
 *
 * It also preserves nested blocks (children) so container-like modules keep
 * their inner modules on deploy.
 *
 * @package Divi_Agentic_Core
 */

namespace Divi_Agentic_Core\Core\Renderers;

require_once __DIR__ . '/class-divi-base-renderer.php';

/**
 * Class Divi_Metadata_Renderer
 */
class Divi_Metadata_Renderer extends Divi_Base_Renderer {

	/**
	 * Container keys that mark an incoming value as an already-canonical
	 * Divi 5 attribute structure (e.g. produced by export_page).
	 */
	private const CANONICAL_KEYS = [
		'innerContent', 'decoration', 'advanced', 'meta',
		'desktop', 'tablet', 'phone', 'css', 'attributes',
	];

	/**
	 * @inheritDoc
	 */
	public function render( string $slug, array $data, string $content_key, string $children_html ): array {
		$attrs = $this->prepare_base_attrs( $data, $data['builderVersion'] ?? DIVI_BUILDER_VERSION );

		$meta = $this->get_meta( $slug );

		if ( $meta && ! empty( $meta['attributes'] ) ) {
			foreach ( $meta['attributes'] as $attr => $def ) {
				// `module` and `children` are structural, never data attributes.
				if ( 'module' === $attr || 'children' === $attr ) {
					continue;
				}
				// FreeForm CSS (`css` as a string) is already handled by prepare_base_attrs.
				if ( 'css' === $attr && ! is_array( $data['css'] ?? null ) ) {
					continue;
				}
				if ( ! array_key_exists( $attr, $data ) ) {
					continue;
				}
				$mapped = $this->map_attribute( $def, $data[ $attr ], $attrs[ $attr ] ?? null );
				if ( null !== $mapped ) {
					$attrs[ $attr ] = $mapped;
				}
			}
		}

		// Flat authoring shorthands for modules whose convenience keys differ
		// from their canonical attribute name.
		$this->apply_shorthands( $slug, $data, $attrs );

		return [
			'attrs'      => $attrs,
			'inner'      => '',
			'inner_html' => $children_html,
		];
	}

	/**
	 * Read a module's official metadata, reusing Layout_Engine's cache.
	 */
	private function get_meta( string $slug ): ?array {
		if ( class_exists( '\DAC\Core\Layout_Engine' ) ) {
			return \DAC\Core\Layout_Engine::get_module_meta( $slug );
		}
		return null;
	}

	/**
	 * Map a flat schema value to the canonical Divi 5 shape for an attribute.
	 *
	 * @param array $def      Attribute definition from the metadata.
	 * @param mixed $value    Incoming schema value.
	 * @param mixed $existing Existing canonical value (unused when none).
	 * @return mixed Canonical attribute value.
	 */
	private function map_attribute( array $def, $value, $existing ) {
		// Already canonical (export round-trip) -> deep merge.
		if ( $this->is_canonical( $value ) ) {
			return is_array( $existing ) ? array_replace_recursive( $existing, $value ) : $value;
		}

		$ic = $def['settings']['innerContent'] ?? null;

		if ( $ic ) {
			$group_type = $ic['groupType'] ?? 'group-item';

			if ( 'group-item' === $group_type ) {
				return [ 'innerContent' => [ 'desktop' => [ 'value' => $value ] ] ];
			}

			// group-items / into-multiple-groups expect an object of sub-values.
			if ( is_array( $value ) ) {
				$grouped = $value;
			} else {
				$items   = isset( $ic['items'] ) ? array_keys( $ic['items'] ) : [];
				$key     = $items[0] ?? 'value';
				$grouped = [ $key => $value ];
			}

			return [ 'innerContent' => [ 'desktop' => [ 'value' => $grouped ] ] ];
		}

		// No innerContent: structured values pass through untouched.
		if ( is_array( $value ) ) {
			return $value;
		}

		// Object attributes with style groups (advanced/decoration/meta) expect
		// a nested object, not a scalar. Leave the scalar to the authoring
		// shorthands (or the passthrough) to avoid emitting an invalid shape.
		$settings = $def['settings'] ?? [];
		if ( isset( $settings['advanced'] ) || isset( $settings['decoration'] ) || isset( $settings['meta'] ) ) {
			return null;
		}

		return $value;
	}

	/**
	 * Detect an already-canonical Divi 5 attribute value.
	 */
	private function is_canonical( $value ): bool {
		if ( ! is_array( $value ) ) {
			return false;
		}
		foreach ( self::CANONICAL_KEYS as $key ) {
			if ( array_key_exists( $key, $value ) ) {
				return true;
			}
		}
		return false;
	}

	/**
	 * Set an attribute's innerContent value, merging with whatever exists.
	 */
	private function set_inner( array &$attrs, string $attr, $value ): void {
		$current = $attrs[ $attr ]['innerContent']['desktop']['value'] ?? [];
		if ( is_array( $current ) && is_array( $value ) ) {
			$value = array_replace_recursive( $current, $value );
		}
		$attrs[ $attr ]['innerContent'] = [ 'desktop' => [ 'value' => $value ] ];
	}

	/**
	 * Flat authoring shorthands: convenience keys -> canonical paths.
	 */
	private function apply_shorthands( string $slug, array $data, array &$attrs ): void {
		switch ( $slug ) {
			case 'divi/charts':
				if ( isset( $data['chart_type'] ) ) {
					$attrs['chart']['advanced']['config']['desktop']['value']['type'] = $data['chart_type'];
				}
				if ( ! isset( $data['chart'] ) ) {
					$chart = [];
					foreach ( [ 'data', 'title', 'subtitle' ] as $key ) {
						if ( isset( $data[ $key ] ) ) {
							$chart[ $key ] = $data[ $key ];
						}
					}
					if ( isset( $data['legend_title'] ) ) {
						$chart['legendTitle'] = $data['legend_title'];
					} elseif ( isset( $data['legendTitle'] ) ) {
						$chart['legendTitle'] = $data['legendTitle'];
					}
					if ( ! empty( $chart ) ) {
						$this->set_inner( $attrs, 'chart', $chart );
					}
				}
				break;

			case 'divi/gravity-forms':
				if ( ! isset( $data['gravityForm'] ) ) {
					$form_id = $data['form_id'] ?? $data['formId'] ?? null;
					if ( null !== $form_id ) {
						$this->set_inner( $attrs, 'gravityForm', [ 'formId' => $form_id ] );
					}
				}
				break;

			case 'divi/instagram-feed':
				if ( ! isset( $data['feed'] ) ) {
					$feed = [];
					if ( isset( $data['account'] ) ) {
						$feed['accountId'] = $data['account'];
					}
					if ( isset( $data['account_id'] ) ) {
						$feed['accountId'] = $data['account_id'];
					}
					if ( isset( $data['post_count'] ) ) {
						$feed['postCount'] = $data['post_count'];
					}
					if ( ! empty( $feed ) ) {
						$this->set_inner( $attrs, 'feed', $feed );
					}
				}
				break;

			case 'divi/before-after-image':
				if ( ! isset( $data['beforeImage'] ) && isset( $data['before_src'] ) ) {
					$this->set_inner( $attrs, 'beforeImage', [ 'beforeImageSrc' => $data['before_src'] ] );
				}
				if ( ! isset( $data['afterImage'] ) && isset( $data['after_src'] ) ) {
					$this->set_inner( $attrs, 'afterImage', [ 'afterImageSrc' => $data['after_src'] ] );
				}
				break;

			case 'divi/payment-button':
				if ( ! isset( $data['button'] ) ) {
					$button = [];
					foreach ( [ 'provider', 'environment', 'amountMode', 'amount', 'currency', 'openInNewTab' ] as $key ) {
						if ( isset( $data[ $key ] ) ) {
							$button[ $key ] = $data[ $key ];
						}
					}
					if ( ! empty( $button ) ) {
						$this->set_inner( $attrs, 'button', $button );
					}
				}
				break;

			case 'divi/imagely-gallery':
				if ( ! isset( $data['imagelyGallery'] ) ) {
					$gallery_id = $data['gallery_id'] ?? $data['galleryId'] ?? null;
					if ( null !== $gallery_id ) {
						$this->set_inner( $attrs, 'imagelyGallery', $gallery_id );
					}
				}
				break;

			case 'divi/canvas-portal':
				if ( ! isset( $data['canvas'] ) ) {
					$canvas_id = $data['canvas_id'] ?? $data['canvasId'] ?? null;
					if ( null !== $canvas_id ) {
						$attrs['canvas']['advanced']['canvasId'] = [ 'desktop' => [ 'value' => $canvas_id ] ];
					}
				}
				break;

			case 'divi/post-slider':
			case 'divi/fullwidth-post-slider':
				foreach ( [ 'number', 'categories', 'orderby', 'offset', 'excerptLength', 'contentSource', 'excerptManual' ] as $key ) {
					if ( isset( $data[ $key ] ) ) {
						$attrs['post']['advanced'][ $key ] = [ 'desktop' => [ 'value' => $data[ $key ] ] ];
					}
				}
				if ( isset( $data['button_text'] ) || isset( $data['button_url'] ) ) {
					$this->set_inner( $attrs, 'button', [
						'text'    => $data['button_text'] ?? '',
						'linkUrl' => $data['button_url'] ?? '',
					] );
				}
				if ( isset( $data['arrows'] ) && ! is_array( $data['arrows'] ) ) {
					$attrs['arrows']['advanced']['enable'] = [ 'desktop' => [ 'value' => $data['arrows'] ] ];
				}
				if ( isset( $data['pagination'] ) && ! is_array( $data['pagination'] ) ) {
					$attrs['pagination']['advanced']['enable'] = [ 'desktop' => [ 'value' => $data['pagination'] ] ];
				}
				break;

			case 'divi/post-filter':
				if ( isset( $data['apply_mode'] ) || isset( $data['relation'] ) ) {
					if ( ! isset( $attrs['module']['advanced']['filters'] ) ) {
						$attrs['module']['advanced']['filters'] = [ 'desktop' => [ 'value' => [] ] ];
					}
					if ( isset( $data['apply_mode'] ) ) {
						$attrs['module']['advanced']['filters']['desktop']['value']['applyMode'] = $data['apply_mode'];
					}
					if ( isset( $data['relation'] ) ) {
						$attrs['module']['advanced']['filters']['desktop']['value']['relation'] = $data['relation'];
					}
				}
				break;
		}
	}
}
