<?php
$files = glob( 'DAW_bundle/divi-agentic-core/inc/core/renderers/*.php' );
foreach ( $files as $f ) {
	echo basename( $f ) . "\n";
}
