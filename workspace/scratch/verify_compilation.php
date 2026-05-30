<?php
// Bootstrap WordPress
define('WP_USE_THEMES', false);
require_once __DIR__ . '/../../../app/public/wp-load.php';

error_reporting(E_ALL);
ini_set('display_errors', 1);

require_once __DIR__ . '/../../divi-agentic-core/inc/core/class-layout-engine.php';

use ET\Builder\FrontEnd\Module\Style;
use ET\Builder\Packages\Module\Layout\Components\ModuleElements\ModuleElements;

$def_path = __DIR__ . '/../../site/bibliotheca/page-defs/blog.json';
require_once __DIR__ . '/../../divi-agentic-core/inc/core/class-design-resolver.php';

$resolver = new \DAC\Core\Design_Resolver(__DIR__ . '/../../site/bibliotheca/design-system/divitheme.json');
$resolved_schema = json_decode($resolver->resolve_schema_string(file_get_contents($def_path)), true);

$engine = new \DAC\Core\Layout_Engine();
$compiled_html = $engine->compile($resolved_schema);

$parser = new \WP_Block_Parser();
$blocks = $parser->parse($compiled_html);

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
$all_meta = include __DIR__ . '/../../divi-agentic-core/data/_all_modules_metadata.php';
$button_meta = $all_meta['button'] ?? $all_meta['divi/button'] ?? [];

foreach ($buttons as $idx => $b) {
    echo "\n--- Button " . ($idx+1) . " ('" . ($b['attrs']['button']['innerContent']['desktop']['value']['text'] ?? '') . "') ---\n";
    
    // Run style generation
    $elements = new ModuleElements([
        'id' => $b['attrs']['id'] ?? 'test-button-' . $idx,
        'name' => 'divi/button',
        'moduleAttrs' => $b['attrs'],
        'moduleMetadata' => $button_meta,
    ]);
    $elements->set_order_class('et_pb_button_test_' . $idx);
    $elements->set_base_order_class('et_pb_button_test_' . $idx);
    $elements->set_wrapper_order_class('et_pb_button_test_' . $idx . '_wrapper');
    
    $args = [
        'id' => $b['attrs']['id'] ?? 'test-button-' . $idx,
        'name' => 'divi/button',
        'orderIndex' => 1,
        'storeInstance' => 1,
        'attrs' => $b['attrs'],
        'elements' => $elements,
        'styleGroup' => 'module',
        'isCustomPostType' => false,
        'orderClass' => 'et_pb_button_test_' . $idx,
        'baseOrderClass' => 'et_pb_button_test_' . $idx,
        'wrapperOrderClass' => 'et_pb_button_test_' . $idx . '_wrapper',
    ];
    
    Style::reset();
    \ET\Builder\Packages\ModuleLibrary\Button\ButtonModule::module_styles($args);
    
    echo "Generated CSS:\n";
    echo Style::render('default', 'module') . "\n";
}
