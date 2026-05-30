<?php
/**
 * compose_page.php — High-Level Page Composer
 *
 * Converts a simple .page.json (section templates + content slots)
 * into a complete page-defs/<slug>.json ready for build_page.php.
 *
 * Usage:
 *   php compose_page.php --page=home.page.json
 *   php compose_page.php --page=path/to/page.json --out=custom/path.json
 *
 * Pipeline:
 *   .page.json → compose_page.php → page-defs/<slug>.json
 *     → build_page.php --deploy → WordPress
 *
 * Does NOT:
 *   - Load module schemas (that's build_page.php's job)
 *   - Resolve {{design:*}} tokens (build_page.php + Design_Resolver)
 *   - Expand presets (build_page.php applies presets)
 *   - Deploy (build_page.php + wp-cli)
 *
 * Does:
 *   - Load section templates from workspace/sections/
 *   - Fill {{slot:name}} placeholders with content
 *   - Handle _repeat blocks for repeating items
 *   - Auto-compute column_structure from item count
 *   - Assemble sections into a complete page-def
 *   - Write page-defs/<slug>.json
 */

require_once __DIR__ . '/env_loader.php';
define('DAW_ROOT', str_replace('/', DIRECTORY_SEPARATOR, dirname(__DIR__, 2)));
define('DAW_SITE', getenv('DAW_SITE') ?: 'bibliotheca');
define('SECTIONS_DIR', DAW_ROOT . DIRECTORY_SEPARATOR . 'workspace' . DIRECTORY_SEPARATOR . 'sections');
define('DEFS_DIR', DAW_ROOT . DIRECTORY_SEPARATOR . 'site' . DIRECTORY_SEPARATOR . DAW_SITE . DIRECTORY_SEPARATOR . 'page-defs');
define('COMPOSITIONS_DIR', DAW_ROOT . DIRECTORY_SEPARATOR . 'site' . DIRECTORY_SEPARATOR . DAW_SITE . DIRECTORY_SEPARATOR . 'compositions');

$TYPE_TO_STRUCTURE = [
    '4_4' => '4_4', '1_2' => '1_2', '1_3' => '1_3',
    '1_4' => '1_4', '1_5' => '1_5', '2_3' => '2_3', '3_4' => '3_4',
];

$UNRESOLVED_SLOTS = [];

function deep_merge(array $base, array $override): array {
    $result = $base;
    foreach ($override as $key => $value) {
        if (is_array($value) && isset($result[$key]) && is_array($result[$key])) {
            // Check if this is an indexed array (should replace, not merge)
            if (array_keys($value) !== range(0, count($value) - 1)) {
                $result[$key] = deep_merge($result[$key], $value);
            } else {
                $result[$key] = $value;
            }
        } else {
            $result[$key] = $value;
        }
    }
    return $result;
}

function load_template(string $name): array {
    // Support template@variant syntax
    $variant = null;
    if (str_contains($name, '@')) {
        $parts = explode('@', $name, 2);
        $name = $parts[0];
        $variant = $parts[1];
    }

    // Try directory-based structure first (sections/{name}/_base.section.json)
    $dir_path = SECTIONS_DIR . DIRECTORY_SEPARATOR . $name;
    $flat_path = SECTIONS_DIR . DIRECTORY_SEPARATOR . $name . '.section.json';
    $base_path = $dir_path . DIRECTORY_SEPARATOR . '_base.section.json';

    if (is_dir($dir_path) && file_exists($base_path)) {
        $data = json_decode(file_get_contents($base_path), true);
        if (!$data) { fwrite(STDERR, "[ERROR] Invalid JSON in: {$base_path}\n"); exit(1); }

        if ($variant) {
            $variant_path = $dir_path . DIRECTORY_SEPARATOR . $variant . '.variant.json';
            if (!file_exists($variant_path)) {
                fwrite(STDERR, "[ERROR] Variant not found: {$name}@{$variant}\n");
                fwrite(STDERR, "[HINT] Available variants: " . implode(', ', glob($dir_path . DIRECTORY_SEPARATOR . '*.variant.json')) . "\n"); exit(1);
            }
            $variant_data = json_decode(file_get_contents($variant_path), true);
            if (!$variant_data) { fwrite(STDERR, "[ERROR] Invalid JSON in variant: {$variant_path}\n"); exit(1); }
            $data = deep_merge($data, $variant_data);
            fwrite(STDERR, "[COMPOSE]  variant: {$name}@{$variant}\n");
        }

        return $data;
    }

    // Fallback to flat file
    if (file_exists($flat_path)) {
        $data = json_decode(file_get_contents($flat_path), true);
        if (!$data) { fwrite(STDERR, "[ERROR] Invalid JSON in: {$flat_path}\n"); exit(1); }
        return $data;
    }

    if (file_exists($name)) {
        $data = json_decode(file_get_contents($name), true);
        if (!$data) { fwrite(STDERR, "[ERROR] Invalid JSON in: {$name}\n"); exit(1); }
        return $data;
    }

    fwrite(STDERR, "[ERROR] Section template not found: {$name}\n");
    fwrite(STDERR, "[HINT] Create in: " . SECTIONS_DIR . "\n"); exit(1);
}

