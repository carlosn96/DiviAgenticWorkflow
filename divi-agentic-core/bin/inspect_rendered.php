<?php
$h = file_get_contents('DAW_bundle/site/sanpablo/content_state/local/rendered_127774.html');
$pos = strpos($h, 'array_keys');
if ($pos !== false) {
    echo substr($h, max(0, $pos - 1500), 2500);
} else {
    echo "not found";
}
