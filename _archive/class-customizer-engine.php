<?php
namespace DAC\Core;

class Customizer_Engine {

    private array $token_map = [
        'palette' => [
            'primary'        => 'accent_color',
            'secondary'      => 'secondary_accent_color',
            'text'           => 'font_color',
            'header'         => 'header_color',
            'background'     => null,
            'link'           => null,
        ],
        'typography' => [
            'body_font'          => 'body_font',
            'body_font_size'     => 'body_font_size',
            'body_font_height'   => 'body_font_height',
            'body_font_weight'   => 'body_font_weight',
            'heading_font'       => 'heading_font',
            'heading_font_weight'=> 'heading_font_weight',
        ],
        'buttons' => [
            'background'        => 'all_buttons_bg_color',
            'background_hover'  => 'all_buttons_bg_color_hover',
            'text_color'        => 'all_buttons_text_color',
            'text_color_hover'  => 'all_buttons_text_color_hover',
            'border_radius'     => 'all_buttons_border_radius',
            'border_width'      => 'all_buttons_border_width',
            'border_color'      => 'all_buttons_border_color',
            'font_size'         => 'all_buttons_font_size',
            'font_style'        => 'all_buttons_font_style',
        ],
        'layout' => [
            'content_width'     => 'content_width',
            'fixed_nav'         => 'divi_fixed_nav',
            'sidebar'           => 'divi_sidebar',
        ],
        'performance' => [
            'dynamic_framework' => 'divi_dynamic_module_framework',
            'dynamic_icons'     => 'divi_dynamic_icons',
            'critical_css'      => 'divi_critical_css',
            'defer_block_css'   => 'divi_defer_block_css',
            'jquery_body'       => 'divi_enable_jquery_body',
            'disable_emojis'    => 'divi_disable_emojis',
        ],
    ];

    private array $brand_defaults = [
        'palette' => [
            'primary'   => '#DC2626',
            'secondary' => '#D4A747',
            'text'      => '#001338',
            'header'    => '#001338',
        ],
        'typography' => [
            'body_font'       => 'DM Sans',
            'body_font_size'  => '16px',
            'body_font_height'=> '1.65',
            'heading_font'    => 'Playfair Display',
        ],
        'buttons' => [
            'background'    => '#DC2626',
            'text_color'    => '#FFFFFF',
            'border_radius' => '50',
        ],
    ];

    public function apply_design_file( string $filepath ): array {
        if ( ! file_exists( $filepath ) ) return [ 'success' => false, 'error' => "DESIGN.md not found" ];
        $content = file_get_contents( $filepath );
        $design = $this->parse_design_md( $content );
        return $this->apply_design( $design );
    }

    public function apply_design( array $design ): array {
        $divi_opts = get_option( 'et_divi', [] );
        $applied = [];

        foreach ( $design as $section => $tokens ) {
            if ( isset( $this->token_map[$section] ) ) {
                foreach ( $this->token_map[$section] as $token_key => $option_name ) {
                    if ( $option_name === null ) continue;
                    if ( isset( $tokens[$token_key] ) ) {
                        $divi_opts[$option_name] = $tokens[$token_key];
                        $applied[] = "et_divi.{$option_name}";
                    }
                }
            }
            if ( $section === 'custom_css' && isset($tokens['css']) ) {
                $divi_opts['divi_custom_css'] = $tokens['css'];
                if ( function_exists( 'wp_update_custom_css_post' ) ) {
                    wp_update_custom_css_post( $tokens['css'] );
                }
                $applied[] = 'custom_css';
            }
        }

        update_option( 'et_divi', $divi_opts );
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
