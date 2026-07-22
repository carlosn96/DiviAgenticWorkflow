<?php
/**
 * brand-sync.php
 *
 * Sincroniza _design_vars.json → todo el ecosistema Divi:
 *   1. wp_options['et_divi'] (Customizer global)
 *   2. divitheme.json (tokens + presets file)
 *   3. Global Colors (gcids) via GlobalData::set_global_colors()
 *   4. Global Variables (gvids) via GlobalData::set_global_variables()
 *      (radios, espacios, fuentes como variables nativas Divi 5)
 *
 * Un solo comando, una sola fuente de verdad (_design_vars.json).
 *
 * Uso: wp eval-file bin/brand-sync.php [--vars=<path>]
 */

namespace DAC\Bin;

use WP_CLI;

defined('ABSPATH') || exit;

// ─── Helpers ────────────────────────────────────────────────────────────

function find_vars_file(): ?string {
    $env_vars = getenv('DAW_VARS');
    if ($env_vars && file_exists($env_vars)) return $env_vars;

    if (function_exists('daw_find_project_root') && function_exists('daw_get_active_site')) {
        $root = daw_find_project_root();
        $site = daw_get_active_site();
        if ($root && $site && defined('DIVI_AGENTIC_BUNDLE_NAME')) {
            $p = $root . '/' . DIVI_AGENTIC_BUNDLE_NAME . '/site/' . $site . '/brand/_design_vars.json';
            if (file_exists($p)) return $p;
        }
    }

    $bundle_dir = defined('DIVI_AGENTIC_BUNDLE_NAME')
        ? dirname(__DIR__, 2)
        : dirname(__DIR__, 3);
    $site_dir = dirname($bundle_dir) . '/site';
    if (is_dir($site_dir)) {
        $glob = glob($site_dir . '/*/brand/_design_vars.json');
        if (!empty($glob)) return $glob[0];
    }

    return null;
}

function resolve_paths(string $vars_path): array {
    $bundle_dir = '';
    if (function_exists('daw_find_project_root') && function_exists('daw_get_active_site') && defined('DIVI_AGENTIC_BUNDLE_NAME')) {
        $root = daw_find_project_root();
        $site = daw_get_active_site();
        if ($root && $site) {
            $bundle_dir = $root . '/' . DIVI_AGENTIC_BUNDLE_NAME;
        }
    }
    if (!$bundle_dir) {
        if (preg_match('#^(.*)/site/[^/]+/brand/_design_vars\.json$#', $vars_path, $m)) {
            $bundle_dir = $m[1];
        } else {
            $bundle_dir = dirname(dirname(__DIR__));
        }
    }

    preg_match('#/site/([^/]+)/brand/_design_vars\.json$#', $vars_path, $m);
    $site_name = $m[1] ?? '';

    return [
        'bundle'    => $bundle_dir,
        'site'      => $site_name,
        'divitheme' => $bundle_dir . '/site/' . $site_name . '/design-system/divitheme.json',
    ];
}

function load_json(string $path): ?array {
    if (!file_exists($path)) return null;
    $raw = file_get_contents($path);
    $data = json_decode($raw, true);
    if (json_last_error() !== JSON_ERROR_NONE) return null;
    return $data;
}

function color_ensure_hash(string $hex): string {
    $hex = trim($hex);
    if (str_starts_with($hex, '#')) return $hex;
    if (preg_match('/^[0-9A-Fa-f]{3,8}$/', $hex)) return "#{$hex}";
    return $hex;
}

function get_prefixed_values(array $vars, string $prefix): array {
    $result = [];
    foreach ($vars as $key => $value) {
        if (str_starts_with($key, $prefix)) {
            $name = substr($key, strlen($prefix));
            $name = str_replace('_', '-', $name);
            $result[$name] = $value;
        }
    }
    return $result;
}

// ─── Mapping: _design_vars.json → et_divi keys ─────────────────────────

