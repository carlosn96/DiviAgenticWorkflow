<?php
/**
 * Render callback for divi/plus-counter (container mode).
 * Wraps InnerBlocks ($block_content) in a layout wrapper.
 * VB edits child modules (divi/icon, divi/number-counter, divi/text) natively.
 */
if ( ! function_exists( 'daw_pc_extract_value' ) ) {
	function daw_pc_extract_value( $val ) {
		if ( is_string( $val ) ) return $val;
		if ( is_array( $val ) ) {
			if ( isset( $val['innerContent']['desktop']['value'] ) ) {
				$inner = $val['innerContent']['desktop']['value'];
				return is_string( $inner ) ? $inner : '';
			}
		}
		return '';
	}
}

$layout = daw_pc_extract_value( $block_attrs['layout_style'] ?? '01' );
?>
<div class="daw-plus-counter layout-<?php echo esc_attr( $layout ); ?>" data-layout="<?php echo esc_attr( $layout ); ?>">
<?php echo $block_content; ?>
</div>