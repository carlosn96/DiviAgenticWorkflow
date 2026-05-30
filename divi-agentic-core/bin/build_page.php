<?php
/**
 * build_page.php — Unified Page Builder for Divi 5
 * ==================================================
 * SINGLE PHP entry point that replaces daw_builder.py + build_home*.py.
 * Reads a page definition JSON → builds resolved schema → writes & deploys.
 *
 * Usage:
 *   php build_page.php --def=home.json
 *   php build_page.php --def=site/bibliotheca/page-defs/mi-pagina.json --deploy
 *   php build_page.php --def=home.json --deploy --front
 *   php build_page.php --def=home.json --deploy --verify
 *   php build_page.php --def=home.json --deploy --verify --url="https://example.com/mi-pagina"
 *   php build_page.php --def=home.json --no-resolve --out=pages/raw.json
 *   php build_page.php --def=home.json --site-url="https://example.com"
 *
 * Site selection: set $env:DAW_SITE or use path directly (--def=site/<name>/page-defs/...).
 *
 * Page definition format (JSON):
 *   {
 *     "title": "Page Title",
 *     "slug": "page-slug",
 *     "sections": [
 *       {
 *         "presets": ["section:hero-dark"],
 *         "rows": [
 *           { "column_structure": "4_4",
 *             "modules": [
 *               { "type": "divi/text", "presets": ["text:display"] }
 *             ]
 *           },
 *           { "column_structure": "1_2,1_2",
 *             "columns": [
 *               { "type": "1_2", "modules": [...] },
 *               { "type": "1_2", "modules": [...] }
 *             ]
 *           }
 *         ]
 *       }
 *     ]
 *   }
 */

// ── Paths ──────────────────────────────────────────────────────────
$DIR_SEP = DIRECTORY_SEPARATOR;
define('DAW_ROOT', str_replace('/', $DIR_SEP, dirname(__DIR__, 2)));
define('SITE', getenv('DAW_SITE') ?: 'bibliotheca');
define('SITE_DIR', DAW_ROOT . $DIR_SEP . 'site' . $DIR_SEP . SITE);
define('MODULES_DIR', DAW_ROOT . $DIR_SEP . 'workspace' . $DIR_SEP . 'data' . $DIR_SEP . 'modules');
define('DESIGN_SYSTEM_PATH', SITE_DIR . $DIR_SEP . 'design-system' . $DIR_SEP . 'divitheme.json');
define('DEFS_DIR', SITE_DIR . $DIR_SEP . 'page-defs');
define('PAGES_DIR', SITE_DIR . $DIR_SEP . 'pages');
define('WP_BAT', DAW_ROOT . $DIR_SEP . 'wp.bat');
define('PHP_BAT', DAW_ROOT . $DIR_SEP . 'php.bat');

// ── Helpers ─────────────────────────────────────────────────────────

function load_module_schema(string $module_type): array {
    static $cache = [];
    if (isset($cache[$module_type])) {
        return $cache[$module_type];
    }
    $slug = str_replace('divi/', '', $module_type);
    $path = MODULES_DIR . "/{$slug}.json";
    if (!file_exists($path)) {
        fwrite(STDERR, "[WARN] Module schema not found: {$path}\n");
        fwrite(STDERR, "[HINT] Run: php " . dirname(__DIR__) . "/bin/generate-module-schema.php --all\n");
        $cache[$module_type] = ['block' => ['name' => $module_type, 'attrs' => []]];
        return $cache[$module_type];
    }
    $cache[$module_type] = json_decode(file_get_contents($path), true);
    return $cache[$module_type];
}

function load_design_system(?string $path = null): array {
    $path = $path ?? DESIGN_SYSTEM_PATH;
    if (!file_exists($path)) {
        fwrite(STDERR, "[WARN] Design system not found: {$path}\n");
        fwrite(STDERR, "[HINT] Run: python " . DAW_ROOT . "/workspace/build_design_system.py --minimal\n");
        return ['tokens' => [], 'presets' => []];
    }
    return json_decode(file_get_contents($path), true);
}

