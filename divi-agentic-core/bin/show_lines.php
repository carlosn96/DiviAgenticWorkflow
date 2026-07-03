<?php
$lines = file( 'DAW_bundle/divi-agentic-core/inc/core/class-layout-engine.php' );
for ( $i = 998; $i <= 1015; $i++ ) {
	echo ( $i + 1 ) . ': ' . $lines[ $i ];
}
