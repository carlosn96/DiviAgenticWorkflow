<?php
/**
 * Renderer: Divi Base (abstract)
 *
 * Common attribute preparation shared by all divi/* renderers.
 *
 * @package Divi_Agentic_Core
 */

namespace Divi_Agentic_Core\Core\Renderers;

require_once __DIR__ . '/interface-block-renderer.php';
require_once __DIR__ . '/trait-block-helpers.php';

/**
 * Class Divi_Base_Renderer
 *
 * Implementa la preparacion base de atributos para bloques divi/*:
 * - merge de style_keys
 * - deep-merge de module{}
 * - CSS freeForm
 * - auto-wrap de decoration (con bugfix de stray keys)
 * - htmlAttributes (module_class, module_id)
 */
abstract class Divi_Base_Renderer implements Block_Renderer_Interface {
	use Block_Helpers;

	/**
	 * Prepare base attrs array for a divi/* block (static helper).
	 *
	 * @param array  $data           Raw block data.
	 * @param string $builder_version Divi builder version.
	 * @return array{
	 *   builderVersion: string,
	 *   module: array
	 * }
	 */
	public static function prepare_base_attrs_static( array $data, string $builder_version ): array {
		$attrs = [
			'builderVersion' => $builder_version,
			'module'         => [],
		];

		$style_keys = [ 'decoration', 'boxShadow', 'spacing', 'meta', 'advanced', 'headingFont', 'bodyFont', 'animation', 'transform' ];
		foreach ( $style_keys as $key ) {
			if ( isset( $data[ $key ] ) ) {
				$attrs['module'][ $key ] = $data[ $key ];
			}
		}

		if ( isset( $data['module'] ) && is_array( $data['module'] ) ) {
			foreach ( $data['module'] as $mk => $mv ) {
				if ( is_array( $mv ) && isset( $attrs['module'][ $mk ] ) && is_array( $attrs['module'][ $mk ] ) ) {
					$attrs['module'][ $mk ] = array_replace_recursive( $attrs['module'][ $mk ], $mv );
				} else {
					$attrs['module'][ $mk ] = $mv;
				}
			}
		}

		// Custom CSS freeForm
		if ( isset( $data['css'] ) ) {
			$css = $data['css'];
			if ( is_string( $css ) ) {
				$attrs['css'] = [ 'desktop' => [ 'value' => [ 'freeForm' => $css ] ] ];
			} elseif ( is_array( $css ) ) {
				foreach ( [ 'desktop', 'tablet', 'phone' ] as $bp ) {
					if ( isset( $css[ $bp ] ) ) {
						$bp_css = $css[ $bp ];
						if ( is_string( $bp_css ) ) {
							$attrs['css'][ $bp ] = [ 'value' => [ 'freeForm' => $bp_css ] ];
						} elseif ( is_array( $bp_css ) ) {
							$attrs['css'][ $bp ] = $bp_css;
						}
					}
				}
			}
		}

		// htmlAttributes from module_class / module_id
		$module_class = $data['module_class'] ?? '';
		$module_id    = $data['module_id'] ?? '';
		if ( ! empty( $module_class ) || ! empty( $module_id ) ) {
			$html_attrs = [];
			if ( ! empty( $module_class ) ) {
				$html_attrs['class'] = $module_class;
			}
			if ( ! empty( $module_id ) ) {
				$html_attrs['id'] = $module_id;
			}
			if ( ! isset( $attrs['module']['advanced'] ) ) {
				$attrs['module']['advanced'] = [];
			}
			$attrs['module']['advanced']['htmlAttributes'] = [
				'desktop' => [ 'value' => $html_attrs ],
			];
		}

		return self::wrap_decoration_static( $attrs );
	}

