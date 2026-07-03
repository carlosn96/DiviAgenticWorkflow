<?php
$code = file_get_contents( 'DAW_bundle/divi-agentic-core/inc/core/class-layout-engine.php' );
$tokens = token_get_all( $code );
$balance = 0;
$open_lines = [];
foreach ( $tokens as $tok ) {
	if ( is_array( $tok ) ) {
		$type = $tok[0];
		if ( $type === T_CURLY_OPEN || $type === T_DOLLAR_OPEN_CURLY_BRACES ) {
			$balance++;
			$open_lines[] = $tok[2];
			continue;
		}
		if ( in_array( $type, [ T_CONSTANT_ENCAPSED_STRING, T_INLINE_HTML, T_COMMENT, T_DOC_COMMENT, T_STRING, T_VARIABLE, T_LNUMBER, T_DNUMBER ], true ) ) {
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
			$open_lines[] = $line;
		} elseif ( $txt[ $i ] === '}' ) {
			$balance--;
			array_pop( $open_lines );
		}
	}
}
echo 'Balance: ' . $balance . "\n";
echo 'Last open lines: ' . implode( ', ', array_slice( $open_lines, -10 ) ) . "\n";
