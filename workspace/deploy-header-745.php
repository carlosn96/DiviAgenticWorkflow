<?php
/**
 * Deploy header layout to et_header_layout post ID 745.
 * Basado en deploy-footer.php pero con target ID fijo.
 */

$schema_path = 'DAW_bundle/site/lopezvelarde/page-defs/header-745-combined.json';
$ds_path = 'DAW_bundle/site/lopezvelarde/design-system/divitheme.json';
$target_id = 745;

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

// Update specific et_header_layout by ID (745)
$post_data = [
    'ID' => $target_id,
    'post_title' => 'Header Principal - ID 745',
    'post_content' => wp_slash($blocks),
    'post_status' => 'publish',
    'post_type' => 'et_header_layout',
    'post_author' => 1,
];

$post_id = wp_update_post($post_data);

if (is_wp_error($post_id)) {
    WP_CLI::error('Failed to update header: ' . $post_id->get_error_message());
}

// Divi 5 meta flags
update_post_meta($post_id, '_et_pb_use_builder', 'on');
update_post_meta($post_id, '_et_pb_use_divi_5', 'on');
update_post_meta($post_id, '_et_pb_show_page_creation', 'off');
update_post_meta($post_id, '_et_pb_built_with_d5', '1');
update_post_meta($post_id, '_et_builder_version', '5.8.1');

WP_CLI::success("Header deployed as et_header_layout ID: $post_id");

// Verify
$check = get_post($post_id);
echo "Content: " . strlen($check->post_content) . " chars\n";
echo "Title: " . $check->post_title . "\n";
