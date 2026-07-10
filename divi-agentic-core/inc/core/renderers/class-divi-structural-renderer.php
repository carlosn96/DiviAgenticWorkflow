<?php
/**
 * Renderer: Divi Structural
 *
 * Handles section, row, column, column-inner, row-inner, group and group-like containers.
 *
 * @package Divi_Agentic_Core
 */

namespace Divi_Agentic_Core\Core\Renderers;

require_once __DIR__ . '/class-divi-base-renderer.php';

/**
 * Class Divi_Structural_Renderer
 */
class Divi_Structural_Renderer extends Divi_Base_Renderer {

	/** @var array Flex type mapping for column sizing. */
	private array $flex_map = [
		'4_4'      => '24_24',
		'1_2'      => '12_24',
		'1_3'      => '8_24',
		'2_3'      => '16_24',
		'3_4'      => '18_24',
		'1_4'      => '6_24',
		'1_1'      => '24_24',
		'2_5'      => '10_24',
		'1_5'      => '5_24',
		'3_5'      => '14_24',
		'vertical' => '24_24',
	];

	/**
	 * @inheritDoc
	 */
	public function render( string $slug, array $data, string $content_key, string $children_html ): array {
		$attrs = $this->prepare_base_attrs( $data, $data['builderVersion'] ?? '5.7.4' );

		switch ( $slug ) {
			case 'divi/section':
				$attrs = $this->render_section( $slug, $data, $attrs );
				break;

			case 'divi/row':
			case 'divi/row-inner':
				$attrs = $this->render_row( $slug, $data, $attrs );
				break;

			case 'divi/column':
			case 'divi/column-inner':
				$attrs = $this->render_column( $slug, $data, $attrs );
				break;
		}

		return [
			'attrs'      => $attrs,
			'inner'      => '',
			'inner_html' => '',
		];
	}

	/**
	 * Render divi/section.
	 *
	 * @param string $slug Block slug.
	 * @param array  $data Raw data.
	 * @param array  $attrs Prepared base attrs.
	 * @return array Updated attrs.
	 */
	private function render_section( string $slug, array $data, array $attrs ): array {
		$attrs['module']['advanced']['type'] = [
			'desktop' => [ 'value' => 'regular' ],
		];

		$parallax_val = ( isset( $data['parallax'] ) && $data['parallax'] === 'on' ) ? 'on' : 'off';

		if ( ! isset( $attrs['module']['decoration']['background']['desktop']['value'] ) ) {
			$attrs['module']['decoration']['background']['desktop']['value'] = [];
		}
		$bg_val = &$attrs['module']['decoration']['background']['desktop']['value'];

		$bg_was_empty = empty( $bg_val );

		if ( isset( $bg_val['overlay']['gradient'] ) && is_string( $bg_val['overlay']['gradient'] ) ) {
			$gradient_str = $bg_val['overlay']['gradient'];
			$parsed       = self::parse_css_gradient( $gradient_str );
			if ( $parsed ) {
				$parsed['overlaysImage'] = 'on';
				$bg_val['gradient']      = $parsed;
			}
			unset( $bg_val['overlay'] );
		}

		if ( ! empty( $data['background_image'] ) ) {
			$bg_val['image'] = [
				'url'      => $data['background_image'],
				'size'     => $data['bg_size'] ?? 'cover',
				'position' => $data['bg_position'] ?? 'center center',
				'repeat'   => $data['bg_repeat'] ?? 'no-repeat',
				'blend'    => $data['bg_blend'] ?? 'normal',
				'parallax' => [ 'enabled' => $parallax_val ],
			];
		}

		if ( ! empty( $data['bg_gradient'] ) && is_array( $data['bg_gradient'] ) ) {
			$bg_val['gradient'] = array_merge(
				[
					'enabled'       => 'on',
					'type'          => 'linear',
					'direction'     => '180deg',
					'overlaysImage' => 'on',
					'stops'         => [
						[ 'color' => 'rgba(0,0,0,0.6)', 'position' => '0%' ],
						[ 'color' => 'rgba(0,0,0,0)', 'position' => '100%' ],
					],
				],
				$data['bg_gradient']
			);
		}

		if ( ! empty( $data['parallax'] ) && isset( $bg_val['image'] ) ) {
			$bg_val['image']['parallax']['enabled'] = $parallax_val;
		}

		if ( $bg_was_empty && empty( $bg_val ) ) {
			unset( $attrs['module']['decoration']['background']['desktop']['value'] );
			if ( empty( $attrs['module']['decoration']['background']['desktop'] ) ) {
				unset( $attrs['module']['decoration']['background']['desktop'] );
			}
			if ( empty( $attrs['module']['decoration']['background'] ) ) {
				unset( $attrs['module']['decoration']['background'] );
			}
		}

		return $attrs;
	}

