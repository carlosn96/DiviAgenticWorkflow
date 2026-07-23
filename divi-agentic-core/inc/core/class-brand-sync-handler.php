<?php

namespace DAC\Core;

use WP_CLI;
use DAC\Core\Token_Registry;

class Brand_Sync_Handler {

    public static function run(?string $site = null): void {
        $vars_path = null;

        if ($site) {
            $p = dirname(DIVI_AGENTIC_CORE_DIR) . '/site/' . $site . '/brand/_design_vars.json';
            if (file_exists($p)) $vars_path = $p;
        }

        if (!$vars_path) $vars_path = self::find_vars_file();
        if (!$vars_path) {
            WP_CLI::error('Could not locate _design_vars.json. Pass site slug.');
        }

        $vars = self::load_json($vars_path);
        if ($vars === null) {
            WP_CLI::error("Failed to parse _design_vars.json");
        }

        self::validate_vars($vars);

        $brand_name = $vars['brand_name'] ?? basename(dirname(dirname($vars_path)));
        WP_CLI::log('── Syncing brand: ' . $brand_name . ' ──');

        self::sync_et_divi($vars);
        $paths = self::resolve_paths($vars_path);
        self::sync_divitheme($paths['divitheme'], $vars);
        self::sync_global_colors($vars);
        self::sync_global_variables($vars);
        self::flush_divi_cache();

        WP_CLI::success("Brand fully synced: et_divi (40 groups) + divitheme.json + gcids + gvids.");
    }

    private static function find_vars_file(): ?string {
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

        $site_dir = dirname(DIVI_AGENTIC_CORE_DIR) . '/site';
        if (is_dir($site_dir)) {
            $glob = glob($site_dir . '/*/brand/_design_vars.json');
            if (!empty($glob)) return $glob[0];
        }

        return null;
    }

    private static function resolve_paths(string $vars_path): array {
        $bundle_dir = dirname(DIVI_AGENTIC_CORE_DIR);
        preg_match('#/site/([^/]+)/brand/_design_vars\.json$#', $vars_path, $m);
        $site_name = $m[1] ?? '';

        return [
            'bundle'    => $bundle_dir,
            'site'      => $site_name,
            'divitheme' => $bundle_dir . '/site/' . $site_name . '/design-system/divitheme.json',
        ];
    }

    private static function load_json(string $path): ?array {
        if (!file_exists($path)) return null;
        $data = json_decode(file_get_contents($path), true);
        return (json_last_error() === JSON_ERROR_NONE) ? $data : null;
    }

    private static function color_ensure_hash(string $hex): string {
        $hex = trim($hex);
        if (str_starts_with($hex, '#')) return $hex;
        if (preg_match('/^[0-9A-Fa-f]{3,8}$/', $hex)) return "#{$hex}";
        return $hex;
    }

    private static function sync_et_divi(array $vars): array {
        $updated = [];
        $map = Token_Registry::get_et_divi_map();
        $font_family_keys = Token_Registry::get_font_family_keys();

        foreach ($map as $source_key => $et_keys) {
            $value = $vars[$source_key] ?? null;

            if ($value === null && str_starts_with($source_key, '_')) {
                if ($source_key === '_secondary_accent') {
                    $value = $vars['color_surface_mid'] ?? '#0A1E3D';
                }
            }

            if ($value === null || $value === '') continue;

            if (in_array($source_key, Token_Registry::get_color_keys(), true)) {
                $value = self::color_ensure_hash($value);
            }

            if (in_array($source_key, $font_family_keys, true)) {
                $value = explode(',', $value)[0];
                $value = trim($value, "'\" ");
            }

            foreach ($et_keys as $et_key) {
                if (!empty($et_key) && et_get_option($et_key) !== $value) {
                    et_update_option($et_key, $value);
                    $updated[] = $et_key;
                }
            }
        }

        $handlers = Token_Registry::get_post_sync_handlers();
        foreach ($handlers as $source_key => $handler) {
            $id = $vars[$source_key] ?? null;
            if (empty($id)) continue;
            switch ($handler['handler']) {
                case 'attachment_url':
                    $url = wp_get_attachment_url((int)$id);
                    if ($url) {
                        $current = $handler['target'] === 'et'
                            ? et_get_option($handler['option'])
                            : get_option($handler['option']);
                        if ($current !== $url) {
                            if ($handler['target'] === 'et') {
                                et_update_option($handler['option'], $url);
                            } else {
                                update_option($handler['option'], $url);
                            }
                            $updated[] = $handler['option'];
                        }
                    }
                    break;
                case 'attachment_id':
                    if (get_option($handler['option']) !== (int)$id) {
                        update_option($handler['option'], (int)$id);
                        $updated[] = $handler['option'];
                    }
                    break;
            }
        }

        if (!empty($updated)) {
            WP_CLI::log(sprintf('et_divi: %d option(s) updated: %s', count($updated), implode(', ', $updated)));
        } else {
            WP_CLI::log('et_divi: no changes needed.');
        }

        return $updated;
    }

