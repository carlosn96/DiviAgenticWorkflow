<?php
$meta = include __DIR__ . '/../../divi-agentic-core/data/_all_modules_metadata.php';
$render = include __DIR__ . '/../../divi-agentic-core/data/_all_modules_default_render_attributes.php';

foreach ($meta as $k => $m) {
    if ($m['name'] === 'divi/button' || $k === 'divi/button') {
        file_put_contents(__DIR__ . '/button_meta.json', json_encode($m, JSON_PRETTY_PRINT));
        file_put_contents(__DIR__ . '/button_render.json', json_encode($render[$k] ?? [], JSON_PRETTY_PRINT));
        echo "Dumped to json files successfully.\n";
    }
}
