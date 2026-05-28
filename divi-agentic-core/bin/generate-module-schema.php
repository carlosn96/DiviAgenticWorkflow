<?php
/**
 * Generate authoritative Divi 5 module block schemas from official metadata.
 *
 * This is the SINGLE source of truth for module structure. Reads the actual
 * _all_modules_metadata.php (2.6MB) so schemas are 100% accurate to the
 * installed Divi version.
 *
 * build_page.php reads the JSON files this script produces — it does NOT
 * define module structure on its own.
 *
 * Usage:
 *   php generate-module-schema.php <module-key>         # print to stdout
 *   php generate-module-schema.php <module-key> --out path.json
 *   php generate-module-schema.php --all --out dir/     # generate all modules
 *   php generate-module-schema.php --list               # list available keys
 */

$meta_file = __DIR__ . '/../data/_all_modules_metadata.php';
$render_file = __DIR__ . '/../data/_all_modules_default_render_attributes.php';

if (!file_exists($meta_file)) {
    die("Metadata file not found: $meta_file\n");
}

$meta = include $meta_file;
$render = file_exists($render_file) ? include $render_file : [];

$args = array_slice($argv, 1);
$key = null;
$out_path = null;
$all = false;
$list = false;

foreach ($args as $i => $a) {
    if ($a === '--out' && isset($args[$i + 1])) {
        $out_path = $args[$i + 1];
    } elseif ($a === '--all') {
        $all = true;
    } elseif ($a === '--list') {
        $list = true;
    } elseif (!str_starts_with($a, '--') && !isset($prev_flag)) {
        $key = $a;
    }
}

if ($list) {
    foreach (array_keys($meta) as $m) {
        echo "  $m\n";
    }
    exit;
}

if ($all) {
    $dir = $out_path ?: __DIR__ . '/../../workspace/data/modules';
    if (!is_dir($dir)) {
        mkdir($dir, 0777, true);
    }
    $generated = 0;
    foreach ($meta as $k => $mod) {
        $module_name = $mod['name'] ?? $k;
        $slug = basename($module_name);
        $file = $dir . '/' . $slug . '.json';
        $schema = build_module_schema($k, $meta, $render);
        file_put_contents($file, json_encode($schema, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES));
        $generated++;
    }
    echo "[OK] Generated $generated module schemas in: $dir\n";
    exit;
}

if (!$key) {
    echo "Usage: php generate-module-schema.php <module-key> [--out path.json] [--all --out dir/] [--list]\n";
    exit;
}

// Resolve key
if (!isset($meta[$key])) {
    $found = null;
    foreach ($meta as $k => $m) {
        if (($m['name'] ?? '') === $key || $k === $key) {
            $found = $k;
            break;
        }
    }
    if (!$found) {
        die("Module not found: $key\n");
    }
    $key = $found;
}

$schema = build_module_schema($key, $meta, $render);

if ($out_path) {
    $dir = dirname($out_path);
    if (!is_dir($dir)) {
        mkdir($dir, 0777, true);
    }
    file_put_contents($out_path, json_encode($schema, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) . "\n");
    echo "[OK] Schema written: $out_path\n";
} else {
    echo json_encode($schema, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) . "\n";
    $total = count($meta[$key]['attributes'] ?? []);
    $with_render = count($render[$key] ?? []);
    echo "\n--- Module: {$meta[$key]['name']} | Attributes: $total | With render path: $with_render ---\n";
}

// ---- Builder ----
function build_module_schema(string $key, array $meta, array $render): array {
    $mod = $meta[$key];
    $module_name = $mod['name'] ?? $key;
    $attrs = $mod['attributes'] ?? [];
    $module_render = $render[$key] ?? [];
    $block_attrs = [];

    foreach ($attrs as $attr_name => $def) {
        $render_path = $module_render[$attr_name] ?? null;
        if ($render_path) {
            $block_attrs[$attr_name] = build_settings($render_path);
        } else {
            $type = $def['type'] ?? 'string';
            $default = $def['default'] ?? null;
            if ($default === null) {
                switch ($type) {
                    case 'object':  $default = new stdClass(); break;
                    case 'array':   $default = []; break;
                    case 'number':
                    case 'integer': $default = 0; break;
                    case 'boolean': $default = false; break;
                    default:        $default = ''; break;
                }
            }
            $block_attrs[$attr_name] = $default;
        }
    }

    return [
        'block' => [
            'name' => $module_name,
            'attrs' => $block_attrs,
        ],
    ];
}

function build_settings(array $render_path): array {
    $out = [];
    foreach ($render_path as $k => $v) {
        if (is_array($v)) {
            if (array_key_exists('value', $v)) {
                $out[$k] = ['value' => $v['value']];
            } else {
                $child = build_settings($v);
                if (!empty($child)) {
                    $out[$k] = $child;
                }
            }
        } else {
            $out[$k] = $v;
        }
    }
    return $out;
}