    private static function sync_divitheme(string $path, array $vars): void {
        $dir = dirname($path);
        if (!is_dir($dir)) mkdir($dir, 0755, true);

        $existing = self::load_json($path);

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

    private static function sync_global_colors(array $vars): void {
        $color_keys = Token_Registry::get_color_keys();
        $color_tokens = [];
        foreach ($color_keys as $key) {
            if (isset($vars[$key])) {
                $name = str_replace('_', '-', substr($key, strlen('color_')));
                $color_tokens[$name] = $vars[$key];
            }
        }

        if (empty($color_tokens)) {
            WP_CLI::log('gcids: no color tokens found, skipping.');
            return;
        }

        if (!class_exists('\ET\Builder\Packages\GlobalData\GlobalData')) {
            WP_CLI::warning('Divi 5 GlobalData class not found. Skipping gcid sync.');
            return;
        }

        $colors_ds = [];

        foreach ($color_tokens as $key => $hex) {
            $hex = self::color_ensure_hash($hex);
            $gcid = 'gcid-' . sanitize_title($key);
            $colors_ds[$gcid] = ['color' => $hex, 'active' => 'yes'];
        }

        foreach ($vars as $key => $value) {
            if (str_starts_with($key, 'customizer_')) {
                $slot = substr($key, 11);
                $slots = Token_Registry::get_customizer_slots();
                $gcid = $slots[$slot] ?? '';
                if (!empty($gcid) && isset($color_tokens[$value])) {
                    $colors_ds[$gcid] = ['color' => self::color_ensure_hash($color_tokens[$value]), 'active' => 'yes'];
                }
            }
        }

        $existing_global_data = maybe_unserialize(et_get_option('et_global_data'));
        if (is_array($existing_global_data) && isset($existing_global_data['global_colors'])) {
            $existing_global_data['global_colors'] = [];
            et_update_option('et_global_data', $existing_global_data);
        }

        \ET\Builder\Packages\GlobalData\GlobalData::set_global_colors($colors_ds, true);
        update_option('_dac_gcid_hash', md5(json_encode($colors_ds)));

        WP_CLI::log(sprintf('gcids: %d color tokens + customizer slots synced.', count($color_tokens)));
    }

    private static function sync_global_variables(array $vars): void {
        if (!class_exists('\ET\Builder\Packages\GlobalData\GlobalData')) {
            WP_CLI::warning('Divi 5 GlobalData class not found. Skipping gvid sync.');
            return;
        }

        $gvids = [];
        $gvid_groups = Token_Registry::get_gvid_groups();
        $order = 1;
        foreach ($gvid_groups['numbers'] ?? [] as $source_key => $def) {
            $value = $vars[$source_key] ?? null;
            if (empty($value)) continue;
            $gvid_name = 'gvid-' . str_replace('_', '-', $source_key);
            $gvids['numbers'][$gvid_name] = [
                'label'  => ucwords(str_replace('_', ' ', $source_key)),
                'value'  => $value,
                'order'  => $order++,
                'status' => 'active',
            ];
        }

        $order = 1;
        foreach ($gvid_groups['fonts'] ?? [] as $source_key => $def) {
            $value = $vars[$source_key] ?? '';
            if ($value === '') continue;
            $family = explode(',', $value)[0];
            $family = trim($family, "'\" ");
            $gvids['fonts']['gvid-font-' . str_replace('_', '-', $source_key)] = [
                'label'  => 'Font ' . ucfirst(str_replace('_', ' ', $source_key)),
                'value'  => $family,
                'order'  => $order++,
                'status' => 'active',
            ];
        }

        if (empty($gvids)) {
            WP_CLI::log('gvids: no tokens found, skipping.');
            return;
        }

        $counts = [];
        foreach ($gvids as $type => $items) {
            $counts[] = count($items) . ' ' . $type;
        }

        \ET\Builder\Packages\GlobalData\GlobalData::set_global_variables($gvids);
        WP_CLI::log(sprintf('gvids: %s registered as Divi 5 Global Variables.', implode(', ', $counts)));
    }

    private static function flush_divi_cache(): void {
        $upload_dir = wp_get_upload_dir();
        $et_cache = $upload_dir['basedir'] . '/et-cache';

        if (is_dir($et_cache)) {
            foreach (glob($et_cache . '/et-divi-customizer*') as $f) unlink($f);
            $global_dir = $et_cache . '/global';
            if (is_dir($global_dir)) array_map('unlink', glob($global_dir . '/*'));
        }

        delete_option('et_core_page_resource_auto_clear');
        update_option('et_core_page_resource_auto_clear', time());

        if (function_exists('et_core_clear_wp_cache')) {
            et_core_clear_wp_cache();
        }

        WP_CLI::log('Divi CSS cache flushed.');
    }

    private static function validate_vars(array &$vars): void {
        $schema = Token_Registry::get_validation_schema();
        $has_errors = false;

        foreach ($schema as $key => $rule) {
            $exists = array_key_exists($key, $vars);
            $value = $vars[$key] ?? null;
            $is_required = !empty($rule['required']);

            if ($is_required && (!$exists || $value === null)) {
                if (!$exists) {
                    WP_CLI::error("Missing required key: '{$key}'");
                    $has_errors = true;
                } else {
                    WP_CLI::warning("Required key '{$key}' is null — skipping.");
                }
                continue;
            }
            if (!$exists && !$is_required && array_key_exists('default', $rule)) {
                if ($rule['default'] !== null) {
                    WP_CLI::warning("Missing optional key '{$key}' — using default: {$rule['default']}");
                }
                $vars[$key] = $rule['default'];
                continue;
            }
            if (!$exists) continue;

            $valid = true;
            $error_msg = '';

            switch ($rule['type']) {
                case 'color':
                    if ($value === null) { $valid = true; break; }
                    $valid = preg_match('/^#[0-9A-Fa-f]{3,8}$/', $value) === 1;
                    if (!$valid) $error_msg = "Expected hex color, got: {$value}";
                    break;
                case 'font-family':
                    $valid = is_string($value) && trim($value) !== '';
                    if (!$valid) $error_msg = "Expected font family string, got: " . gettype($value);
                    break;
                case 'size':
                    $valid = is_string($value) && preg_match('/^\d+(\.\d+)?(px|ms|rem|em|%)?$/', trim($value)) === 1;
                    if (!$valid) $error_msg = "Expected size (e.g. 16px), got: {$value}";
                    break;
                case 'number':
                    $valid = is_numeric($value);
                    if (!$valid) $error_msg = "Expected number, got: {$value}";
                    break;
                case 'on_off':
                    $valid = in_array($value, ['on', 'off', 'no', 'yes'], true) || is_bool($value);
                    if (!$valid) $error_msg = "Expected on/off/yes/no, got: {$value}";
                    break;
                case 'id':
                    $valid = $value === null || is_numeric($value);
                    if (!$valid) $error_msg = "Expected numeric ID or null, got: {$value}";
                    break;
                case 'string':
                    $valid = is_string($value);
                    if (!$valid) $error_msg = "Expected string, got: " . gettype($value);
                    break;
            }

            if (!$valid) {
                WP_CLI::warning("Validation failed for '{$key}': {$error_msg}");
                if (!$is_required && array_key_exists('default', $rule)) {
                    $vars[$key] = $rule['default'];
                    WP_CLI::warning("  → Replaced with default: {$rule['default']}");
                }
            }
        }

        if ($has_errors) {
            WP_CLI::error("Fix the errors above and re-run brand sync.");
        }
    }
}