	/**
	 * Static wrapper for decoration auto-wrap.
	 */
	private static function wrap_decoration_static( array $attrs ): array {
		$dec_modes = [ 'desktop', 'tablet', 'phone', 'hover', 'sticky' ];
		if ( ! isset( $attrs['module']['decoration'] ) ) {
			return $attrs;
		}
		foreach ( [ 'background', 'spacing', 'layout', 'sizing', 'border', 'boxShadow', 'filter', 'transform', 'transition', 'animation', 'position', 'scroll' ] as $dk ) {
			if ( ! isset( $attrs['module']['decoration'][ $dk ] ) ) {
				continue;
			}
			$cur = $attrs['module']['decoration'][ $dk ];
			if ( ! is_array( $cur ) ) {
				$attrs['module']['decoration'][ $dk ] = [
					'desktop' => [ 'value' => $cur ],
				];
				continue;
			}
			$modes    = array_keys( $cur );
			$has_mode = ! empty( array_intersect( $dec_modes, $modes ) );
			if ( ! $has_mode ) {
				$attrs['module']['decoration'][ $dk ] = [
					'desktop' => [ 'value' => $cur ],
				];
			} else {
				$stray = array_diff( $modes, $dec_modes );
				if ( ! empty( $stray ) ) {
					$stray_map = [];
					foreach ( $stray as $sk ) {
						$stray_map[ $sk ] = $cur[ $sk ];
						unset( $cur[ $sk ] );
					}
					if ( ! isset( $cur['desktop'] ) ) {
						$cur['desktop'] = [ 'value' => [] ];
					}
					if ( ! is_array( $cur['desktop'] ) ) {
						$cur['desktop'] = [ 'value' => $cur['desktop'] ];
					}
					if ( ! isset( $cur['desktop']['value'] ) || ! is_array( $cur['desktop']['value'] ) ) {
						$cur['desktop']['value'] = [];
					}
					$cur['desktop']['value'] = array_merge( $stray_map, $cur['desktop']['value'] );
					$attrs['module']['decoration'][ $dk ] = $cur;
				}
			}
		}
		return $attrs;
	}

	/**
	 * Prepare base attrs array for a divi/* block.
	 *
	 * @param array  $data           Raw block data.
	 * @param string $builder_version Divi builder version.
	 * @return array{
	 *   builderVersion: string,
	 *   module: array
	 * }
	 */
	protected function prepare_base_attrs( array $data, string $builder_version ): array {
		$attrs = [
			'builderVersion' => $builder_version,
			'module'         => [],
		];

		$style_keys = [ 'decoration', 'boxShadow', 'spacing', 'meta', 'advanced', 'headingFont', 'bodyFont', 'animation', 'transform' ];
		foreach ( $style_keys as $key ) {
			if ( isset( $data[ $key ] ) ) {
				$attrs['module'][ $key ] = $data[ $key ];
			}
		}

		if ( isset( $data['module'] ) && is_array( $data['module'] ) ) {
			foreach ( $data['module'] as $mk => $mv ) {
				if ( is_array( $mv ) && isset( $attrs['module'][ $mk ] ) && is_array( $attrs['module'][ $mk ] ) ) {
					$attrs['module'][ $mk ] = array_replace_recursive( $attrs['module'][ $mk ], $mv );
				} else {
					$attrs['module'][ $mk ] = $mv;
				}
			}
		}

		// Custom CSS freeForm
		if ( isset( $data['css'] ) ) {
			$css = $data['css'];
			if ( is_string( $css ) ) {
				$attrs['css'] = [ 'desktop' => [ 'value' => [ 'freeForm' => $css ] ] ];
			} elseif ( is_array( $css ) ) {
				foreach ( [ 'desktop', 'tablet', 'phone' ] as $bp ) {
					if ( isset( $css[ $bp ] ) ) {
						$bp_css = $css[ $bp ];
						if ( is_string( $bp_css ) ) {
							$attrs['css'][ $bp ] = [ 'value' => [ 'freeForm' => $bp_css ] ];
						} elseif ( is_array( $bp_css ) ) {
							$attrs['css'][ $bp ] = $bp_css;
						}
					}
				}
			}
		}

		// Auto-wrap decoration values with desktop.value
		$attrs = $this->wrap_decoration( $attrs );

		// htmlAttributes from module_class / module_id
		$module_class = $data['module_class'] ?? '';
		$module_id    = $data['module_id'] ?? '';
		if ( ! empty( $module_class ) || ! empty( $module_id ) ) {
			$html_attrs = [];
			if ( ! empty( $module_class ) ) {
				$html_attrs['class'] = $module_class;
			}
			if ( ! empty( $module_id ) ) {
				$html_attrs['id'] = $module_id;
			}
			if ( ! isset( $attrs['module']['advanced'] ) ) {
				$attrs['module']['advanced'] = [];
			}
			$attrs['module']['advanced']['htmlAttributes'] = [
				'desktop' => [ 'value' => $html_attrs ],
			];
		}

		return $attrs;
	}

