<?php
/**
 * Trait: Module_Metadata
 *
 * Reads Divi 5's official _all_modules_metadata.php to provide
 * accurate attribute serialization paths. The Layout_Engine uses
 * this to stop guessing and compile blocks against the real spec.
 *
 * Files consumed:
 *   - _all_modules_metadata.php              (2.6MB — schema: types, settings, groups)
 *   - _all_modules_default_render_attributes.php (155KB — default values per attribute)
 */

trait Module_Metadata {

    private static $meta_data     = null;
    private static $render_data   = null;
    private static $meta_loaded   = false;

    /**
     * Lazy-load metadata files once.
     */
    private static function load_metadata(): void {
        if (self::$meta_loaded) return;

        $meta_path   = DIVI_AGENTIC_CORE_DIR . '/data/_all_modules_metadata.php';
        $render_path = DIVI_AGENTIC_CORE_DIR . '/data/_all_modules_default_render_attributes.php';

        if (file_exists($meta_path)) {
            self::$meta_data = include $meta_path;
        } else {
            self::$meta_data = [];
            trigger_error('Module_Metadata: _all_modules_metadata.php not found at ' . $meta_path, E_USER_WARNING);
        }

        if (file_exists($render_path)) {
            self::$render_data = include $render_path;
        } else {
            self::$render_data = [];
        }

        self::$meta_loaded = true;
    }

    // ──────────────────────────────────────────────
    //  Public API
    // ──────────────────────────────────────────────

    /**
     * Get the metadata for a single module by slug or full name.
     */
    public static function get_module_meta(string $slug): ?array {
        self::load_metadata();
        $key = self::resolve_key($slug);
        return self::$meta_data[$key] ?? null;
    }

    /**
     * Check if a module has a specific attribute.
     */
    public static function module_has_attribute(string $slug, string $attr): bool {
        $meta = self::get_module_meta($slug);
        return $meta && isset($meta['attributes'][$attr]);
    }

    /**
     * Get the attribute definition (type, default, settings) for a module attribute.
     */
    public static function get_attribute_def(string $slug, string $attr): ?array {
        $meta = self::get_module_meta($slug);
        return $meta['attributes'][$attr] ?? null;
    }

    /**
     * Get the innerContent serialization path for an attribute.
     * Returns ['groupType' => 'group-item'|'group-items', 'items' => [...]]
     * or null if the attribute doesn't use innerContent.
     */
    public static function get_inner_content_schema(string $slug, string $attr): ?array {
        $def = self::get_attribute_def($slug, $attr);
        if (!$def || !isset($def['settings']['innerContent'])) return null;
        return $def['settings']['innerContent'];
    }

    /**
     * Check if an attribute uses "group-item" (single value like title)
     * or "group-items" (multiple sub-values like image → {src, alt, id}).
     */
    public static function is_group_items(string $slug, string $attr): ?bool {
        $schema = self::get_inner_content_schema($slug, $attr);
        if (!$schema) return null;
        if (($schema['groupType'] ?? '') === 'group-items') return true;
        if (isset($schema['items'])) return true;
        return false;
    }

    /**
     * Return all sub-item keys for a group-items attribute.
     * e.g. slide.image → ['src', 'alt', 'id', 'titleText']
     */
    public static function get_inner_content_items(string $slug, string $attr): array {
        $schema = self::get_inner_content_schema($slug, $attr);
        if (!$schema || !isset($schema['items'])) return [];
        return array_keys($schema['items']);
    }

    /**
     * Get decoration settings groups for an attribute.
     * e.g. slide → ['font', 'button', 'background', 'border', ...]
     */
    public static function get_decoration_groups(string $slug, string $attr): array {
        $def = self::get_attribute_def($slug, $attr);
        if (!$def || !isset($def['settings']['decoration'])) return [];
        return array_keys($def['settings']['decoration']);
    }

    /**
     * Get render defaults for a specific module attribute.
     * Returns the structured array from _all_modules_default_render_attributes.php.
     */
    public static function get_render_defaults(string $slug, string $attr): ?array {
        self::load_metadata();
        $key = self::resolve_key($slug);
        return self::$render_data[$key][$attr] ?? null;
    }

    /**
     * Check if a module exists in the official metadata.
     */
    public static function module_exists(string $slug): bool {
        self::load_metadata();
        return self::resolve_key($slug) !== null;
    }

    /**
     * List all known modules (key => name).
     */
    public static function get_all_modules(): array {
        self::load_metadata();
        $result = [];
        foreach (self::$meta_data as $key => $mod) {
            $result[$key] = $mod['name'] ?? "divi/$key";
        }
        return $result;
    }

    /**
     * List all modules filtered by category (section, row, column, module, child-module).
     */
    public static function get_modules_by_category(string $category): array {
        self::load_metadata();
        $result = [];
        foreach (self::$meta_data as $key => $mod) {
            if (($mod['category'] ?? '') === $category) {
                $result[$key] = $mod['name'] ?? "divi/$key";
            }
        }
        return $result;
    }

    // ──────────────────────────────────────────────
    //  Internal
    // ──────────────────────────────────────────────

    /**
     * Resolve "divi/number-counter" or "number-counter" to the metadata key.
     */
    private static function resolve_key(string $slug): ?string {
        if (isset(self::$meta_data[$slug])) return $slug;
        // Try stripping "divi/" prefix
        $stripped = preg_replace('#^divi/#', '', $slug);
        if (isset(self::$meta_data[$stripped])) return $stripped;
        // Search by full name
        foreach (self::$meta_data as $key => $mod) {
            if (($mod['name'] ?? '') === $slug) return $key;
        }
        return null;
    }
}
