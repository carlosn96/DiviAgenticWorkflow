<?php
$u = 'http://sanpablo-mx.local/semana-biblica-2026-pro/';
$h = @file_get_contents($u);
if ($h === false) { echo "FETCH FAIL\n"; exit(1); }
$pos = strpos($h, 'array_keys');
if ($pos !== false) {
    echo "array_keys found at $pos\n";
    echo substr($h, max(0, $pos - 300), 600);
} else {
    echo "No array_keys found\n";
}
