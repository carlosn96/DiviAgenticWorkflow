<?php
namespace DAC\Core;

/**
 * Token Registry — fuente de verdad única para todos los tokens de diseño.
 *
 * Cualquier cambio en un token se hace AQUÍ y se propaga automáticamente a:
 *   - brand-sync.php (ET_DIVI_MAP, validación, gvids, gcids)
 *   - Design_Resolver (patrones de resolución {{design:*}})
 *   - Customizer_Engine (token → et_divi mapping)
 *   - scaffold_vars (generación de _design_vars.json completo)
 *
 * NUNCA hardcodees mappings en múltiples archivos.
 * Si agregas un token, agrégalo SOLO aquí.
 */
class Token_Registry {

    private static ?array $tokens = null;

    private static function init(): void {
        if (self::$tokens !== null) return;

        self::$tokens = [

            // ── Brand metadata ──
            'brand_name' => [
                'type'     => 'string',
                'required' => true,
                'default'  => 'Mi Marca',
                'et_divi'  => [],
            ],
            'brand_description' => [
                'type'     => 'string',
                'required' => false,
                'default'  => '',
                'et_divi'  => [],
            ],

            // ── Colors → et_divi + gcids ──
            'color_accent' => [
                'type'     => 'color',
                'required' => true,
                'validate' => [
                    'contrast_against' => ['color_surface_light', 'color_surface_white', 'color_surface_deep'],
                    'contrast_min'     => 4.5,
                    'harmony_group'    => 'primary',
                ],
                'et_divi'  => [
                    'accent_color', 'link_color',
                    'menu_link_active', 'fixed_menu_link_active',
                    'primary_nav_dropdown_line_color',
                    'secondary_nav_bg', 'secondary_nav_dropdown_bg',
                    'fixed_secondary_nav_bg',
                    'footer_widget_header_color', 'footer_widget_bullet_color',
                    'footer_menu_active_link_color',
                    'slide_nav_bg',
                    'all_buttons_bg_color',
                ],
            ],
            'color_accent_hover' => [
                'type'     => 'color',
                'required' => false,
                'default'  => null,
                'validate' => [
                    'contrast_against' => ['color_surface_light', 'color_surface_white'],
                    'contrast_min'     => 4.5,
                    'harmony_group'    => 'primary',
                ],
                'et_divi'  => ['all_buttons_bg_color_hover'],
            ],
            'color_ink' => [
                'type'     => 'color',
                'required' => false,
                'default'  => '#ffffff',
                'et_divi'  => [],
            ],
            'color_ink_soft' => [
                'type'     => 'color',
                'required' => false,
                'default'  => '#666666',
                'et_divi'  => [],
            ],
            'color_surface_deep' => [
                'type'     => 'color',
                'required' => true,
                'validate' => [
                    'contrast_against' => ['color_text_on_dark'],
                    'contrast_min'     => 7.0,
                    'harmony_group'    => 'surface',
                ],
                'et_divi'  => [
                    'primary_nav_bg', 'fixed_primary_nav_bg',
                    'mobile_primary_nav_bg',
                    'footer_bg', 'bottom_bar_background_color',
                ],
            ],
            'color_surface_mid' => [
                'type'     => 'color',
                'required' => false,
                'default'  => null,
                'validate' => [
                    'harmony_group' => 'surface',
                ],
                'et_divi'  => ['primary_nav_dropdown_bg', 'secondary_nav_dropdown_bg'],
            ],
            'color_surface_light' => [
                'type'     => 'color',
                'required' => false,
                'default'  => null,
                'validate' => [
                    'harmony_group' => 'surface',
                ],
                'et_divi'  => [],
            ],
            'color_surface_white' => [
                'type'     => 'color',
                'required' => false,
                'default'  => '#ffffff',
                'validate' => [
                    'harmony_group' => 'surface',
                ],
                'et_divi'  => [],
            ],
            'color_text_primary' => [
                'type'     => 'color',
                'required' => true,
                'validate' => [
                    'contrast_against' => ['color_surface_light', 'color_surface_white'],
                    'contrast_min'     => 7.0,
                    'harmony_group'    => 'text',
                ],
                'et_divi'  => ['font_color', 'header_color', 'bottom_bar_text_color'],
            ],
            'color_text_secondary' => [
                'type'     => 'color',
                'required' => false,
                'default'  => '#666666',
                'validate' => [
                    'contrast_against' => ['color_surface_light', 'color_surface_white'],
                    'contrast_min'     => 7.0,
                    'harmony_group'    => 'text',
                ],
                'et_divi'  => [],
            ],
            'color_text_on_dark' => [
                'type'     => 'color',
                'required' => true,
                'validate' => [
                    'contrast_against' => ['color_surface_deep'],
                    'contrast_min'     => 7.0,
                    'harmony_group'    => 'text',
                ],
                'et_divi'  => [
                    'menu_link', 'fixed_menu_link',
                    'secondary_nav_text_color_new', 'secondary_nav_dropdown_link_color',
                    'fixed_secondary_menu_link', 'mobile_menu_link',
                    'primary_nav_dropdown_link_color',
                    'footer_widget_text_color', 'footer_widget_link_color',
                    'slide_nav_links_color', 'slide_nav_links_color_active',
                ],
            ],
            'color_success' => [
                'type'     => 'color',
                'required' => false,
                'default'  => '#28a745',
                'validate' => [
                    'contrast_against' => ['color_surface_light', 'color_surface_white'],
                    'contrast_min'     => 4.5,
                    'harmony_group'    => 'functional',
                ],
                'et_divi'  => [],
            ],
            'color_error' => [
                'type'     => 'color',
                'required' => false,
                'default'  => '#dc3545',
                'validate' => [
                    'contrast_against' => ['color_surface_light', 'color_surface_white'],
                    'contrast_min'     => 4.5,
                    'harmony_group'    => 'functional',
                ],
                'et_divi'  => [],
            ],

            // ── Font families → et_divi + gvids fonts ──
            'font_display' => [
                'type'     => 'font-family',
                'required' => true,
                'validate' => [
                    'pairing_group' => 'display',
                ],
                'et_divi'  => ['heading_font'],
                'gvid'     => 'fonts',
            ],
            'font_body' => [
                'type'     => 'font-family',
                'required' => true,
                'validate' => [
                    'pairing_group' => 'sans',
                ],
                'et_divi'  => ['body_font', 'primary_nav_font', 'secondary_nav_font', 'slide_nav_font', 'all_buttons_font'],
                'gvid'     => 'fonts',
            ],
            'font_ui' => [
                'type'     => 'font-family',
                'required' => false,
                'default'  => null,
                'validate' => [
                    'pairing_group' => 'sans',
                ],
                'et_divi'  => [],
                'gvid'     => 'fonts',
            ],

            // ── Font values → et_divi (no gvid) ──
            'font_body_size'   => ['type' => 'size',   'et_divi' => ['body_font_size']],
            'font_body_height' => ['type' => 'number', 'et_divi' => ['body_font_height']],
            'font_body_weight' => ['type' => 'number', 'et_divi' => ['body_font_weight']],
            'font_heading_weight' => ['type' => 'number', 'et_divi' => ['heading_font_weight']],

            // ── Heading sizes h1-h6 → et_divi (no gvid) ──
            'font_heading_size_h1' => ['type' => 'size', 'default' => '48px', 'validate' => ['scale_group' => 'heading', 'order' => 1], 'et_divi' => ['heading_font_size_h1']],
            'font_heading_size_h2' => ['type' => 'size', 'default' => '36px', 'validate' => ['scale_group' => 'heading', 'order' => 2], 'et_divi' => ['heading_font_size_h2']],
            'font_heading_size_h3' => ['type' => 'size', 'default' => '28px', 'validate' => ['scale_group' => 'heading', 'order' => 3], 'et_divi' => ['heading_font_size_h3']],
            'font_heading_size_h4' => ['type' => 'size', 'default' => '24px', 'validate' => ['scale_group' => 'heading', 'order' => 4], 'et_divi' => ['heading_font_size_h4']],
            'font_heading_size_h5' => ['type' => 'size', 'default' => '20px', 'validate' => ['scale_group' => 'heading', 'order' => 5], 'et_divi' => ['heading_font_size_h5']],
            'font_heading_size_h6' => ['type' => 'size', 'default' => '18px', 'validate' => ['scale_group' => 'heading', 'order' => 6], 'et_divi' => ['heading_font_size_h6']],

            // ── Radii → gvids numbers ──
            'radius_sm'   => ['type' => 'size', 'default' => '4px',   'validate' => ['scale_group' => 'radius', 'order' => 1], 'et_divi' => [], 'gvid' => 'numbers'],
            'radius_md'   => ['type' => 'size', 'default' => '8px',   'validate' => ['scale_group' => 'radius', 'order' => 2], 'et_divi' => [], 'gvid' => 'numbers'],
            'radius_lg'   => ['type' => 'size', 'default' => '16px',  'validate' => ['scale_group' => 'radius', 'order' => 3], 'et_divi' => [], 'gvid' => 'numbers'],
            'radius_xl'   => ['type' => 'size', 'default' => '24px',  'validate' => ['scale_group' => 'radius', 'order' => 4], 'et_divi' => [], 'gvid' => 'numbers'],
            'radius_full' => ['type' => 'size', 'default' => '9999px','validate' => ['scale_group' => 'radius', 'order' => 5], 'et_divi' => [], 'gvid' => 'numbers'],

            // ── Spaces → gvids numbers ──
            'space_xs'  => ['type' => 'size', 'default' => '8px',   'validate' => ['scale_group' => 'space', 'order' => 1], 'et_divi' => [], 'gvid' => 'numbers'],
            'space_sm'  => ['type' => 'size', 'default' => '12px',  'validate' => ['scale_group' => 'space', 'order' => 2], 'et_divi' => [], 'gvid' => 'numbers'],
            'space_md'  => ['type' => 'size', 'default' => '16px',  'validate' => ['scale_group' => 'space', 'order' => 3], 'et_divi' => [], 'gvid' => 'numbers'],
            'space_lg'  => ['type' => 'size', 'default' => '24px',  'validate' => ['scale_group' => 'space', 'order' => 4], 'et_divi' => [], 'gvid' => 'numbers'],
            'space_xl'  => ['type' => 'size', 'default' => '32px',  'validate' => ['scale_group' => 'space', 'order' => 5], 'et_divi' => [], 'gvid' => 'numbers'],
            'space_2xl' => ['type' => 'size', 'default' => '64px',  'validate' => ['scale_group' => 'space', 'order' => 6], 'et_divi' => [], 'gvid' => 'numbers'],
            'space_3xl' => ['type' => 'size', 'default' => '128px', 'validate' => ['scale_group' => 'space', 'order' => 7], 'et_divi' => [], 'gvid' => 'numbers'],

            // ── Shadows → gvids numbers ──
            'shadow_sm' => ['type' => 'string', 'default' => '0 1px 2px rgba(0,0,0,0.1)',  'et_divi' => [], 'gvid' => 'numbers'],
            'shadow_md' => ['type' => 'string', 'default' => '0 4px 8px rgba(0,0,0,0.15)', 'et_divi' => [], 'gvid' => 'numbers'],
            'shadow_lg' => ['type' => 'string', 'default' => '0 8px 24px rgba(0,0,0,0.2)', 'et_divi' => [], 'gvid' => 'numbers'],
            'shadow_xl' => ['type' => 'string', 'default' => '0 16px 48px rgba(0,0,0,0.25)','et_divi' => [], 'gvid' => 'numbers'],

            // ── Easings → gvids numbers ──
            'easing_default' => ['type' => 'string', 'default' => 'ease',                                 'et_divi' => [], 'gvid' => 'numbers'],
            'easing_enter'   => ['type' => 'string', 'default' => 'cubic-bezier(0.32, 0.72, 0, 1)',       'et_divi' => [], 'gvid' => 'numbers'],
            'easing_exit'    => ['type' => 'string', 'default' => 'cubic-bezier(0.5, 0, 0.75, 0)',        'et_divi' => [], 'gvid' => 'numbers'],

            // ── Durations → gvids numbers ──
            'duration_fast'   => ['type' => 'size', 'default' => '200ms', 'et_divi' => [], 'gvid' => 'numbers'],
            'duration_normal' => ['type' => 'size', 'default' => '400ms', 'et_divi' => [], 'gvid' => 'numbers'],
            'duration_slow'   => ['type' => 'size', 'default' => '800ms', 'et_divi' => [], 'gvid' => 'numbers'],

            // ── Buttons → et_divi ──
            'button_border_radius'  => ['type' => 'size',   'default' => '4px',    'et_divi' => ['all_buttons_border_radius']],
            'button_border_width'   => ['type' => 'size',   'default' => '0',      'et_divi' => ['all_buttons_border_width']],
            'button_font_size'      => ['type' => 'size',   'default' => '16px',   'et_divi' => ['all_buttons_font_size']],
            'button_font_style'     => ['type' => 'string', 'default' => '',       'et_divi' => ['all_buttons_font_style']],
            'button_text_color'        => ['type' => 'color', 'default' => '#ffffff', 'validate' => ['contrast_against' => ['color_accent', 'color_accent_hover'], 'contrast_min' => 4.5], 'et_divi' => ['all_buttons_text_color']],
            'button_text_color_hover'  => ['type' => 'color', 'default' => '#ffffff', 'validate' => ['contrast_against' => ['color_accent_hover', 'color_accent'], 'contrast_min' => 4.5], 'et_divi' => ['all_buttons_text_color_hover']],
            'button_border_color'   => ['type' => 'color',  'default' => null,     'et_divi' => ['all_buttons_border_color']],

            // ── Layout → et_divi ──
            'layout_content_width' => ['type' => 'size',   'default' => '1200px', 'et_divi' => []],
            'layout_fixed_nav'     => ['type' => 'on_off', 'default' => 'on',     'et_divi' => ['divi_fixed_nav']],
            'layout_sidebar'       => ['type' => 'on_off', 'default' => 'no',     'et_divi' => []],

            // ── Performance → et_divi ──
            'perf_dynamic_framework' => ['type' => 'on_off', 'default' => 'on', 'et_divi' => ['divi_dynamic_module_framework']],
            'perf_dynamic_icons'     => ['type' => 'on_off', 'default' => 'on', 'et_divi' => ['divi_dynamic_icons']],
            'perf_critical_css'      => ['type' => 'on_off', 'default' => 'on', 'et_divi' => ['divi_critical_css']],
            'perf_defer_block_css'   => ['type' => 'on_off', 'default' => 'on', 'et_divi' => ['divi_defer_block_css']],
            'perf_jquery_body'       => ['type' => 'on_off', 'default' => 'on', 'et_divi' => ['divi_enable_jquery_body']],
            'perf_disable_emojis'    => ['type' => 'on_off', 'default' => 'on', 'et_divi' => ['divi_disable_emojis']],

            // ── Social → et_divi ──
            'social_facebook'  => ['type' => 'string', 'default' => '', 'et_divi' => ['divi_facebook_url']],
            'social_twitter'   => ['type' => 'string', 'default' => '', 'et_divi' => ['divi_twitter_url']],
            'social_instagram' => ['type' => 'string', 'default' => '', 'et_divi' => ['divi_instagram_url']],
            'social_youtube'   => ['type' => 'string', 'default' => '', 'et_divi' => ['divi_youtube_url']],
            'social_linkedin'  => ['type' => 'string', 'default' => '', 'et_divi' => ['divi_linkedin_url']],

            // ── Derived tokens (no directos de _design_vars.json) ──
            '_secondary_accent' => [
                'type'     => 'derived',
                'required' => false,
                'et_divi'  => ['secondary_accent_color'],
            ],

            // ── Media → opciones de WordPress (con post_sync handlers) ──
            'logo_id' => [
                'type' => 'id', 'default' => null, 'et_divi' => [],
                'post_sync' => ['handler' => 'attachment_url', 'option' => 'divi_logo', 'target' => 'et'],
            ],
            'favicon_id' => [
                'type' => 'id', 'default' => null, 'et_divi' => [],
                'post_sync' => ['handler' => 'attachment_id', 'option' => 'site_icon', 'target' => 'wp'],
            ],
            'apple_icon_id' => [
                'type' => 'id', 'default' => null, 'et_divi' => [],
                'post_sync' => ['handler' => 'attachment_url', 'option' => 'divi_apple_touch_icon', 'target' => 'et'],
            ],
        ];

        // Fill defaults for optional tokens without explicit default
        foreach (self::$tokens as $key => &$def) {
            if (empty($def['required']) && !array_key_exists('default', $def)) {
                $def['default'] = null;
            }
        }
        unset($def);
    }

