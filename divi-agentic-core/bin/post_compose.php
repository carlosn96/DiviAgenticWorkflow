<?php
/**
 * post_compose.php — Premium Design Post-Composition
 *
 * Enhances a page-def after compose_page.php:
 *   1. Injects brand presets into sections/modules lacking decoration
 *   2. Replaces demo/catalog image URLs with brand-safe placeholders
 *   3. Applies sensible decoration defaults per section type
 *
 * Usage:
 *   php post_compose.php --def=slug.json
 *   php post_compose.php --def=path/to/page-def.json --out=output.json
 */

require_once __DIR__ . '/env_loader.php';
$DIR_SEP = DIRECTORY_SEPARATOR;
define('DAW_ROOT', str_replace('/', $DIR_SEP, dirname(__DIR__, 2)));
define('DAW_SITE', getenv('DAW_SITE') ?: 'bibliotheca');
define('DEFS_DIR', DAW_ROOT . $DIR_SEP . 'site' . $DIR_SEP . DAW_SITE . $DIR_SEP . 'page-defs');
define('DS_PATH', DAW_ROOT . $DIR_SEP . 'site' . $DIR_SEP . DAW_SITE . $DIR_SEP . 'design-system' . $DIR_SEP . 'divitheme.json');

// ─── Default presets per section type ──────────────────────
$SECTION_DEFAULTS = [
    'hero'              => ['section:hero-dark'],
    'hero-centered'     => ['section:hero-dark'],
    'features'          => ['section:light'],
    'stats'             => ['section:trust-bar'],
    'testimonials'      => ['section:light'],
    'cta'               => ['section:cta-epic'],
    'content'           => ['section:light'],
    'content-list'      => ['section:dark'],
    'logos'             => ['section:light'],
    'about'             => ['section:light'],
    'contact'           => ['section:white'],
    'team'              => ['section:light'],
    'gallery'           => ['section:white'],
    'blog'              => ['section:light'],
    'faq'               => ['section:white'],
    'timeline'          => ['section:light'],
];

$MODULE_DEFAULTS = [
    'divi/blurb'        => ['module:feature-card'],
    'divi/number-counter' => ['module:stat-item'],
    'divi/button'       => ['module:btn-primary'],
    'divi/image'        => ['module:image-shadow'],
];

$DEMO_URL_PATTERNS = [
    '/\/\/divi\.space\//i',
    '/\/\/placehold\.co\//i',
    '/\/\/picsum\.photos\//i',
    '/\/\/source\.unsplash\.com\//i',
    '/\/\/via\.placeholder\.com\//i',
    '/\/\/unsplash\.com\/photos\//i',
    '/\/\/images\.unsplash\.com\//i',
    '/\/\/diviplus\.io\//i',
    '/\/\/divilayoutsextended\.com\//i',
    '/\/\/elegantthemes\.com\//i',
    '/\/\/elegantblocks\.com\//i',
    '/\/\/divilayouts\.com\//i',
];

function load_json(string $path): ?array {
    if (!file_exists($path)) return null;
    $data = json_decode(file_get_contents($path), true);
    return $data ?: null;
}

function deep_merge(array $base, array $override): array {
    $result = $base;
    foreach ($override as $key => $val) {
        if (isset($result[$key]) && is_array($result[$key]) && is_array($val)) {
            $result[$key] = deep_merge($result[$key], $val);
        } else {
            $result[$key] = $val;
        }
    }
    return $result;
}

function detect_section_type(array $section): string {
    if (isset($section['_section_type'])) return $section['_section_type'];
    $rows = $section['rows'] ?? [];
    if (empty($rows)) return 'content';
    $modules = [];
    foreach ($rows as $row) {
        $columns = $row['columns'] ?? [];
        foreach ($columns as $col) {
            foreach ($col['modules'] ?? [] as $mod) {
                $modules[] = $mod['type'] ?? '';
            }
        }
    }
    $types = array_count_values($modules);
    $top = $types ? array_search(max($types), $types) : '';
    if (str_contains($top, 'number-counter')) return 'stats';
    if (str_contains($top, 'blurb') && ($types['divi/blurb'] ?? 0) >= 3) return 'features';
    if (str_contains($top, 'testimonial')) return 'testimonials';
    return 'content';
}

function has_decoration(array $node): bool {
    if (isset($node['decoration']) && !empty($node['decoration'])) return true;
    if (isset($node['presets']) && !empty($node['presets'])) return true;
    return false;
}

