<?php
$d = 'app/public/wp-content/plugins/dg-product-carousel';
$it = new RecursiveIteratorIterator(new RecursiveDirectoryIterator($d));
foreach ($it as $f) {
    if ($f->isFile() && $f->getExtension() === 'php') {
        $c = file_get_contents($f->getPathname());
        if (strpos($c, 'array_keys') !== false) {
            echo $f->getPathname() . "\n";
        }
    }
}