    // ─── Queries ────────────────────────────────────────────────────────

    public static function get_all(): array {
        self::init();
        return self::$tokens;
    }

    /** Returns map for brand-sync: source_key → [et_divi_option, ...] */
    public static function get_et_divi_map(): array {
        self::init();
        $map = [];
        foreach (self::$tokens as $key => $def) {
            if (!empty($def['et_divi'])) {
                $map[$key] = $def['et_divi'];
            }
        }
        return $map;
    }

    /** Returns validation schema: key → [type, required?, default?] */
    public static function get_validation_schema(): array {
        self::init();
        $schema = [];
        foreach (self::$tokens as $key => $def) {
            // Skip derived tokens (no aparecen en _design_vars.json)
            if ($def['type'] === 'derived') continue;
            $entry = ['type' => $def['type']];
            if (!empty($def['required'])) {
                $entry['required'] = true;
            }
            if (array_key_exists('default', $def)) {
                $entry['default'] = $def['default'];
            }
            $schema[$key] = $entry;
        }
        return $schema;
    }

    /** Returns required key names */
    public static function get_required_keys(): array {
        self::init();
        $keys = [];
        foreach (self::$tokens as $key => $def) {
            if (!empty($def['required'])) {
                $keys[] = $key;
            }
        }
        return $keys;
    }