function inject_section_presets(array $section, string $section_type, array $design_system): array {
    global $SECTION_DEFAULTS;
    $defaults = $SECTION_DEFAULTS[$section_type] ?? $SECTION_DEFAULTS['content'];
    
    // Force-inject section presets on all sections from the catalog (their colors are wrong).
    // The section preset overrides background color, gradient, image, and spacing.
    // Merge with any existing presets to keep the section type identity.
    $existing_presets = $section['presets'] ?? [];
    
    // Only inject if section has no brand presets already
    $has_brand_preset = false;
    foreach ($existing_presets as $p) {
        if (str_starts_with($p, 'section:')) {
            $has_brand_preset = true;
            break;
        }
    }
    
    if (!$has_brand_preset) {
        $section['presets'] = array_unique(array_merge($defaults, $existing_presets));
        fwrite(STDERR, "[POSTC]  injected section presets: " . implode(', ', $defaults) . " ({$section_type})\n");
    }
    
    // Strip external background images from catalog templates
    if (isset($section['decoration']['background']['desktop']['value']['image']['url'])) {
        $url = $section['decoration']['background']['desktop']['value']['image']['url'];
        if (preg_match('/\/\/(?:diviplus|divilayoutsextended|elegantthemes|elegantblocks|divilayouts|divi\.space|unsplash|picsum|placehold)\./i', $url)) {
            unset($section['decoration']['background']['desktop']['value']['image']);
            fwrite(STDERR, "[POSTC]  stripped catalog background image\n");
        }
    }
    
    // Remove hardcoded gradients from catalog (section preset provides brand gradient)
    if (isset($section['decoration']['background']['desktop']['value']['gradient'])) {
        unset($section['decoration']['background']['desktop']['value']['gradient']);
    }
    
    return $section;
}

function inject_module_presets(array $module): array {
    global $MODULE_DEFAULTS;
    $type = $module['type'] ?? '';
    if (!has_decoration($module) && isset($MODULE_DEFAULTS[$type])) {
        $module['presets'] = $module['presets'] ?? $MODULE_DEFAULTS[$type];
        fwrite(STDERR, "[POSTC]  injected module presets: " . implode(', ', $MODULE_DEFAULTS[$type]) . " ({$type})\n");
    }
    return $module;
}

function strip_demo_images($value) {
    global $DEMO_URL_PATTERNS;
    if (is_string($value)) {
        $cleaned = $value;
        foreach ($DEMO_URL_PATTERNS as $pattern) {
            $cleaned = preg_replace($pattern, '//brand.placeholder/', $cleaned);
        }
        if ($cleaned !== $value) {
            fwrite(STDERR, "[POSTC]  replaced demo image URL\n");
        }
        return $cleaned;
    }
    if (is_array($value)) {
        $result = [];
        foreach ($value as $k => $v) {
            $result[$k] = strip_demo_images($v);
        }
        return $result;
    }
    return $value;
}

// ─── Process sections recursively ──────────────────────────
function strip_placeholder_modules(array &$modules): void {
    $modules = array_values(array_filter($modules, function($mod) {
        $type = $mod['type'] ?? '';
        if ($type === 'divi/placeholder') {
            fwrite(STDERR, "[POSTC]  stripped divi/placeholder module\n");
            return false;
        }
        return true;
    }));
}

function process_sections(array &$sections, array $design_system): void {
    foreach ($sections as &$section) {
        $section_type = detect_section_type($section);
        $section = inject_section_presets($section, $section_type, $design_system);
        foreach ($section['rows'] ?? [] as &$row) {
            foreach ($row['columns'] ?? [] as &$col) {
                strip_placeholder_modules($col['modules']);
                foreach ($col['modules'] ?? [] as &$mod) {
                    $mod = inject_module_presets($mod);
                }
            }
        }
    }
    unset($section, $row, $col, $mod);
}

// ─── CLI ───────────────────────────────────────────────────
$opts = getopt('', ['def::', 'out::', 'help']);
$def_file = $opts['def'] ?? null;

if (isset($opts['help']) || !$def_file) {
    echo "Usage: php post_compose.php --def=slug.json [--out=output.json]\n\n";
    echo "  --def=<file>  Page-def file (in page-defs/ or full path)\n";
    echo "  --out=<file>  Output path (default: overwrites input)\n";
    exit(isset($opts['help']) ? 0 : 1);
}

if (!file_exists($def_file)) {
    $alt = DEFS_DIR . $DIR_SEP . $def_file;
    if (!file_exists($alt)) {
        $alt = DEFS_DIR . $DIR_SEP . $def_file . '.json';
    }
    if (file_exists($alt)) { $def_file = $alt; }
}

if (!file_exists($def_file)) {
    fwrite(STDERR, "[ERROR] Page-def not found: {$def_file}\n");
    exit(1);
}

$page_def = json_decode(file_get_contents($def_file), true);
if (!$page_def) {
    fwrite(STDERR, "[ERROR] Invalid JSON in: {$def_file}\n");
    exit(1);
}

$design_system = load_json(DS_PATH);
if (!$design_system) {
    fwrite(STDERR, "[WARN] Design system not found at: " . DS_PATH . "\n");
    $design_system = ['presets' => []];
}

echo "[POSTC] Post-composing: {$page_def['title']}\n";

// Process
$page_def = strip_demo_images($page_def);
$sections = $page_def['sections'] ?? [];
process_sections($sections, $design_system);
$page_def['sections'] = $sections;

// Write
$out_file = $opts['out'] ?? $def_file;
file_put_contents(
    $out_file,
    json_encode($page_def, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES)
);
echo "[POSTC] Written to: {$out_file}\n";