function resolve_tokens(string $str, array $tokens, string $site_url = ''): string {
    if ($site_url !== '' && strpos($str, '{{SITE_URL}}') !== false) {
        $str = str_replace('{{SITE_URL}}', $site_url, $str);
    }
    return preg_replace_callback(
        '/\{\{design:(\w+):([\w-]+)\}\}/',
        function ($m) use ($tokens) {
            $type = $m[1];
            $name = $m[2];
            if ($type === 'color') {
                return "var(--gcid-{$name})";
            }
            return $tokens[$type][$name] ?? $m[0];
        },
        $str
    );
}

function resolve_tokens_recursive($value, array $tokens, string $site_url = '') {
    if (is_string($value)) {
        $has_design = strpos($value, '{{design:') !== false;
        $has_url = $site_url !== '' && strpos($value, '{{SITE_URL}}') !== false;
        if ($has_design || $has_url) {
            return resolve_tokens($value, $tokens, $site_url);
        }
        return $value;
    }
    if (is_array($value)) {
        $result = [];
        foreach ($value as $k => $v) {
            $result[$k] = resolve_tokens_recursive($v, $tokens, $site_url);
        }
        return $result;
    }
    return $value;
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

function normalize_gradient_stops(array $stops): array {
    return array_map(function ($stop) {
        if (isset($stop['position']) && is_string($stop['position'])) {
            $stop['position'] = rtrim($stop['position'], '%');
        }
        return $stop;
    }, $stops);
}

function normalize_decoration_gradients($d) {
    if (is_array($d)) {
        if (isset($d['gradient']['stops'])) {
            $d['gradient']['stops'] = normalize_gradient_stops($d['gradient']['stops']);
        }
        foreach ($d as $k => $v) {
            $d[$k] = normalize_decoration_gradients($v);
        }
        return $d;
    }
    return $d;
}

function get_preset(array $design_system, string $category, string $name, string $site_url = ''): array {
    $raw = $design_system['presets'][$category][$name] ?? [];
    if (!$raw) {
        return [];
    }
    $tokens = $design_system['tokens'] ?? [];
    return resolve_tokens_recursive($raw, $tokens, $site_url);
}

function apply_presets(array $node, array $preset_list, array $design_system, string $site_url = ''): array {
    $result = $node;
    foreach ($preset_list as $ref) {
        $parts = explode(':', $ref, 2);
        if (count($parts) !== 2) {
            continue;
        }
        $preset = get_preset($design_system, $parts[0], $parts[1], $site_url);
        $result = deep_merge($result, $preset);
    }
    return $result;
}

// ── Builders ────────────────────────────────────────────────────────

function extract_motion_presets(array &$attrs): void {
    foreach (['animation', 'scroll', 'transform'] as $key) {
        if (isset($attrs[$key])) {
            $preset_ref = "{$key}:{$attrs[$key]}";
            unset($attrs[$key]);
            if (!in_array($preset_ref, $attrs['presets'] ?? [])) {
                $attrs['presets'][] = $preset_ref;
            }
        }
    }
}

function build_module(array $def, array $design_system, bool $resolved, string $site_url = ''): array {
    $module_type = $def['type'];

    // Transform divi/heading to divi/text for native compatibility with global typography presets and contrast guarantees
    if ($module_type === 'divi/heading') {
        $module_type = 'divi/text';
        // Auto-wrap content in proper header tag if it's plain text
        if (isset($def['content']) && is_string($def['content']) && !str_starts_with(trim($def['content']), '<h')) {
            $level = 'h2';
            foreach ($def['presets'] ?? [] as $preset_ref) {
                if (str_contains($preset_ref, 'display-xl') || str_contains($preset_ref, 'hero-title')) {
                    $level = 'h1';
                } elseif (str_contains($preset_ref, 'display-md') || str_contains($preset_ref, 'headline')) {
                    $level = 'h2';
                }
            }
            $def['content'] = "<{$level}>" . $def['content'] . "</{$level}>";
        }
    }

    unset($def['type']);

    $schema = load_module_schema($module_type);
    $presets = $def['presets'] ?? [];
    unset($def['presets']);

    // Recursively build children (for divi/group, etc.)
    $children = [];
    if (isset($def['children'])) {
        foreach ($def['children'] as $child_def) {
            $children[] = build_module($child_def, $design_system, $resolved, $site_url);
        }
        unset($def['children']);
    }

    extract_motion_presets($def);

    $schema_attrs = $schema['block']['attrs'] ?? [];

    // Prioritize Presets -> Overrides. Initialize result with schema base attributes.
    $result = $schema_attrs;

    if ($resolved && $presets) {
        $result = apply_presets($result, $presets, $design_system, $site_url);
    }

    // Merge local page overrides ($def) on top of the preset-applied structure
    $result = deep_merge($result, $def);
    $result['module'] = $module_type;
    if ($children) {
        $result['children'] = $children;
    }

    // For heading blocks, align headingLevel with the resolved level from presets or tag headers in content
    if ($module_type === 'divi/heading') {
        $detected_level = null;
        if (isset($result['headingFont'])) {
            foreach (['h1', 'h2', 'h3', 'h4', 'h5', 'h6'] as $level) {
                if (isset($result['headingFont'][$level])) {
                    $detected_level = $level;
                    break;
                }
            }
        }
        if (!$detected_level && isset($result['content']) && is_string($result['content'])) {
            if (preg_match('/<h([1-6])\b/i', $result['content'], $matches)) {
                $detected_level = 'h' . $matches[1];
            }
        }
        if ($detected_level) {
            $result['title']['decoration']['font']['font']['desktop']['value']['headingLevel'] = $detected_level;
        }
    }

    $tokens = $design_system['tokens'] ?? [];

    if ($resolved) {
        $result = resolve_tokens_recursive($result, $tokens, $site_url);
    }

    return $result;
}

function build_row(array $def, array $design_system, bool $resolved, string $site_url = ''): array {
    $presets = $def['presets'] ?? [];
    unset($def['presets']);

    $columns = [];

    // Explicit columns mode
    if (isset($def['columns'])) {
        foreach ($def['columns'] as $col_def) {
            $col_type = $col_def['type'];
            $col_modules = [];
            foreach ($col_def['modules'] ?? [] as $mod_def) {
                $col_modules[] = build_module($mod_def, $design_system, $resolved, $site_url);
            }
            $columns[] = [
                'type' => $col_type,
                'modules' => $col_modules,
            ];
        }
        unset($def['columns']);
    }

    // Flat modules mode (single column 4_4 implied)
    if (isset($def['modules'])) {
        $col_modules = [];
        foreach ($def['modules'] as $mod_def) {
            $col_modules[] = build_module($mod_def, $design_system, $resolved, $site_url);
        }
        $columns[] = [
            'type' => '4_4',
            'modules' => $col_modules,
        ];
        unset($def['modules']);
    }

    $col_structure = $def['column_structure'] ?? implode(',', array_column($columns, 'type'));
    unset($def['column_structure']);

    extract_motion_presets($def);

    if (isset($def['decoration'])) {
        $def['decoration'] = normalize_decoration_gradients($def['decoration']);
    }

    // Apply presets first, then local overrides
    $result = [];
    if ($resolved && $presets) {
        $result = apply_presets($result, $presets, $design_system, $site_url);
    }

    $result = deep_merge($result, $def);
    $result['column_structure'] = $col_structure;
    $result['columns'] = $columns;

    return $result;
}

function build_section(array $def, array $design_system, bool $resolved, string $site_url = ''): array {
    $presets = $def['presets'] ?? [];
    unset($def['presets']);

    $rows = [];
    if (isset($def['rows'])) {
        foreach ($def['rows'] as $row_def) {
            $rows[] = build_row($row_def, $design_system, $resolved, $site_url);
        }
        unset($def['rows']);
    }

    extract_motion_presets($def);

    if (isset($def['bg_gradient']['stops'])) {
        $def['bg_gradient']['stops'] = normalize_gradient_stops($def['bg_gradient']['stops']);
    }
    if (isset($def['decoration'])) {
        $def['decoration'] = normalize_decoration_gradients($def['decoration']);
    }

    // Apply presets first, then local overrides
    $result = [];
    if ($resolved && $presets) {
        $result = apply_presets($result, $presets, $design_system, $site_url);
    }

    $result = deep_merge($result, $def);
    $result['rows'] = $rows;

    return $result;
}

function build_page(array $page_def, array $design_system, bool $resolved, string $site_url = ''): array {
    $title = $page_def['title'] ?? 'Page';
    $sections = [];
    foreach ($page_def['sections'] ?? [] as $section_def) {
        $sections[] = build_section($section_def, $design_system, $resolved, $site_url);
    }
    $result = ['sections' => $sections];

    if ($resolved) {
        $result = resolve_tokens_recursive($result, $design_system['tokens'] ?? [], $site_url);
    }

    return $result;
}

function validate_page(array $schema): bool {
    $sections = $schema['sections'] ?? [];
    if (empty($sections)) {
        fwrite(STDERR, "[ERROR] Validation failed: page has no sections.\n");
        return false;
    }
    foreach ($sections as $s_idx => $section) {
        if (empty($section['rows'])) {
            fwrite(STDERR, "[ERROR] Section {$s_idx} has no rows.\n");
            return false;
        }
        foreach ($section['rows'] as $r_idx => $row) {
            $columns = $row['columns'] ?? [];
            if (empty($columns)) {
                fwrite(STDERR, "[ERROR] Section {$s_idx} row {$r_idx} has no columns.\n");
                return false;
            }
            foreach ($columns as $c_idx => $col) {
                foreach ($col['modules'] ?? [] as $m_idx => $mod) {
                    $type = $mod['module'] ?? '';
                    if (!str_starts_with($type, 'divi/')) {
                        fwrite(STDERR, "[ERROR] S{$s_idx} R{$r_idx} C{$c_idx} M{$m_idx}: invalid module type '{$type}'\n");
                        return false;
                    }
                }
            }
        }
    }
    echo "[OK] Structural validation passed.\n";
    return true;
}

// ── CLI ─────────────────────────────────────────────────────────────

$opts = getopt('', ['def::', 'out::', 'deploy', 'front', 'no-resolve', 'site-url::', 'verify', 'url::', 'help']);
$def_file = $opts['def'] ?? null;
$out_file = $opts['out'] ?? null;
$do_deploy = isset($opts['deploy']);
$as_front = isset($opts['front']);
$resolved = !isset($opts['no-resolve']);
$site_url = $opts['site-url'] ?? '';

if (isset($opts['help']) || !$def_file) {
    echo "Usage: php build_page.php --def=page-def.json [options]\n\n";
    echo "Options:\n";
    echo "  --def=<file>     Page definition JSON file (in site/<DAW_SITE>/page-defs/ or full path)\n";
    echo "  --out=<file>     Output path for resolved schema (default: pages/<slug>.json)\n";
    echo "  --deploy         After building, deploy via WP-CLI\n";
    echo "  --front          Set page as front page (only with --deploy)\n";
    echo "  --verify         Run post-deploy verification (only with --deploy)\n";
    echo "  --url=<url>      Page URL for visual verification (implies --verify)\n";
    echo "  --no-resolve     Skip preset expansion and token resolution (raw schema)\n";
    echo "  --site-url=<url> Base URL for {{SITE_URL}} replacement (auto-detected with --deploy)\n";
    echo "\n";
    echo "Examples:\n";
    echo "  php build_page.php --def=home.json\n";
    echo "  php build_page.php --def=home.json --deploy\n";
    echo "  php build_page.php --def=home.json --deploy --front\n";
    echo "  php build_page.php --def=home.json --deploy --verify\n";
    echo "  php build_page.php --def=home.json --deploy --verify --url=\"https://example.com/pagina\"\n";
    echo "  php build_page.php --def=home.json --site-url='https://midominio.com'\n";
    exit(isset($opts['help']) ? 0 : 1);
}

// Auto-detect SITE_URL from WordPress if deploying
if ($site_url === '' && $do_deploy) {
    $detect_cmd = '"' . WP_BAT . '" option get siteurl 2>NUL';
    $detected = trim(shell_exec($detect_cmd));
    if ($detected && !str_contains($detected, 'error')) {
        $site_url = rtrim($detected, '/');
        echo "[INFO] Auto-detected SITE_URL: {$site_url}\n";
    }
}

// Resolve definition file path
if (!file_exists($def_file)) {
    $alt = DEFS_DIR . '/' . $def_file;
    if (file_exists($alt)) {
        $def_file = $alt;
    } else {
        fwrite(STDERR, "[ERROR] Page definition not found: {$def_file}\n");
        fwrite(STDERR, "[HINT] Create it in: " . DEFS_DIR . "\n");
        exit(1);
    }
}

$page_def = json_decode(file_get_contents($def_file), true);
if (!$page_def) {
    fwrite(STDERR, "[ERROR] Invalid JSON in: {$def_file}\n");
    exit(1);
}

$design_system = load_design_system();

// Resolve output path
$slug = $page_def['slug'] ?? preg_replace('/\.json$/i', '', basename($def_file));
if (!$out_file && !$do_deploy) {
    $out_file = PAGES_DIR . DIRECTORY_SEPARATOR . "{$slug}.json";
}

// Normalize paths to use backslashes on Windows
if ($out_file) {
    $out_file = str_replace('/', DIRECTORY_SEPARATOR, $out_file);
}

$page_title = $page_def['title'] ?? $slug;
echo "[BUILD] Building page: {$page_title}\n";
echo "[BUILD] Resolved mode: " . ($resolved ? 'yes' : 'no') . "\n";

$schema = build_page($page_def, $design_system, $resolved, $site_url);

if (!validate_page($schema)) {
    exit(1);
}

// Write output
if ($out_file) {
    $out_dir = dirname($out_file);
    if (!is_dir($out_dir)) {
        mkdir($out_dir, 0777, true);
    }
    file_put_contents(
        $out_file,
        json_encode($schema, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES)
    );
    echo "[OK] Schema written to: {$out_file}\n";
}

// Deploy
if ($do_deploy) {
    if (!$out_file) {
        $out_file = sys_get_temp_dir() . DIRECTORY_SEPARATOR . "daw_{$slug}.json";
        file_put_contents(
            $out_file,
            json_encode($schema, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES)
        );
    }

    $ds_path = DESIGN_SYSTEM_PATH;
    $cmd = '"' . WP_BAT . '" agentic deploy_page';
    $cmd .= ' --title="' . $page_title . '"';
    $cmd .= ' --slug="' . $slug . '"';
    $cmd .= ' --schema="' . $out_file . '"';
    $cmd .= ' --design-system="' . $ds_path . '"';
    if ($as_front) {
        $cmd .= ' --front';
    }

    echo "[DEPLOY] Running: {$cmd}\n";
    passthru($cmd . ' 2>NUL', $exit_code);
    if ($exit_code !== 0) {
        fwrite(STDERR, "[ERROR] Deploy failed with code {$exit_code}\n");
        exit($exit_code);
    }
    echo "[OK] Page deployed successfully.\n";

    // Post-deploy verification
    $do_verify = isset($opts['verify']) || isset($opts['url']);
    if ($do_verify) {
        echo "\n";
        $verify_script = dirname(__FILE__) . DIRECTORY_SEPARATOR . 'verify_page.php';
        $verify_cmd = '"' . PHP_BAT . '" "' . $verify_script . '" --slug="' . $slug . '"';
        if (!empty($opts['url'])) {
            $verify_cmd .= ' --url="' . $opts['url'] . '"';
        }
        echo "[VERIFY] Running post-deploy checks...\n";
        passthru($verify_cmd . ' 2>NUL', $verify_code);
        if ($verify_code !== 0) {
            fwrite(STDERR, "[WARN] Verification checks failed for page '{$slug}'\n");
            fwrite(STDERR, "[WARN] Page was deployed but may have issues. Review the check output above.\n");
        }
    }
}