function get_nested_value(array $array, string $key) {
    $normalized = str_replace(['[', ']'], ['.', ''], $key);
    $parts = explode('.', $normalized);
    $current = $array;
    foreach ($parts as $part) {
        if ($part === '') continue;
        if (is_array($current) && isset($current[$part])) {
            $current = $current[$part];
        } else {
            return null;
        }
    }
    return $current;
}

function fill_slots($value, array $slots, string $context = '') {
    global $UNRESOLVED_SLOTS;
    if (is_string($value)) {
        return preg_replace_callback('/\{\{slot:([^\}]+)\}\}/', function ($m) use ($slots, $context) {
            global $UNRESOLVED_SLOTS;
            $key = $m[1];
            $val = get_nested_value($slots, $key);
            if ($val !== null && (is_string($val) || is_numeric($val))) {
                return (string) $val;
            }
            if ($val !== null) { return $val; }
            $UNRESOLVED_SLOTS[] = "{$context}:{{slot:{$key}}}";
            fwrite(STDERR, "[COMPOSE]  WARNING: Unresolved slot '{$key}' in {$context}\n");
            return '';
        }, $value);
    }
    if (is_array($value)) {
        if (isset($value['_repeat'])) { return process_repeat($value, $slots); }
        $result = [];
        foreach ($value as $k => $v) { $result[$k] = fill_slots($v, $slots, $context); }
        return $result;
    }
    return $value;
}

function process_repeat(array $node, array $slots, string $context = ''): array {
    global $TYPE_TO_STRUCTURE;
    $repeat = $node['_repeat'];
    $source_key = $repeat['source'];
    $target_key = $repeat['target'] ?? 'columns';
    $column_type = $repeat['column_type'] ?? '1_4';
    $module_type = $repeat['module_type'] ?? null;
    unset($node['_repeat']);

    $raw_items = $slots[$source_key] ?? [];
    if (!is_array($raw_items) || empty($raw_items)) {
        fwrite(STDERR, "[WARN] _repeat source '{$source_key}' empty\n");
        $node[$target_key] = []; return fill_slots($node, $slots, $context);
    }

    if ($target_key === 'children') {
        $children = [];
        $template = isset($node['modules'][0]) ? $node['modules'][0] : [];
        foreach ($raw_items as $item) {
            $item_data = is_array($item) ? $item : ['_value' => $item];
            $item_slots = array_merge($slots, $item_data);
            $child = ['type' => $module_type ?? 'divi/icon-list-item'];
            $child = array_merge($child, fill_slots($template, $item_slots, $context));
            $children[] = $child;
        }
        $node[$target_key] = $children;
        unset($node['modules']);
        return fill_slots($node, $slots, $context);
    }

    $count = count($raw_items);
    // Dynamic column structure calculation based on item count to avoid invalid Divi layouts (e.g. "1_3,1_3")
    if (in_array($column_type, ['1_2', '1_3', '1_4'])) {
        if ($count === 1) {
            $column_type = '4_4';
        } elseif ($count === 2) {
            $column_type = '1_2';
        } elseif ($count === 3) {
            $column_type = '1_3';
        } elseif ($count >= 4) {
            $column_type = '1_4';
        }
    }

    $type_part = $TYPE_TO_STRUCTURE[$column_type] ?? '1_4';
    // Limit columns array fill to max 6 columns (Divi limit)
    $node['column_structure'] = implode(',', array_fill(0, min($count, 6), $type_part));

    $columns = [];
    $item_index = 0;
    foreach ($raw_items as $item) {
        if ($item_index >= 6) break; // Divi supports up to 6 columns
        $item_data = is_array($item) ? $item : ['_value' => $item];
        $item_slots = array_merge($slots, $item_data);
        $col = ['type' => $column_type, 'modules' => []];
        if (isset($node['modules'])) {
            $col['modules'] = fill_slots($node['modules'], $item_slots, $context);
        }
        $columns[] = $col;
        $item_index++;
    }
    $node[$target_key] = $columns;
    unset($node['modules']);

    return fill_slots($node, $slots, $context);
}