	/**
	 * Render divi/row.
	 *
	 * @param string $slug Block slug.
	 * @param array  $data Raw data.
	 * @param array  $attrs Prepared base attrs.
	 * @return array Updated attrs.
	 */
	private function render_row( string $slug, array $data, array $attrs ): array {
		$cols = $data['column_structure'] ?? '4_4';

		if ( is_array( $cols ) ) {
			$attrs['module']['advanced']['columnStructure'] = [];
			foreach ( [ 'desktop', 'tablet', 'phone' ] as $bp ) {
				if ( isset( $cols[ $bp ] ) ) {
					$attrs['module']['advanced']['columnStructure'][ $bp ] = [ 'value' => $cols[ $bp ] ];
				}
			}
		} else {
			$attrs['module']['advanced']['columnStructure'] = [
				'desktop' => [ 'value' => $cols ],
			];
		}

		$default_layout = [ 'flexWrap' => 'wrap' ];
		if ( isset( $attrs['module']['decoration']['layout']['desktop']['value'] ) && is_array( $attrs['module']['decoration']['layout']['desktop']['value'] ) ) {
			$attrs['module']['decoration']['layout']['desktop']['value'] = array_merge(
				$default_layout,
				$attrs['module']['decoration']['layout']['desktop']['value']
			);
		} else {
			$attrs['module']['decoration']['layout'] = [
				'desktop' => [ 'value' => $default_layout ],
			];
		}

		return $attrs;
	}

	/**
	 * Render divi/column and divi/column-inner.
	 *
	 * @param string $slug Block slug.
	 * @param array  $data Raw data.
	 * @param array  $attrs Prepared base attrs.
	 * @return array Updated attrs.
	 */
	private function render_column( string $slug, array $data, array $attrs ): array {
		if ( ! isset( $data['type'] ) ) {
			return $attrs;
		}

		if ( ! isset( $attrs['module']['advanced']['type'] ) ) {
			$attrs['module']['advanced']['type'] = [];
		}

		$attrs['module']['advanced']['type']['desktop'] = [ 'value' => $data['type'] ];

		if ( $data['type'] !== '4_4' ) {
			if ( ! isset( $attrs['module']['advanced']['type']['phone'] ) ) {
				$attrs['module']['advanced']['type']['phone'] = [ 'value' => 'vertical' ];
			}
			if ( ! isset( $attrs['module']['advanced']['type']['tablet'] ) ) {
				$attrs['module']['advanced']['type']['tablet'] = [ 'value' => $data['type'] ];
			}
		}

		if ( ! isset( $attrs['module']['decoration']['sizing'] ) ) {
			$attrs['module']['decoration']['sizing'] = [];
		}
		if ( ! isset( $attrs['module']['decoration']['sizing']['desktop']['value']['flexType'] ) ) {
			$attrs['module']['decoration']['sizing']['desktop'] = [ 'value' => [ 'flexType' => $this->flex_map[ $data['type'] ] ?? '24_24' ] ];
		}

		foreach ( [ 'tablet', 'phone' ] as $bp ) {
			if ( isset( $attrs['module']['advanced']['type'][ $bp ]['value'] ) ) {
				$bp_type = $attrs['module']['advanced']['type'][ $bp ]['value'];
				if ( ! isset( $attrs['module']['decoration']['sizing'][ $bp ]['value']['flexType'] ) ) {
					$attrs['module']['decoration']['sizing'][ $bp ] = [ 'value' => [ 'flexType' => $this->flex_map[ $bp_type ] ?? '24_24' ] ];
				}
			}
		}

		// Forward column custom CSS class to htmlAttributes (Divi 5 ignores css.className on columns)
		$col_class = $data['advanced']['css']['className'] ?? '';
		if ( ! empty( $col_class ) ) {
			if ( ! isset( $attrs['module']['advanced']['htmlAttributes'] ) ) {
				$attrs['module']['advanced']['htmlAttributes'] = [];
			}
			if ( ! isset( $attrs['module']['advanced']['htmlAttributes']['desktop'] ) ) {
				$attrs['module']['advanced']['htmlAttributes']['desktop'] = [ 'value' => [] ];
			}
			$attrs['module']['advanced']['htmlAttributes']['desktop']['value']['class'] = $col_class;
		}

		return $attrs;
	}
}