    /** Returns defaults: key → default value */
    public static function get_defaults(): array {
        self::init();
        $defaults = [];
        foreach (self::$tokens as $key => $def) {
            if (array_key_exists('default', $def)) {
                $defaults[$key] = $def['default'];
            }
        }
        return $defaults;
    }

    /**
     * Returns gvid config for brand-sync:
     * [gvid_group] => [source_key => value, ...]
     */
    public static function get_gvid_groups(): array {
        self::init();
        $groups = [];
        foreach (self::$tokens as $key => $def) {
            if (!empty($def['gvid'])) {
                $group = $def['gvid'];
                if (!isset($groups[$group])) {
                    $groups[$group] = [];
                }
                $groups[$group][$key] = $def;
            }
        }
        return $groups;
    }

    /**
     * Returns gvid prefixes for Design_Resolver regex.
     * Extracts unique gvid prefixes from token keys that have a gvid group.
     * e.g. 'radius_sm' → 'radius', 'space_md' → 'space'
     */
    public static function get_gvid_prefixes(): array {
        self::init();
        $prefixes = [];
        foreach (self::$tokens as $key => $def) {
            if (!empty($def['gvid'])) {
                // Extract prefix before first underscore
                $parts = explode('_', $key);
                $prefix = $parts[0];
                $prefixes[$prefix] = true;
            }
        }
        return array_keys($prefixes);
    }

