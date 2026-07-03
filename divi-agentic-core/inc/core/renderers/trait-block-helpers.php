<?php
/**
 * Trait: Block Helpers
 *
 * Pure stateless utilities shared by all renderers.
 *
 * @package Divi_Agentic_Core
 */

namespace Divi_Agentic_Core\Core\Renderers;

/**
 * Trait Block_Helpers
 *
 * All methods are static and side-effect free. They can be used by any
 * renderer, including third-party ones (dgpc/dac), without inheriting from
 * Divi-specific base classes.
 */
trait Block_Helpers {

	/**
	 * Recursively convert var(--gcid-*) to $variable() syntax for Divi 5 VB recognition.
	 *
	 * The Divi 5 Visual Builder requires $variable({"type":"color","value":{"name":"gcid-*","settings":{}}})$
	 * format in block attributes to recognize global color references. The frontend resolver
	 * converts it back to var(--gcid-*) during CSS rendering.
	 *
	 * @param mixed $value Value to convert (string, array, or scalar).
	 * @return mixed Converted value.
	 */
	public static function convert_gcid_to_variable_syntax( $value ) {
		if ( is_string( $value ) && preg_match( '/^var\(--(gcid-[0-9a-z-]+)\)$/', $value, $m ) ) {
			$json = wp_json_encode(
				[
					'type'  => 'color',
					'value' => [
						'name'     => $m[1],
						'settings' => new \stdClass(),
					],
				],
				JSON_UNESCAPED_SLASHES
			);
			return "\$variable({$json})\$";
		}

		if ( is_array( $value ) ) {
			foreach ( $value as $k => $v ) {
				$value[ $k ] = self::convert_gcid_to_variable_syntax( $v );
			}
		}

		return $value;
	}

	/**
	 * Parse a CSS gradient string ("linear-gradient(165deg, #hex 0%, ...)")
	 * into a Divi 5 structured gradient object.
	 *
	 * Supports linear and radial gradients.
	 *
	 * @param string $gradient CSS gradient string.
	 * @return array|null Structured gradient or null if invalid.
	 */
	public static function parse_css_gradient( string $gradient ): ?array {
		$gradient = trim( $gradient );
		if ( ! preg_match( '/^(linear|radial)-gradient\s*\((.+)\)$/s', $gradient, $m ) ) {
			return null;
		}

		$type = $m[1] === 'radial' ? 'radial' : 'linear';
		$body = $m[2];

		$parts = [];
		$depth = 0;
		$buf   = '';

		for ( $i = 0, $len = strlen( $body ); $i < $len; $i++ ) {
			$ch = $body[ $i ];
			if ( $ch === '(' ) {
				$depth++;
				$buf .= $ch;
			} elseif ( $ch === ')' ) {
				$depth--;
				$buf .= $ch;
			} elseif ( $ch === ',' && $depth === 0 ) {
				$parts[] = trim( $buf );
				$buf     = '';
			} else {
				$buf .= $ch;
			}
		}

		if ( $buf !== '' ) {
			$parts[] = trim( $buf );
		}

		if ( empty( $parts ) ) {
			return null;
		}

		$direction = '180deg';
		$stops     = [];
		$offset    = 0;

		if ( $type === 'linear' ) {
			$first = $parts[0];
			if ( preg_match( '/^\d+deg$/', $first )
				|| in_array( $first, [ 'to top', 'to bottom', 'to left', 'to right', 'to top left', 'to top right', 'to bottom left', 'to bottom right' ], true )
			) {
				$direction = $first;
				$offset    = 1;
			} elseif ( preg_match( '/^(to\s+\S+(?:\s+\S+)?)$/i', $first ) ) {
				$direction = $first;
				$offset    = 1;
			}
		} elseif ( $type === 'radial' ) {
			// Radial has shape/size/position before stops; skip for now.
			$offset = 1;
		}

		for ( $i = $offset; $i < count( $parts ); $i++ ) {
			$stop = trim( $parts[ $i ] );
			if ( preg_match( '/(#[0-9a-fA-F]+|[a-zA-Z]+\([^)]*\)|rgba?\([^)]*\)|hsla?\([^)]*\))/', $stop, $c_match ) ) {
				$color    = $c_match[1];
				$rest     = trim( substr( $stop, strlen( $c_match[0] ) ) );
				$position = '50';
				if ( preg_match( '/([\d.]+)%/', $rest, $p_match ) ) {
					$position = $p_match[1];
				}
				$stops[] = [ 'color' => $color, 'position' => $position ];
			}
		}

		if ( empty( $stops ) ) {
			return null;
		}

		return [
			'type'      => $type,
			'direction' => $direction,
			'stops'     => $stops,
		];
	}

	/**
	 * Normalize gradient stop positions: strip trailing % if present.
	 *
	 * Divi 5 Background::gradient_style_declaration() appends unit (default %)
	 * to position, so "0%" + "%" = "0%%" which breaks CSS.
	 *
	 * @param array $attrs Block attributes.
	 * @return array Normalized attributes.
	 */
	public static function normalize_gradient_stops( array $attrs ): array {
		if ( isset( $attrs['module']['decoration']['background']['desktop']['value']['gradient']['stops'] ) ) {
			$stops = &$attrs['module']['decoration']['background']['desktop']['value']['gradient']['stops'];
			foreach ( $stops as &$stop ) {
				if ( isset( $stop['position'] ) && is_string( $stop['position'] ) ) {
					$stop['position'] = rtrim( $stop['position'], '%' );
				}
			}
			unset( $stop );
		}

		return $attrs;
	}

	/**
	 * Remove empty "value": [] from background breakpoints.
	 *
	 * Divi 5 requires background.value to be an object or contain valid props;
	 * an empty array causes decoding issues.
	 *
	 * @param array $attrs Block attributes.
	 * @return array Normalized attributes.
	 */
	public static function normalize_empty_background( array $attrs ): array {
		if ( ! isset( $attrs['module']['decoration']['background'] ) || ! is_array( $attrs['module']['decoration']['background'] ) ) {
			return $attrs;
		}

		foreach ( [ 'desktop', 'tablet', 'phone' ] as $bp ) {
			if ( isset( $attrs['module']['decoration']['background'][ $bp ]['value'] ) ) {
				$bv = $attrs['module']['decoration']['background'][ $bp ]['value'];
				if ( is_array( $bv ) && empty( $bv ) ) {
					unset( $attrs['module']['decoration']['background'][ $bp ]['value'] );
				}
			}
		}

		$bg_arr = $attrs['module']['decoration']['background'];
		if ( empty( $bg_arr['desktop'] ) && empty( $bg_arr['tablet'] ) && empty( $bg_arr['phone'] ) ) {
			unset( $attrs['module']['decoration']['background'] );
		}

		return $attrs;
	}
}
