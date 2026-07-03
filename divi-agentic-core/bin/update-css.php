<?php
$path = 'C:\Users\Departamento WEB\Local Sites\sanpablo\DAW_bundle\site\sanpablo\page-defs\semana-biblica-2026-pro-global.css';
$css = file_get_contents($path);
update_post_meta(139, '_et_pb_custom_css', $css);
echo 'CSS updated (' . strlen($css) . ' bytes)' . PHP_EOL;