const COLOR_KEYS = [
    'color_accent' => [
        'accent_color', 'link_color',
        'menu_link_active', 'fixed_menu_link_active',
        'primary_nav_dropdown_line_color',
        'secondary_nav_bg', 'secondary_nav_dropdown_bg',
        'fixed_secondary_nav_bg',
        'footer_widget_header_color', 'footer_widget_bullet_color',
        'footer_menu_active_link_color',
        'slide_nav_bg',
    ],
    'color_accent_hover' => [
        'all_buttons_bg_color_hover',
    ],
    'color_surface_deep' => [
        'primary_nav_bg', 'fixed_primary_nav_bg',
        'mobile_primary_nav_bg',
        'footer_bg', 'bottom_bar_background_color',
    ],
    'color_surface_mid' => [
        'primary_nav_dropdown_bg', 'secondary_nav_dropdown_bg',
    ],
    'color_text_on_dark' => [
        'menu_link', 'fixed_menu_link',
        'secondary_nav_text_color_new', 'secondary_nav_dropdown_link_color',
        'fixed_secondary_menu_link', 'mobile_menu_link',
        'primary_nav_dropdown_link_color',
        'footer_widget_text_color', 'footer_widget_link_color',
        'slide_nav_links_color', 'slide_nav_links_color_active',
    ],
    'color_text_primary' => [
        'font_color', 'header_color', 'bottom_bar_text_color',
    ],
    '_secondary_accent' => [
        'secondary_accent_color',
    ],
    'color_success' => [],
    'color_error' => [],
];

const FONT_KEYS = [
    'font_display'   => ['heading_font'],
    'font_body'      => ['body_font', 'primary_nav_font', 'secondary_nav_font', 'slide_nav_font', 'all_buttons_font'],
];

const FONT_VALUE_KEYS = [
    'font_body_size'   => 'body_font_size',
    'font_body_height' => 'body_font_height',
    'font_body_weight' => 'body_font_weight',
    'font_heading_weight' => 'heading_font_weight',
];

const CUSTOMIZER_SLOTS = [
    'primary'   => 'gcid-primary-color',
    'secondary' => 'gcid-secondary-color',
    'heading'   => 'gcid-heading-color',
    'body'      => 'gcid-body-color',
    'link'      => 'gcid-link-color',
];

// ─── 1. Sync to et_divi (Customizer) ───────────────────────────────────

function sync_et_divi(array $vars): array {
    $updated = [];

    // Colors — use et_update_option for each key to keep global cache in sync
    foreach (COLOR_KEYS as $var_key => $et_keys) {
        $source_key = str_starts_with($var_key, '_') ? substr($var_key, 1) : $var_key;
        $color_value = $vars[$source_key] ?? null;

        if (!$color_value && str_starts_with($var_key, '_')) {
            if ($var_key === '_secondary_accent') {
                $color_value = $vars['color_surface_mid'] ?? '#0A1E3D';
            }
        }
        if (!$color_value) continue;
        $color_value = color_ensure_hash($color_value);

        foreach ($et_keys as $et_key) {
            if (!empty($et_key) && et_get_option($et_key) !== $color_value) {
                et_update_option($et_key, $color_value);
                $updated[] = $et_key;
            }
        }
    }

    // Font families
    foreach (FONT_KEYS as $var_key => $et_keys) {
        $font_value = $vars[$var_key] ?? null;
        if (!$font_value) continue;
        $font_name = explode(',', $font_value)[0];
        $font_name = trim($font_name, "'\" ");

        foreach ($et_keys as $et_key) {
            if (et_get_option($et_key) !== $font_name) {
                et_update_option($et_key, $font_name);
                $updated[] = $et_key;
            }
        }
    }

    // Font values (size, height, weight)
    foreach (FONT_VALUE_KEYS as $var_key => $et_key) {
        $value = $vars[$var_key] ?? null;
        if ($value === null) continue;
        if ((string)et_get_option($et_key) !== (string)$value) {
            et_update_option($et_key, $value);
            $updated[] = $et_key;
        }
    }

    // Logo
    $logo_id = $vars['logo_id'] ?? null;
    if ($logo_id) {
        $logo_url = wp_get_attachment_url((int)$logo_id);
        if ($logo_url) {
            et_update_option('divi_logo', $logo_url);
            $updated[] = 'divi_logo';
        }
    }

    if (!empty($updated)) {
        WP_CLI::log(sprintf('et_divi: %d option(s) updated: %s', count($updated), implode(', ', $updated)));
    } else {
        WP_CLI::log('et_divi: no changes needed.');
    }

    return $updated;
}

