<?php
$code = file_get_contents( 'DAW_bundle/divi-agentic-core/inc/core/class-layout-engine.php' );
$tokens = token_get_all( $code );
$balance = 0;
foreach ( $tokens as $tok ) {
	if ( is_array( $tok ) ) {
		if ( in_array( $tok[0], [ T_CONSTANT_ENCAPSED_STRING, T_INLINE_HTML, T_COMMENT, T_DOC_COMMENT ], true ) ) {
			continue;
		}
		$txt = $tok[1];
	} else {
		$txt = $tok;
	}
	$balance += substr_count( $txt, '{' ) - substr_count( $txt, '}' );
}
echo "Balance: $balance\n";