	/**
	 * Auto-wrap decoration values with desktop.value when they lack a Divi mode key.
	 *
	 * Mueve keys sueltas (como background.color) dentro de desktop.value para evitar
	 * el error "array_keys(): Argument #1 ($array) must be of type array, string given".
	 *
	 * @param array $attrs Block attributes.
	 * @return array Normalized attributes.
	 */
	protected function wrap_decoration( array $attrs ): array {
		if ( ! isset( $attrs['module']['decoration'] ) ) {
			return $attrs;
		}

		$dec_modes = [ 'desktop', 'tablet', 'phone', 'hover', 'sticky' ];
		foreach ( [ 'background', 'spacing', 'layout', 'sizing', 'border', 'boxShadow', 'filter', 'transform', 'transition', 'animation', 'position', 'scroll' ] as $dk ) {
			if ( ! isset( $attrs['module']['decoration'][ $dk ] ) ) {
				continue;
			}

			$cur = $attrs['module']['decoration'][ $dk ];
			if ( ! is_array( $cur ) ) {
				$attrs['module']['decoration'][ $dk ] = [
					'desktop' => [ 'value' => $cur ],
				];
				continue;
			}

			$modes    = array_keys( $cur );
			$has_mode = ! empty( array_intersect( $dec_modes, $modes ) );

			if ( ! $has_mode ) {
				$attrs['module']['decoration'][ $dk ] = [
					'desktop' => [ 'value' => $cur ],
				];
			} else {
				$stray = array_diff( $modes, $dec_modes );
				if ( ! empty( $stray ) ) {
					$stray_map = [];
					foreach ( $stray as $sk ) {
						$stray_map[ $sk ] = $cur[ $sk ];
						unset( $cur[ $sk ] );
					}
					if ( ! isset( $cur['desktop'] ) ) {
						$cur['desktop'] = [ 'value' => [] ];
					}
					if ( ! is_array( $cur['desktop'] ) ) {
						$cur['desktop'] = [ 'value' => $cur['desktop'] ];
					}
					if ( ! isset( $cur['desktop']['value'] ) || ! is_array( $cur['desktop']['value'] ) ) {
						$cur['desktop']['value'] = [];
					}
					$cur['desktop']['value'] = array_merge( $stray_map, $cur['desktop']['value'] );
					$attrs['module']['decoration'][ $dk ] = $cur;
				}
			}
		}

		return $attrs;
	}

	/**
	 * Helper: prepare content.innerContent from $data['content'].
	 *
	 * @param array  $data Raw block data.
	 * @param array  $attrs Current attributes.
	 * @return array Updated attributes.
	 */
	protected function prepare_content_inner_content( array $data, array $attrs ): array {
		if ( ! isset( $data['content'] ) ) {
			return $attrs;
		}

		if ( is_string( $data['content'] ) ) {
			$attrs['content']['innerContent'] = [
				'desktop' => [ 'value' => $data['content'] ],
			];
		} elseif ( isset( $data['content']['innerContent'] ) ) {
			$attrs['content'] = $data['content'];
		} else {
			$attrs['content']['innerContent'] = [
				'desktop' => [ 'value' => $data['content'] ],
			];
		}

		return $attrs;
	}
}
