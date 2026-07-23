<?php
namespace DAC\Core;

class AI_Bridge {

    public function generate_tokens( string $query ): array {
        return $this->local_generator( $query );
    }

    private function local_generator( string $query ): array {
        $query_lower = strtolower( $query );
        $d = Token_Registry::get_defaults();

        $tokens = [
            'colors' => [
                'primary'    => $d['color_accent'] ?? '#DC2626',
                'secondary'  => $d['color_text_secondary'] ?? '#D4A747',
                'accent'     => $d['color_accent'] ?? '#DC2626',
                'background' => $d['color_surface_light'] ?? '#FAF8F5',
                'bg_deep'    => $d['color_surface_deep'] ?? '#001338',
                'text'       => $d['color_text_primary'] ?? '#001338',
            ],
            'typography' => [
                'heading' => $d['font_display'] ?? 'Playfair Display',
                'body'    => $d['font_body'] ?? 'DM Sans',
            ],
            'style' => [
                'radius'         => $d['radius_md'] ?? '8px',
                'radius_button'  => $d['radius_full'] ?? '50px',
                'shadow'         => 'subtle',
            ]
        ];

        if ( strpos( $query_lower, 'dark' ) !== false || strpos( $query_lower, 'oscuro' ) !== false ) {
            $tokens['colors']['background'] = $d['color_surface_deep'] ?? '#001338';
            $tokens['colors']['text']       = $d['color_text_on_dark'] ?? '#FFFFFF';
        }

        if ( strpos( $query_lower, 'modern' ) !== false || strpos( $query_lower, 'vanguardia' ) !== false ) {
            $tokens['style']['radius'] = $d['radius_lg'] ?? '12px';
        }

        return [
            'success' => true,
            'tokens'  => $tokens,
            'source'  => 'irlv-internal-engine'
        ];
    }

    public function tokens_to_design( array $tokens ): array {
        $c = $tokens['colors'];
        $d = Token_Registry::get_defaults();
        return [
            'palette' => [
                'primary'        => $c['primary'],
                'secondary'      => $c['secondary'],
                'accent'         => $c['accent'],
                'background'     => $c['background'],
                'text'           => $c['text'],
            ],
            'typography' => [
                'body_font'      => $tokens['typography']['body'],
                'heading_font'   => $tokens['typography']['heading'],
            ],
            'buttons' => [
                'background'     => $c['primary'],
                'border_radius'  => $tokens['style']['radius_button'],
                'text_color'     => '#FFFFFF',
            ],
            'layout' => [
                'content_width'  => (int)($d['layout_content_width'] ?? '1200px'),
                'fixed_nav'      => $d['layout_fixed_nav'] ?? 'on',
            ],
            'performance' => [
                'dynamic_framework' => $d['perf_dynamic_framework'] ?? 'on',
                'dynamic_icons'     => $d['perf_dynamic_icons'] ?? 'on',
                'critical_css'      => $d['perf_critical_css'] ?? 'on',
            ],
        ];
    }
}
