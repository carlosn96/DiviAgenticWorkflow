<?php
$code = file_get_contents( 'DAW_bundle/divi-agentic-core/inc/core/class-layout-engine.php' );
$tokens = token_get_all( $code );
$open = 0;
$close = 0;
foreach ( $tokens as $tok ) {
	if ( is_array( $tok ) ) {
		if ( in_array( $tok[0], [ T_STRING, T_VARIABLE, T_LNUMBER, T_DNUMBER, T_CONSTANT_ENCAPSED_STRING, T_INLINE_HTML ], true ) ) {
			continue;
		}
		$txt = $tok[1];
	} else {
		$txt = $tok;
	}
	$open  += substr_count( $txt, '{' );
	$close += substr_count( $txt, '}' );
}
echo "Open: $open Close: $close Diff: " . ( $open - $close ) . "\n";