// ─── 2. Build / update divitheme.json ──────────────────────────────────

function sync_divitheme(string $path, array $vars): void {
    $dir = dirname($path);
    if (!is_dir($dir)) {
        mkdir($dir, 0755, true);
    }

    $existing = load_json($path);

    $new = [
        'name'        => $vars['brand_name'] ?? ($existing['name'] ?? ''),
        'description' => $vars['brand_description'] ?? ($existing['description'] ?? ''),
        'strategy'    => $existing['strategy'] ?? 'custom',
        'presets'     => $existing['presets'] ?? new \stdClass(),
    ];

    file_put_contents($path, json_encode($new, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES));
    WP_CLI::log(sprintf(
        'divitheme.json: updated (presets preserved: %s, strategy: %s)',
        isset($existing['presets']) ? 'yes' : 'no',
        $new['strategy']
    ));
}

// ─── 3. Sync Global Colors (gcids) ─────────────────────────────────────

function sync_global_colors(array $vars): void {
    $color_tokens = get_prefixed_values($vars, 'color_');
    if (empty($color_tokens)) {
        WP_CLI::log('gcids: no color tokens found, skipping.');
        return;
    }

    if (!class_exists('\ET\Builder\Packages\GlobalData\GlobalData')) {
        WP_CLI::warning('Divi 5 GlobalData class not found. Skipping gcid sync.');
        return;
    }

    $colors_ds = [];
    $key_map   = [];

    foreach ($color_tokens as $key => $hex) {
        $hex = color_ensure_hash($hex);
        $gcid = 'gcid-' . sanitize_title($key);
        $key_map[$gcid] = $key;
        $colors_ds[$gcid] = ['color' => $hex, 'active' => 'yes'];
    }

    // Customizer slot gcids
    $customizer_map = [];
    foreach ($vars as $key => $value) {
        if (str_starts_with($key, 'customizer_')) {
            $customizer_map[substr($key, 11)] = $value;
        }
    }
    foreach ($customizer_map as $slot => $token_key) {
        $gcid = CUSTOMIZER_SLOTS[$slot] ?? '';
        if (!empty($gcid) && isset($color_tokens[$token_key])) {
            $key_map[$gcid] = $token_key . ' (customizer)';
            $colors_ds[$gcid] = ['color' => color_ensure_hash($color_tokens[$token_key]), 'active' => 'yes'];
        }
    }

    // Clear existing to prevent duplicates
    $existing_global_data = maybe_unserialize(et_get_option('et_global_data'));
    if (is_array($existing_global_data) && isset($existing_global_data['global_colors'])) {
        $existing_global_data['global_colors'] = [];
        et_update_option('et_global_data', $existing_global_data);
    }

    \ET\Builder\Packages\GlobalData\GlobalData::set_global_colors($colors_ds, true);
    update_option('_dac_gcid_hash', md5(json_encode($colors_ds)));

    WP_CLI::log(sprintf('gcids: %d color tokens + %d customizer slots synced.', count($color_tokens), count($customizer_map)));
}

// ─── 4. Sync Global Variables (gvids) ──────────────────────────────────

