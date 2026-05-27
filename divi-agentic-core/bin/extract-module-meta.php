<?php
/**
 * Utility: Extract module schema from Divi 5 official metadata.
 *
 * Usage: php divi-agentic-core/bin/extract-module-meta.php <module-key>
 * Example: php divi-agentic-core/bin/extract-module-meta.php number-counter
 */

$meta_file = __DIR__ . '/../data/_all_modules_metadata.php';
$render_file = __DIR__ . '/../data/_all_modules_default_render_attributes.php';

if (!file_exists($meta_file)) {
    die("Metadata file not found: $meta_file\n");
}

$meta = include $meta_file;
$render = file_exists($render_file) ? include $render_file : [];

$key = $argv[1] ?? '';
if (!$key) {
    echo "Available modules:\n";
    foreach (array_keys($meta) as $m) {
        echo "  $m\n";
    }
    exit;
}

if (!isset($meta[$key])) {
    // Try to find by name
    $found = null;
    foreach ($meta as $k => $m) {
        if ($m['name'] === $key || $k === $key) {
            $found = $k;
            break;
        }
    }
    if (!$found) {
        die("Module not found: $key\n");
    }
    $key = $found;
}

$mod = $meta[$key];
echo "=== MODULE: {$mod['name']} ===\n";
echo "Key: $key\n";
echo "Title: {$mod['title']}\n";
echo "Category: {$mod['category']}\n";
echo "Child: " . ($mod['childModuleName'] ?? 'none') . "\n";
echo "Children: " . json_encode($mod['childrenName'] ?? []) . "\n";
echo "D4 Shortcode: " . ($mod['d4Shortcode'] ?? 'none') . "\n";
echo "\n--- ATTRIBUTES ---\n";

foreach ($mod['attributes'] as $attr => $def) {
    $type = $def['type'] ?? '?';
    $default = $def['default'] ?? null;
    
    if (is_array($default)) {
        $default_str = json_encode($default);
    } elseif (is_bool($default)) {
        $default_str = $default ? 'true' : 'false';
    } elseif (is_null($default)) {
        $default_str = 'null';
    } else {
        $default_str = (string)$default;
    }
    
    if (strlen($default_str) > 120) {
        $default_str = substr($default_str, 0, 120) . '...';
    }
    
    echo "$attr\n";
    echo "  Type: $type\n";
    echo "  Default: $default_str\n";
    
    // Show render path if available
    if (isset($render[$key][$attr])) {
        $path = $render[$key][$attr];
        echo "  Render path: " . json_encode($path) . "\n";
    }
    echo "\n";
}

echo "--- FULL ATTRIBUTES JSON ---\n";
echo json_encode($mod['attributes'], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE) . "\n";
