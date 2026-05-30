<?php
// Bootstrap WordPress
define('WP_USE_THEMES', false);
require_once __DIR__ . '/../../../app/public/wp-load.php';

error_reporting(E_ALL);
ini_set('display_errors', 1);

use ET\Builder\Packages\Module\Layout\Components\ModuleElements\ModuleElements;

$post = get_post(339319);
$parser = new \WP_Block_Parser();
$blocks = $parser->parse($post->post_content);

function find_buttons($blocks) {
    $found = [];
    foreach ($blocks as $block) {
        if ($block['blockName'] === 'divi/button') {
            $found[] = $block;
        }
        if (!empty($block['innerBlocks'])) {
            $found = array_merge($found, find_buttons($block['innerBlocks']));
        }
    }
    return $found;
}

$buttons = find_buttons($blocks);
$b = $buttons[1]; // The failing one ("Leer artículo")

// Let's restructure the attributes to put decoration keys flat under button.decoration!
$flat_attrs = $b['attrs'];
if (isset($flat_attrs['button']['decoration']['button']['decoration'])) {
    $nested = $flat_attrs['button']['decoration']['button']['decoration'];
    unset($flat_attrs['button']['decoration']['button']['decoration']);
    foreach ($nested as $k => $v) {
        $flat_attrs['button']['decoration'][$k] = $v;
    }
}

// Let's restructure hover to be under desktop breakpoint!
// For background:
if (isset($flat_attrs['button']['decoration']['background']['hover']['value']['color'])) {
    $hover_color = $flat_attrs['button']['decoration']['background']['hover']['value']['color'];
    unset($flat_attrs['button']['decoration']['background']['hover']);
    $flat_attrs['button']['decoration']['background']['desktop']['hover']['color'] = $hover_color;
}
// For font:
if (isset($flat_attrs['button']['decoration']['font']['font']['hover']['value']['color'])) {
    $hover_color = $flat_attrs['button']['decoration']['font']['font']['hover']['value']['color'];
    unset($flat_attrs['button']['decoration']['font']['font']['hover']);
    $flat_attrs['button']['decoration']['font']['font']['desktop']['hover']['color'] = $hover_color;
}

$all_meta = include __DIR__ . '/../../divi-agentic-core/data/_all_modules_metadata.php';
$button_meta = $all_meta['button'] ?? $all_meta['divi/button'] ?? [];

$elements = new ModuleElements([
    'id' => $b['attrs']['id'] ?? 'test-button',
    'name' => 'divi/button',
    'moduleAttrs' => $flat_attrs,
    'moduleMetadata' => $button_meta,
]);
$elements->set_order_class('et_pb_button_test');
$elements->set_base_order_class('et_pb_button_test');
$elements->set_wrapper_order_class('et_pb_button_test_wrapper');

echo "=== Calling elements->style('button') with restructured hover ===\n";
$res = $elements->style([
    'attrName' => 'button',
    'styleProps' => [
        'attrs' => $flat_attrs['button']['decoration'] ?? [],
    ]
]);

print_r($res);
