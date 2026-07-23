<?php
namespace DAC\Core;

/**
 * Customizer_Engine — legacy (parcialmente reemplazado por brand-sync.php + Token_Registry)
 *
 * brand-sync.php y Token_Registry ahora son la fuente de verdad.
 * Esta clase se mantiene para compatibilidad con DESIGN.md y {{token:*}}.
 *
 * token_map y brand_defaults se construyen desde Token_Registry
 * para evitar desviación arquitectónica.
 */
class Customizer_Engine {

    private array $token_map;

    private array $brand_defaults;

    public function __construct() {
        $this->build_token_map();
        $this->build_brand_defaults();
    }

    /**
     * Construye token_map desde Token_Registry::get_et_divi_map()
     * usando una tabla de traducción de nombres de token_map → source_key.
     */
    private function build_token_map(): void {
        $full_map = Token_Registry::get_et_divi_map();

        // Traducción: token_map_name => [source_key, group]
        $translation = [
            'palette.primary'           => ['color_accent', 'palette'],
            'palette.secondary'         => ['_secondary_accent', 'palette'],
            'palette.text'              => ['color_text_primary', 'palette'],
            'palette.header'            => ['color_text_primary', 'palette'],
            'typography.body_font'      => ['font_body', 'typography'],
            'typography.body_font_size' => ['font_body_size', 'typography'],
            'typography.body_font_height' => ['font_body_height', 'typography'],
            'typography.body_font_weight' => ['font_body_weight', 'typography'],
            'typography.heading_font'   => ['font_display', 'typography'],
            'typography.heading_font_weight' => ['font_heading_weight', 'typography'],
            'buttons.background'        => ['color_accent', 'buttons'],
            'buttons.background_hover'  => ['color_accent_hover', 'buttons'],
            'buttons.text_color'        => ['button_text_color', 'buttons'],
            'buttons.text_color_hover'  => ['button_text_color_hover', 'buttons'],
            'buttons.border_radius'     => ['button_border_radius', 'buttons'],
            'buttons.border_width'      => ['button_border_width', 'buttons'],
            'buttons.border_color'      => ['button_border_color', 'buttons'],
            'buttons.font_size'         => ['button_font_size', 'buttons'],
            'buttons.font_style'        => ['button_font_style', 'buttons'],
            'layout.content_width'      => ['layout_content_width', 'layout'],
            'layout.fixed_nav'          => ['layout_fixed_nav', 'layout'],
            'layout.sidebar'            => ['layout_sidebar', 'layout'],
            'performance.dynamic_framework' => ['perf_dynamic_framework', 'performance'],
            'performance.dynamic_icons'     => ['perf_dynamic_icons', 'performance'],
            'performance.critical_css'      => ['perf_critical_css', 'performance'],
            'performance.defer_block_css'   => ['perf_defer_block_css', 'performance'],
            'performance.jquery_body'       => ['perf_jquery_body', 'performance'],
            'performance.disable_emojis'    => ['perf_disable_emojis', 'performance'],
        ];

        $this->token_map = [];
        foreach ($translation as $composite => [$source_key, $group]) {
            $local_name = explode('.', $composite)[1];
            // Get et_divi option from full_map
            $et_options = $full_map[$source_key] ?? [];
            // Use first et_divi option as the primary
            $option_name = $et_options[0] ?? null;
            // Special cases where the translation differs from first option
            $overrides = [
                'palette.secondary' => 'secondary_accent_color',
                'palette.text'      => 'font_color',
                'palette.header'    => 'header_color',
            ];
            if (isset($overrides[$composite])) {
                $option_name = $overrides[$composite];
            }
            $this->token_map[$group][$local_name] = $option_name;
        }
    }

    /**
     * Construye brand_defaults desde Token_Registry::get_defaults()
     * usando la misma tabla de traducción.
     */
    private function build_brand_defaults(): void {
        $defaults = Token_Registry::get_defaults();

        $translation = [
            'palette.primary'   => 'color_accent',
            'palette.secondary' => '_secondary_accent',
            'palette.text'      => 'color_text_primary',
            'palette.header'    => 'color_text_primary',
            'typography.body_font'       => 'font_body',
            'typography.body_font_size'  => 'font_body_size',
            'typography.body_font_height'=> 'font_body_height',
            'typography.heading_font'    => 'font_display',
            'buttons.background'    => 'color_accent',
            'buttons.text_color'    => 'button_text_color',
            'buttons.border_radius' => 'button_border_radius',
        ];

        $fallback = [
            'palette.secondary' => '#D4A747',
            'palette.text'      => '#001338',
            'palette.header'    => '#001338',
            'typography.body_font'       => 'DM Sans',
            'typography.body_font_size'  => '16px',
            'typography.body_font_height'=> '1.65',
            'typography.heading_font'    => 'Playfair Display',
            'buttons.background'    => '#DC2626',
            'buttons.text_color'    => '#FFFFFF',
            'buttons.border_radius' => '50',
        ];

        $this->brand_defaults = [];
        foreach ($translation as $composite => $source_key) {
            [$group, $local_name] = explode('.', $composite, 2);
            $val = $defaults[$source_key] ?? $fallback[$composite] ?? null;
            if ($val !== null) {
                $this->brand_defaults[$group][$local_name] = $val;
            }
        }
    }

