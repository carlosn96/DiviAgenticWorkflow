<?php
$code = file_get_contents( 'DAW_bundle/divi-agentic-core/inc/core/class-layout-engine.php' );
$tokens = token_get_all( $code );
$balance = 0;
$opens   = [];
$closes  = [];
foreach ( $tokens as $tok ) {
	if ( is_array( $tok ) ) {
		if ( in_array( $tok[0], [ T_CONSTANT_ENCAPSED_STRING, T_INLINE_HTML, T_STRING, T_VARIABLE, T_LNUMBER, T_DNUMBER ], true ) ) {
			continue;
		}
		$txt  = $tok[1];
		$line = $tok[2];
	} else {
		$txt  = $tok;
		$line = 0;
	}
	for ( $i = 0; $i < strlen( $txt ); $i++ ) {
		if ( $txt[ $i ] === '{' ) {
			$balance++;
			$opens[] = $line . ':' . substr( str_replace( "\n", ' ', $txt ), 0, 20 );
		} elseif ( $txt[ $i ] === '}' ) {
			$balance--;
			if ( empty( $opens ) ) {
				$closes[] = 'extra } at line ' . $line;
			} else {
				array_pop( $opens );
			}
		}
	}
}
echo 'Final balance: ' . $balance . "\n";
echo 'Last open lines: ' . implode( ', ', array_slice( $opens, -20 ) ) . "\n";
echo 'Extra closes: ' . implode( ', ', $closes ) . "\n";
