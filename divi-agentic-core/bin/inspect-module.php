<?php
/**
 * Inspect a module's full attribute definition from official metadata.
 * Usage: php divi-agentic-core/bin/inspect-module.php <module-key> [attr-name]
 */

$meta_file = __DIR__ . '/../data/_all_modules_metadata.php';
$meta = include $meta_file;

$key = $argv[1] ?? '';
if (!$key || !isset($meta[$key])) {
    echo "Available keys:\n";
    $keys = array_keys($meta);
    sort($keys);
    foreach ($keys as $k) {
        echo "  $k\n";
    }
    exit;
}

$mod = $meta[$key];
$attr_filter = $argv[2] ?? null;

echo "=== {$mod['name']} ===\n";
echo "Key: $key\n";
echo "Category: {$mod['category']}\n";
echo "Child: " . ($mod['childModuleName'] ?? 'none') . "\n";

foreach ($mod['attributes'] as $attr => $def) {
    if ($attr_filter && $attr !== $attr_filter) continue;
    
    echo "\n--- $attr ---\n";
    echo "Type: {$def['type']}\n";
    if (isset($def['tagName'])) echo "Tag: {$def['tagName']}\n";
    if (isset($def['inlineEditor'])) echo "Editor: {$def['inlineEditor']}\n";
    if (isset($def['default'])) {
        $d = $def['default'];
        echo "Default: " . (is_string($d) ? $d : json_encode($d, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES)) . "\n";
    }
    
    // Show first-level keys of settings to understand structure
    if (isset($def['settings'])) {
        echo "Settings groups: " . implode(', ', array_keys($def['settings'])) . "\n";
        // Show first 2 levels of each setting group
        foreach ($def['settings'] as $group => $gdef) {
            if (is_array($gdef)) {
                $keys = array_keys($gdef);
                echo "  $group: " . implode(', ', array_slice($keys, 0, 5)) . (count($keys) > 5 ? '...' : '') . "\n";
            }
        }
    }
}
