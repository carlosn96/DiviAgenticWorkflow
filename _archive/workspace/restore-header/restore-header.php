<?php
$post_id = 95;
$raw = file_get_contents(__DIR__ . '/header-raw.txt');

// Bypass ALL WordPress filters by writing directly to DB using raw query
global $wpdb;

// Build query manually without prepare to avoid content mangling
$table = $wpdb->posts;
$content_escaped = str_replace("'", "''", $raw);
$sql = "UPDATE {$table} SET post_content = '{$content_escaped}' WHERE ID = {$post_id}";

$result = $wpdb->query($sql);

if ($result === false) {
    WP_CLI::error('DB error: ' . $wpdb->last_error);
} else {
    WP_CLI::success("Header restored (rows affected: $result)");
}

clean_post_cache($post_id);
update_post_meta($post_id, '_et_pb_use_builder', 'on');
update_post_meta($post_id, '_et_pb_use_divi_5', 'on');
update_post_meta($post_id, '_et_pb_built_with_d5', '1');
update_post_meta($post_id, '_et_builder_version', defined('DIVI_BUILDER_VERSION') ? DIVI_BUILDER_VERSION : '5.7.4');
WP_CLI::success('Meta restored');