    /** Returns font-family source keys */
    public static function get_font_family_keys(): array {
        self::init();
        $keys = [];
        foreach (self::$tokens as $key => $def) {
            if ($def['type'] === 'font-family') {
                $keys[] = $key;
            }
        }
        return $keys;
    }

    /**
     * Returns customizer slot → gcid mapping.
     * Fuente de verdad única — reemplaza 4 copias hardcodeadas.
     */
    public static function get_customizer_slots(): array {
        return [
            'primary'   => 'gcid-primary-color',
            'secondary' => 'gcid-secondary-color',
            'heading'   => 'gcid-heading-color',
            'body'      => 'gcid-body-color',
            'link'      => 'gcid-link-color',
        ];
    }

    /**
     * Returns gcid slugs to skip in Design_Resolver.
     * Derivado de get_customizer_slots() para no duplicar.
     */
    public static function get_gcid_slugs_to_skip(): array {
        $slugs = [];
        foreach (self::get_customizer_slots() as $short => $gcid) {
            $slug = str_replace('gcid-', '', $gcid);
            $slugs[] = $slug;
        }
        return $slugs;
    }

    /**
     * Returns inverse customizer map: gcid-slug → short name.
     * Para BlocksToSchema y otros que necesitan reverse lookup.
     */
    public static function get_inverse_customizer_slots(): array {
        $inverse = [];
        foreach (self::get_customizer_slots() as $short => $gcid) {
            $slug = str_replace('gcid-', '', $gcid);
            $inverse[$slug] = $short;
        }
        return $inverse;
    }

