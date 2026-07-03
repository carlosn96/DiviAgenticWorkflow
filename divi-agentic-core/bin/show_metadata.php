<?php
$lines = file( 'DAW_bundle/divi-agentic-core/inc/core/class-layout-engine.php' );
for ( $i = 948; $i <= 965; $i++ ) {
	echo ( $i + 1 ) . ': ' . $lines[ $i ];
}
