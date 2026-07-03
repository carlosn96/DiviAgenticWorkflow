<?php
$src  = file_get_contents( 'DAW_bundle/divi-agentic-core/inc/core/class-layout-engine.php' );
$test = $src . "}\n";
file_put_contents( 'DAW_bundle/divi-agentic-core/inc/core/class-layout-engine-test.php', $test );
echo "Wrote test file\n";
