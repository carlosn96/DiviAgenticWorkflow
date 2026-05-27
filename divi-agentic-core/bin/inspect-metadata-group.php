<?php
/**
 * Inspect a specific settings group within a module's attribute.
 * Shows the innerContent/a/b structure to understand serialization.
 */

$meta_file = __DIR__ . '/../data/_all_modules_metadata.php';
$meta = include $meta_file;

$key = $argv[1] ?? '';
$attr = $argv[2] ?? '';
$group = $argv[3] ?? 'innerContent';

if (!$key || !isset($meta[$key]) || !isset($meta[$key]['attributes'][$attr])) {
    echo "Usage: php inspect-metadata-group.php <module> <attribute> [group]\n";
    exit;
}

$def = $meta[$key]['attributes'][$attr];

if (!isset($def['settings'][$group])) {
    echo "Group '$group' not found in $key.$attr.\n";
    echo "Available groups: " . implode(', ', array_keys($def['settings'] ?? [])) . "\n";
    exit;
}

$data = $def['settings'][$group];
echo "=== $key.$attr.$group ===\n";
echo json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) . "\n";
