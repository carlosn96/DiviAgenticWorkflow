<?php
namespace DAC\Core;

class AI_Bridge {

    public function generate_tokens( string $query ): array {
        return $this->local_generator( $query );
    }

    private function local_generator( string $query ): array {
        $query_lower = strtolower( $query );

        $tokens = [
            'colors' => [
                'primary'    => '#DC2626',
                'secondary'  => '#D4A747',
                'accent'     => '#DC2626',
                'background' => '#FAF8F5',
                'bg_deep'    => '#001338',
                'text'       => '#001338',
            ],
            'typography' => [
                'heading' => 'Playfair Display',
                'body'    => 'DM Sans',
            ],
            'style' => [
                'radius'         => '8px',
                'radius_button'  => '50px',
                'shadow'         => 'subtle',
            ]
        ];

        if ( strpos( $query_lower, 'dark' ) !== false || strpos( $query_lower, 'oscuro' ) !== false ) {
            $tokens['colors']['background'] = '#001338';
            $tokens['colors']['text']       = '#FFFFFF';
        }

        if ( strpos( $query_lower, 'modern' ) !== false || strpos( $query_lower, 'vanguardia' ) !== false ) {
            $tokens['style']['radius'] = '12px';
        }

        return [
            'success' => true,
            'tokens'  => $tokens,
            'source'  => 'irlv-internal-engine'
        ];
    }

    public function tokens_to_design( array $tokens ): array {
        $c = $tokens['colors'];
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
                'content_width'  => 1600,
                'fixed_nav'      => 'on',
            ],
            'performance' => [
                'dynamic_framework' => 'on',
                'dynamic_icons'     => 'on',
                'critical_css'      => 'on',
            ],
        ];
    }
}
