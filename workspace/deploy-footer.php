<?php
$schema_path = 'DAW_bundle/site/lopezvelarde/page-defs/footer-combined.json';
$ds_path = 'DAW_bundle/site/lopezvelarde/design-system/divitheme.json';

if (!file_exists($schema_path)) {
    WP_CLI::error("Schema not found: $schema_path");
}

$raw = file_get_contents($schema_path);

// Resolve design tokens
if (file_exists($ds_path)) {
    require_once DIVI_AGENTIC_CORE_DIR . '/inc/core/class-design-resolver.php';
    $resolver = new \DAC\Core\Design_Resolver($ds_path);
    $raw = $resolver->resolve_schema_string($raw);
    WP_CLI::log('Design tokens resolved');
}

// Compile via Layout Engine
require_once DIVI_AGENTIC_CORE_DIR . '/inc/core/class-layout-engine.php';
$engine = new \DAC\Core\Layout_Engine();
$blocks = $engine->compile($raw);
WP_CLI::log('Blocks compiled: ' . strlen($blocks) . ' chars');

// Create or update et_footer_layout
$existing = get_posts([
    'post_type' => 'et_footer_layout',
    'posts_per_page' => 1,
    'post_status' => 'publish',
    'orderby' => 'ID',
    'order' => 'ASC'
]);

$post_data = [
    'post_title' => 'Global Footer',
    'post_content' => wp_slash($blocks),
    'post_status' => 'publish',
    'post_type' => 'et_footer_layout',
    'post_author' => 1,
];

if (!empty($existing)) {
    $post_data['ID'] = $existing[0]->ID;
    $post_id = wp_update_post($post_data);
    WP_CLI::log("Updated et_footer_layout ID: $post_id");
} else {
    $post_id = wp_insert_post($post_data);
    WP_CLI::log("Created et_footer_layout ID: $post_id");
}

// Divi meta flags
update_post_meta($post_id, '_et_pb_use_builder', 'on');
update_post_meta($post_id, '_et_pb_use_divi_5', 'on');
update_post_meta($post_id, '_et_pb_show_page_creation', 'off');
update_post_meta($post_id, '_et_pb_built_with_d5', '1');
update_post_meta($post_id, '_et_builder_version', '5.7.4');

WP_CLI::success("Footer deployed as et_footer_layout ID: $post_id");

// Verify
$check = get_post($post_id);
echo "Content: " . strlen($check->post_content) . " chars\n";
echo "Has 'color': " . (strpos($check->post_content, '"color"') !== false ? 'yes' : 'no') . "\n";
echo "Has '$variable': " . (strpos($check->post_content, '$variable') !== false ? 'YES' : 'no') . "\n";