// ─── CLI ────────────────────────────────────────────
$opts = getopt('', ['page::', 'out::', 'help']);
$page_file = $opts['page'] ?? null;

if (isset($opts['help']) || !$page_file) {
    echo "Usage: php compose_page.php --page=page.json [--out=output.json]\n\n";
    echo "  --page=<file>  High-level page composition (.page.json)\n";
    echo "  --out=<file>   Output path (default: site/<DAW_SITE>/page-defs/<slug>.json)\n";
    exit(isset($opts['help']) ? 0 : 1);
}

if (!file_exists($page_file)) {
    $alt = COMPOSITIONS_DIR . DIRECTORY_SEPARATOR . $page_file;
    if (file_exists($alt)) { $page_file = $alt; }
    else {
        $alt2 = COMPOSITIONS_DIR . DIRECTORY_SEPARATOR . $page_file . '.page.json';
        if (file_exists($alt2)) { $page_file = $alt2; }
        else {
            fwrite(STDERR, "[ERROR] Page composition not found\n[HINT] Create in: " . COMPOSITIONS_DIR . "\n");
            exit(1);
        }
    }
}

$composition = json_decode(file_get_contents($page_file), true);
if (!$composition) { fwrite(STDERR, "[ERROR] Invalid JSON\n"); exit(1); }

$title = $composition['title'] ?? 'Page';
$slug = $composition['slug'] ?? preg_replace('/\.page\.json$/i', '', basename($page_file));
echo "[COMPOSE] Page: {$title}\n";

$sections = [];
foreach ($composition['sections'] ?? [] as $i => $section_def) {
    $template_name = $section_def['template'] ?? '';
    if (!$template_name) { fwrite(STDERR, "[ERROR] Section {$i}: missing 'template'\n"); exit(1); }
    echo "[COMPOSE]  section {$i}: {$template_name}\n";
    $template = load_template($template_name);
    $slots = $section_def['slots'] ?? [];
    $sections[] = fill_slots($template, $slots, "section-{$i}:{$template_name}");
}

$page_def = [
    'title' => $title,
    'slug'  => $slug,
    'description' => $composition['description'] ?? '',
    'sections' => $sections,
];

$unresolved_count = count($UNRESOLVED_SLOTS);
if ($unresolved_count > 0) {
    fwrite(STDERR, "[COMPOSE] WARNING: {$unresolved_count} unresolved slot(s) — page may have missing content\n");
}

$out_file = $opts['out'] ?? DEFS_DIR . DIRECTORY_SEPARATOR . "{$slug}.json";
$out_dir = dirname($out_file);
if (!is_dir($out_dir)) { mkdir($out_dir, 0777, true); }

file_put_contents($out_file, json_encode($page_def, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES));
echo "[COMPOSE] Written to: {$out_file}\n";
echo "[COMPOSE] Next: php build_page.php --def={$slug}.json --deploy\n";
