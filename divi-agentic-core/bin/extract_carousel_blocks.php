<?php
$c = file_get_contents('DAW_bundle/site/sanpablo/content_state/local/inicio.txt');
preg_match_all('/<!-- wp:dgpc\/product-carousel[^\n]*--\s*\n?/', $c, $m);
foreach ($m[0] as $i => $block) {
    echo "--- BLOCK " . ($i + 1) . " ---\n";
    echo substr($block, 0, 2000) . "\n\n";
}
