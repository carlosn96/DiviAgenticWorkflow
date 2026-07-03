<?php
$code = file_get_contents( 'DAW_bundle/divi-agentic-core/inc/core/class-layout-engine.php' );
$tokens = token_get_all( $code );
$balance = 0;
$start   = false;
foreach ( $tokens as $tok ) {
	if ( is_array( $tok ) ) {
		if ( $tok[0] === T_CLASS ) {
			$start = true;
		}
		if ( in_array( $tok[0], [ T_CONSTANT_ENCAPSED_STRING, T_INLINE_HTML, T_COMMENT, T_DOC_COMMENT ], true ) ) {
			continue;
		}
		$txt = $tok[1];
	} else {
		$txt = $tok;
	}
	if ( ! $start ) {
		continue;
	}
	$balance += substr_count( $txt, '{' ) - substr_count( $txt, '}' );
}
echo "Class balance: $balance\n";