    /**
     * Returns validation rules: key → validate metadata.
     * Usado por Design_Validator para checks de contraste, escala y pairing.
     */
    public static function get_validation_rules(): array {
        self::init();
        $rules = [];
        foreach (self::$tokens as $key => $def) {
            if (!empty($def['validate'])) {
                $rules[$key] = $def['validate'];
            }
        }
        return $rules;
    }

    /**
     * Returns post-sync handlers: source_key → handler config.
     * Para brand-sync: procesa logo, favicon, apple_icon post et_divi sync.
     */
    public static function get_post_sync_handlers(): array {
        self::init();
        $handlers = [];
        foreach (self::$tokens as $key => $def) {
            if (!empty($def['post_sync'])) {
                $handlers[$key] = $def['post_sync'];
            }
        }
        return $handlers;
    }

    /** Returns derived token keys (empiezan con _) */
    public static function get_derived_keys(): array {
        self::init();
        $keys = [];
        foreach (self::$tokens as $key => $def) {
            if (str_starts_with($key, '_')) {
                $keys[] = $key;
            }
        }
        return $keys;
    }

    /** Returns color source keys, excluding derived tokens */
    public static function get_color_keys(): array {
        self::init();
        $keys = [];
        foreach (self::$tokens as $key => $def) {
            if ($def['type'] === 'color' && !str_starts_with($key, '_')) {
                $keys[] = $key;
            }
        }
        return $keys;
    }

