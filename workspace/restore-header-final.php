<?php
$post_id = 95;
$revision_id = 428;

// Get original revision content
$revision = get_post($revision_id);
if (!$revision) {
    WP_CLI::error("Revision $revision_id not found");
}

$original_content = $revision->post_content;
echo "Original content length: " . strlen($original_content) . "\n";
echo "First 100 chars: " . substr($original_content, 0, 100) . "\n";

// Verify it has proper JSON with quotes
if (strpos($original_content, '"module"') === false) {
    WP_CLI::warning("Content might be mangled - checking...");
}

// Write directly to DB - no filters, no slashes, just raw bytes
global $wpdb;
$table = $wpdb->posts;

// Use $wpdb->_real_escape for safety
$escaped = $wpdb->_real_escape($original_content);

$sql = "UPDATE {$table} SET post_content = '{$escaped}' WHERE ID = {$post_id}";

$result = $wpdb->query($sql);

if ($result === false) {
    WP_CLI::error('DB error: ' . $wpdb->last_error);
} else {
    WP_CLI::success("Header restored from revision (rows: $result)");
}

clean_post_cache($post_id);
wp_cache_flush();

// Verify
$check = get_post($post_id);
echo "After restore: " . strlen($check->post_content) . " chars\n";
echo "Has JSON quotes: " . (strpos($check->post_content, '"module"') !== false ? 'YES' : 'NO') . "\n";
