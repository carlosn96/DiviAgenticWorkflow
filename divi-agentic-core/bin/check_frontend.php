<?php
$u = 'http://sanpablo-mx.local/semana-biblica-2026-pro/';
$h = @file_get_contents($u);
if ($h === false) { echo "FETCH FAIL\n"; exit(1); }
if (strpos($h, 'dgpc_product_carousel') !== false || strpos($h, 'swiper-container') !== false) {
    echo "Carousel HTML found\n";
} else {
    echo "Carousel HTML NOT found\n";
}
if (strpos($h, 'daw-about-products') !== false) {
    echo "CSS class found\n";
} else {
    echo "CSS class NOT found\n";
}
if (strpos($h, 'Error:') !== false || strpos($h, 'array_keys') !== false) {
    echo "Error string found on page\n";
} else {
    echo "No error string on page\n";
}
// Find first title
if (preg_match('/<title>(.+?)<\/title>/', $h, $m)) {
    echo "Title: " . trim($m[1]) . "\n";
}
// Save a snippet around carousel
$pos = strpos($h, 'daw-about-products');
if ($pos !== false) {
    echo "\n--- snippet ---\n";
    echo substr($h, max(0, $pos - 500), 1200);
}
