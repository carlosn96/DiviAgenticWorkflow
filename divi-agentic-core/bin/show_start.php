<?php
$lines = file( 'DAW_bundle/divi-agentic-core/inc/core/class-layout-engine.php' );
for ( $i = 116; $i <= 140; $i++ ) {
	echo ( $i + 1 ) . ': ' . $lines[ $i ];
}
