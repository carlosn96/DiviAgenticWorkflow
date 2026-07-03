<?php
$code = file_get_contents( 'DAW_bundle/divi-agentic-core/inc/core/class-layout-engine.php' );
$tokens = token_get_all( $code );
$balance = 0;
$max     = 0;
foreach ( $tokens as $tok ) {
	if ( is_array( $tok ) ) {
		$type = $tok[0];
		if ( $type === T_CURLY_OPEN || $type === T_DOLLAR_OPEN_CURLY_BRACES ) {
			$balance++;
			continue;
		}
		if ( in_array( $type, [ T_CONSTANT_ENCAPSED_STRING, T_INLINE_HTML, T_COMMENT, T_DOC_COMMENT ], true ) ) {
			continue;
		}
		$txt = $tok[1];
	} else {
		$txt = $tok;
	}
	for ( $i = 0; $i < strlen( $txt ); $i++ ) {
		if ( $txt[ $i ] === '{' ) {
			$balance++;
			if ( $balance > $max ) {
				$max = $balance;
			}
		} elseif ( $txt[ $i ] === '}' ) {
			$balance--;
		}
	}
}
echo "Final: $balance Max: $max\n";