    /**
     * Genera un scaffold completo de _design_vars.json con todos los tokens
     * y sus defaults reales. Sin null/empty — o tiene default o no aparece.
     * Único generador autoritativo.
     *
     * Uso: php -r "echo json_encode(\DAC\Core\Token_Registry::generate_scaffold(), JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES);"
     */
    public static function generate_scaffold(): array {
        self::init();
        $defaults = self::get_defaults();

        $scaffold = [
            'brand_name' => 'Mi Marca',
            'brand_description' => '',
        ];

        // Todos los tokens del registry (excepto derived)
        foreach (self::$tokens as $key => $def) {
            if ($def['type'] === 'derived') continue;

            // Required sin default → null (validate_vars avisa pero no frena)
            if (!empty($def['required']) && !array_key_exists('default', $def)) {
                $scaffold[$key] = null;
                continue;
            }

            // Con default real → usarlo
            if (array_key_exists('default', $def) && $def['default'] !== null) {
                $scaffold[$key] = $def['default'];
            }
        }

        // Media IDs
        $scaffold['logo_id'] = null;
        $scaffold['favicon_id'] = null;
        $scaffold['apple_icon_id'] = null;

        // Customizer mapping
        $scaffold['customizer_primary'] = 'accent';
        $scaffold['customizer_secondary'] = 'secondary_accent';
        $scaffold['customizer_heading'] = 'text_primary';
        $scaffold['customizer_body'] = 'text_primary';
        $scaffold['customizer_link'] = 'accent';

        return $scaffold;
    }
}
