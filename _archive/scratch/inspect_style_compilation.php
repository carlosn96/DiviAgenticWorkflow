<?php
// Bootstrap WordPress
define('WP_USE_THEMES', false);
require_once __DIR__ . '/../../../app/public/wp-load.php';

// Enable error reporting
error_reporting(E_ALL);
ini_set('display_errors', 1);

// Set DAW_SITE if needed
if (!defined('DIVI_AGENTIC_CORE_DIR')) {
    define('DIVI_AGENTIC_CORE_DIR', __DIR__ . '/../divi-agentic-core');
}

use ET\Builder\FrontEnd\Module\Style;
use ET\Builder\Packages\Module\Layout\Components\ModuleElements\ModuleElements;

echo "=== BOOTSTRAPPED WORDPRESS ===\n";

// Get our button block attributes from the database or construct them
$post = get_post(339319);
if (!$post) {
    echo "Post 339319 not found!\n";
    exit;
}
$content = $post->post_content;

// Find wp:divi/button block
$parser = new \WP_Block_Parser();
$blocks = $parser->parse($content);

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
echo "Found " . count($buttons) . " button blocks in database content.\n";

$all_meta = include __DIR__ . '/../../divi-agentic-core/data/_all_modules_metadata.php';
$button_meta = $all_meta['button'] ?? $all_meta['divi/button'] ?? [];

foreach ($buttons as $idx => $b) {
    echo "\n--- Button " . ($idx+1) . " ('" . ($b['attrs']['button']['innerContent']['desktop']['value']['text'] ?? '') . "') ---\n";
    
    // We want to see the generated CSS styles!
    // Divi 5 registers style callbacks and runs them. Let's run the style rendering manually!
    $elements = new ModuleElements([
        'id' => $b['attrs']['id'] ?? 'test-button-' . $idx,
        'name' => 'divi/button',
        'moduleAttrs' => $b['attrs'],
        'moduleMetadata' => $button_meta,
    ]);
    $elements->id = $b['attrs']['id'] ?? 'test-button-' . $idx;
    
    $args = [
        'id' => $b['attrs']['id'] ?? 'test-button-' . $idx,
        'name' => 'divi/button',
        'orderIndex' => 1,
        'storeInstance' => 1,
        'attrs' => $b['attrs'],
        'elements' => $elements,
        'styleGroup' => 'module',
        'isCustomPostType' => false,
        'orderClass' => 'et_pb_button_test',
        'baseOrderClass' => 'et_pb_button_test',
        'wrapperOrderClass' => 'et_pb_button_test_wrapper',
    ];
    
    // Let's call ButtonModule::module_styles
    echo "\nCalling ButtonModule::module_styles...\n";
    Style::reset();
    \ET\Builder\Packages\ModuleLibrary\Button\ButtonModule::module_styles($args);
    
    // Let's see what style declarations were registered in Style
    echo "Registered Styles:\n";
    $styles_data = Style::get_style_array('module');
    print_r($styles_data);
    
    echo "\nRendered CSS:\n";
    echo Style::render('default', 'module') . "\n";
}