function sync_global_variables(array $vars): void {
    if (!class_exists('\ET\Builder\Packages\GlobalData\GlobalData')) {
        WP_CLI::warning('Divi 5 GlobalData class not found. Skipping gvid sync.');
        return;
    }

    $gvids = [];

    // ── Numbers: radii ──
    $radii = get_prefixed_values($vars, 'radius_');
    $order = 1;
    foreach ($radii as $name => $value) {
        $gvids['numbers']['gvid-radius-' . sanitize_title($name)] = [
            'label'  => 'Border Radius ' . ucfirst($name),
            'value'  => $value,
            'order'  => $order++,
            'status' => 'active',
        ];
    }

    // ── Numbers: spaces ──
    $spaces = get_prefixed_values($vars, 'space_');
    foreach ($spaces as $name => $value) {
        $gvids['numbers']['gvid-space-' . sanitize_title($name)] = [
            'label'  => 'Spacing ' . ucfirst($name),
            'value'  => $value,
            'order'  => $order++,
            'status' => 'active',
        ];
    }

    // ── Fonts ──
    $fonts = get_prefixed_values($vars, 'font_');
    $order = 1;
    foreach ($fonts as $name => $value) {
        $family = explode(',', $value)[0];
        $family = trim($family, "'\" ");
        $gvids['fonts']['gvid-font-' . sanitize_title($name)] = [
            'label'  => 'Font ' . ucfirst($name),
            'value'  => $family,
            'order'  => $order++,
            'status' => 'active',
        ];
    }

    if (empty($gvids)) {
        WP_CLI::log('gvids: no radius/space/font tokens found, skipping.');
        return;
    }

    $counts = [];
    foreach ($gvids as $type => $items) {
        $counts[] = count($items) . ' ' . $type;
    }

    \ET\Builder\Packages\GlobalData\GlobalData::set_global_variables($gvids);
    WP_CLI::log(sprintf('gvids: %s registered as Divi 5 Global Variables.', implode(', ', $counts)));
}

// ─── 5. Flush Divi Cache ───────────────────────────────────────────────

function flush_divi_cache(): void {
    $upload_dir = wp_get_upload_dir();
    $et_cache = $upload_dir['basedir'] . '/et-cache';

    if (is_dir($et_cache)) {
        $files = glob($et_cache . '/et-divi-customizer*');
        foreach ($files as $f) unlink($f);
    }
    $global_dir = $et_cache . '/global';
    if (is_dir($global_dir)) {
        array_map('unlink', glob($global_dir . '/*'));
    }

    delete_option('et_core_page_resource_auto_clear');
    update_option('et_core_page_resource_auto_clear', time());

    if (function_exists('et_core_clear_wp_cache')) {
        et_core_clear_wp_cache();
    }

    WP_CLI::log('Divi CSS cache flushed.');
}

// ─── Main ──────────────────────────────────────────────────────────────

function run(): void {
    $vars_path = get_cli_arg('vars');
    if (!$vars_path) $vars_path = find_vars_file();
    if (!$vars_path) {
        WP_CLI::error('Could not locate _design_vars.json. Pass --vars=<path>');
    }

    $vars = load_json($vars_path);
    if ($vars === null) {
        WP_CLI::error("Failed to parse _design_vars.json");
    }

    $brand_name = $vars['brand_name'] ?? basename(dirname(dirname($vars_path)));
    WP_CLI::log('── Syncing brand: ' . $brand_name . ' ──');

    // 1. Customizer global
    $et_divi_updates = sync_et_divi($vars);

    // 2. divitheme.json (tokens + presets)
    $paths = resolve_paths($vars_path);
    sync_divitheme($paths['divitheme'], $vars);

    // 3. Global Colors (gcids)
    sync_global_colors($vars);

    // 4. Global Variables (gvids) — radios, espacios, fuentes como variables nativas
    sync_global_variables($vars);

    // 5. Flush cache
    flush_divi_cache();

    WP_CLI::success('Brand fully synced: et_divi + divitheme.json + gcids + gvids.');
}

function get_cli_arg(string $name): ?string {
    global $argv;
    foreach ($argv as $arg) {
        if (preg_match('/^--' . $name . '=(.+)$/', $arg, $m)) {
            return $m[1];
        }
    }
    $env = getenv('DAW_' . strtoupper($name));
    return $env ?: null;
}

run();