    /** @deprecated Usar brand-sync.php en lugar de DESIGN.md */
    public function apply_design_file( string $filepath ): array {
        if ( ! file_exists( $filepath ) ) return [ 'success' => false, 'error' => "DESIGN.md not found" ];
        $content = file_get_contents( $filepath );
        $design = $this->parse_design_md( $content );
        return $this->apply_design( $design );
    }

    /** @deprecated Usar brand-sync.php en lugar de DESIGN.md */
    public function apply_design( array $design ): array {
        $applied = [];

        foreach ( $design as $section => $tokens ) {
            if ( isset( $this->token_map[$section] ) ) {
                foreach ( $this->token_map[$section] as $token_key => $option_name ) {
                    if ( $option_name === null ) continue;
                    if ( isset( $tokens[$token_key] ) ) {
                        et_update_option( $option_name, $tokens[$token_key] );
                        $applied[] = "et_divi.{$option_name}";
                    }
                }
            }
            if ( $section === 'custom_css' && isset($tokens['css']) ) {
                if ( function_exists( 'wp_update_custom_css_post' ) ) {
                    wp_update_custom_css_post( $tokens['css'] );
                }
                $applied[] = 'custom_css';
            }
        }

        $this->clear_cache();
        return [ 'success' => true, 'applied' => $applied, 'count' => count($applied) ];
    }

    public function apply_brand_defaults(): array {
        return $this->apply_design( $this->brand_defaults );
    }

    public function set_global_colors( array $colors ): array {
        $divi = get_option( 'et_divi', [] );
        $globals = $divi['global_colors'] ?? [];
        $applied = [];

        foreach ( $colors as $slug => $value ) {
            $found = false;
            foreach ( $globals as &$gc ) {
                if ( isset( $gc['slug'] ) && $gc['slug'] === $slug ) {
                    $gc['value'] = $value;
                    $found = true;
                    $applied[] = "global_color.{$slug}";
                    break;
                }
            }
            if ( ! $found ) {
                $globals[] = [
                    'slug'  => $slug,
                    'value' => $value,
                    'label' => ucwords( str_replace( '_', ' ', $slug ) ),
                ];
                $applied[] = "global_color.{$slug} (created)";
            }
        }

        $divi['global_colors'] = $globals;
        update_option( 'et_divi', $divi );
        $this->clear_cache();
        return [ 'success' => true, 'applied' => $applied, 'count' => count($applied) ];
    }

    public function get_global_colors(): array {
        $divi = get_option( 'et_divi', [] );
        return $divi['global_colors'] ?? [];
    }

    public function resolve_token( string $token ): string {
        $divi = get_option( 'et_divi', [] );

        $globals = $divi['global_colors'] ?? [];
        foreach ( $globals as $gc ) {
            if ( ( $gc['slug'] ?? '' ) === $token ) {
                return $gc['value'];
            }
        }

        $fallback = [
            'bg_deep'    => '#001338',
            'bg_cream'   => '#FAF8F5',
            'bg_white'   => '#FFFFFF',
            'accent'     => '#DC2626',
            'gold'       => '#D4A747',
            'text_body'  => '#475569',
            'text_dark'  => '#001338',
            'radius'     => '8px',
            'radius_pill'=> '50px',
            'display'    => '"Playfair Display", Georgia, serif',
            'ui'         => '"DM Sans", system-ui, sans-serif',
        ];

        return $fallback[$token] ?? $token;
    }

    public function resolve_tokens_in_string( string $content ): string {
        return preg_replace_callback( '/\{\{token:([a-zA-Z_]+)\}\}/', function( $m ) {
            return $this->resolve_token( $m[1] );
        }, $content );
    }

    private function parse_design_md( string $content ): array {
        $design = [];
        $lines = explode("\n", $content);
        $section = '';
        $in_code = false;
        $code_type = '';
        $code_body = '';

        foreach ( $lines as $line ) {
            $trimmed = trim( $line );
            if ( str_starts_with( $trimmed, '```' ) ) {
                if ( $in_code ) {
                    if ( $code_type === 'css' ) $design['custom_css']['css'] = trim( $code_body );
                    $in_code = false;
                    $code_body = '';
                } else {
                    $in_code = true;
                    $code_type = substr( $trimmed, 3 );
                }
                continue;
            }
            if ( $in_code ) { $code_body .= $line . "\n"; continue; }
            if ( str_starts_with( $trimmed, '## ' ) ) {
                $section = strtolower( trim( substr( $trimmed, 3 ) ) );
                continue;
            }
            if ( str_starts_with( $trimmed, '- ' ) && $section ) {
                $item = substr( $trimmed, 2 );
                $parts = explode( ':', $item, 2 );
                if ( count( $parts ) === 2 ) {
                    $design[$section][ trim( $parts[0] ) ] = trim( $parts[1], " '\"" );
                }
            }
        }
        return $design;
    }

    private function clear_cache(): void {
        if ( function_exists( 'et_core_clear_wp_cache' ) ) {
            et_core_clear_wp_cache();
        }
        delete_option( 'et_pb_css_synced' );
    }
}
