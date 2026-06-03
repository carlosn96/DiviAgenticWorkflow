<?php
namespace DAC\Core;

class Page_Brain {

    private \DAC\Core\AI_Bridge $ai_bridge;
    private array $context_data = [];

    public function __construct( array $context_data = [] ) { 
        $this->ai_bridge = new \DAC\Core\AI_Bridge(); 
        $this->context_data = $context_data;
    }

    public function build( string $prompt, array $overrides = [], string $brief_path = '' ): array {
        if ( $brief_path && file_exists( $brief_path ) ) { $this->load_brief_to_context( $brief_path ); }
        $pattern = $this->detect( strtolower( $prompt ) );
        
        $blueprint = $this->load_blueprint( $pattern );
        return $this->compile_node( $blueprint );
    }

    public static function presets(): array {
        return [
            'hero' => [ 'spacing' => [ 'padding' => [ 'top' => '120px', 'bottom' => '120px' ] ], 'background' => [ 'color' => '{{brand.theme.bg_deep_token}}' ], 'layout' => [ 'width' => '100%' ] ],
            'card' => [ 'background' => [ 'color' => '#ffffff' ], 'border' => [ 'radius' => [ 'topLeft' => '12px', 'topRight' => '12px', 'bottomLeft' => '12px', 'bottomRight' => '12px' ], 'width' => [ 'top' => '1px', 'right' => '1px', 'bottom' => '1px', 'left' => '1px' ], 'color' => [ 'top' => 'rgba(0,0,0,0.05)', 'right' => 'rgba(0,0,0,0.05)', 'bottom' => 'rgba(0,0,0,0.05)', 'left' => 'rgba(0,0,0,0.05)' ] ], 'boxShadow' => [ 'style' => 'preset1', 'horizontal' => '0px', 'vertical' => '10px', 'blur' => '30px', 'spread' => '0px', 'color' => 'rgba(0,33,71,0.08)' ], 'spacing' => [ 'padding' => [ 'top' => '32px', 'right' => '32px', 'bottom' => '32px', 'left' => '32px' ] ] ],
            'glass' => [ 'background' => [ 'color' => 'rgba(255,255,255,0.03)' ], 'border' => [ 'radius' => [ 'topLeft' => '16px', 'topRight' => '16px', 'bottomLeft' => '16px', 'bottomRight' => '16px' ], 'width' => [ 'top' => '1px', 'right' => '1px', 'bottom' => '1px', 'left' => '1px' ], 'color' => [ 'top' => 'rgba(255,255,255,0.1)', 'right' => 'rgba(255,255,255,0.1)', 'bottom' => 'rgba(255,255,255,0.1)', 'left' => 'rgba(255,255,255,0.1)' ] ], 'filters' => [ 'blur' => '15px', 'saturate' => '150%' ] ],
        ];
    }

    public static function decoration_schema(): array {
        return [
            'layout' => [ 'width' => '', 'flexWrap' => '' ],
            'background' => [ 'color' => '', 'gradient' => [ 'type' => 'linear', 'direction' => '180deg', 'colorOne' => '', 'colorTwo' => '' ], 'image' => [ 'url' => '', 'size' => 'cover', 'position' => 'center', 'repeat' => 'no-repeat', 'blend' => 'normal' ] ],
            'border' => [ 'width' => [ 'top' => '', 'right' => '', 'bottom' => '', 'left' => '' ], 'color' => [ 'top' => '', 'right' => '', 'bottom' => '', 'left' => '' ], 'style' => [ 'top' => 'solid', 'right' => 'solid', 'bottom' => 'solid', 'left' => 'solid' ], 'radius' => [ 'topLeft' => '', 'topRight' => '', 'bottomLeft' => '', 'bottomRight' => '' ] ],
            'boxShadow' => [ 'style' => 'none', 'horizontal' => '0px', 'vertical' => '0px', 'blur' => '0px', 'spread' => '0px', 'color' => 'rgba(0,0,0,0.3)' ],
            'spacing' => [ 'padding' => [ 'top' => '', 'right' => '', 'bottom' => '', 'left' => '' ], 'margin' => [ 'top' => '', 'right' => '', 'bottom' => '', 'left' => '' ] ],
            'sizing' => [ 'width' => '', 'height' => '', 'maxWidth' => '', 'flexType' => '', 'minHeight' => '' ],
            'filters' => [ 'saturate' => '100%', 'brightness' => '100%', 'contrast' => '100%', 'opacity' => '100%', 'blur' => '0px' ],
        ];
    }

    // ─── ENGINE CORE ────────────────────────────────────────────────
    private function load_brief_to_context( string $path ): void {
        $content = file_get_contents( $path );
        if ( ! $content ) return;
        if ( preg_match( '/\*\*H1\*\*:\s*(.+)/', $content, $m ) ) $this->context_data['content']['landing']['hero_title'] = trim( $m[1] );
        if ( preg_match_all( '/\*\*H2[^*]*\*\*:\s*(.+)/', $content, $m ) ) $this->context_data['content']['landing']['section_titles'] = array_map( 'trim', $m[1] );
    }

    private function detect( string $text ): string {
        $map = [
            'landing'    => ['landing','home','inicio','portada','principal','instituto'],
            'service'    => ['admisiones','inscripcion','becas','costos','requisitos'],
            'collection' => ['oferta','talleres','programas','materias','bachillerato','plan'],
            'about'      => ['nosotros','historia','mision','vision','valores','identidad'],
            'instalaciones' => ['instalaciones','campus','laboratorios','instalacion','espacios','mapa'],
            'gallery'    => ['galeria','fotos','imagenes','recorrido','album'],
            'perfil'     => ['perfil','ingreso','egreso','prospecto','transformación'],
            'contact'    => ['contacto','contact','ubicacion','mapa','direccion','horario'],
        ];
        $best = 'landing'; $high = 0;
        foreach ( $map as $key => $kws ) {
            $s = 0;
            foreach ( $kws as $kw ) { if ( strpos( $text, $kw ) !== false ) $s++; }
            if ( $s > $high ) { $high = $s; $best = $key; }
        }
        return $best;
    }

    private function load_blueprint( string $pattern ): array {
        $path = __DIR__ . "/blueprints/{$pattern}.json";
        if ( ! file_exists( $path ) ) {
            $path = __DIR__ . "/blueprints/landing.json";
        }
        
        if ( file_exists( $path ) ) {
            return json_decode( file_get_contents( $path ), true ) ?? [];
        }
        return ['sections' => [], '_meta' => ['pattern' => 'missing_fallback']];
    }

    private function compile_node( $node ) {
        if ( is_string( $node ) ) return $this->interpolate( $node );
        
        if ( is_array( $node ) ) {
            $compiled = [];
            foreach ( $node as $key => $value ) {
                $compiled[$key] = $this->compile_node( $value );
            }
            return $compiled;
        }
        
        return $node;
    }

    private function interpolate( string $string ): string {
        return preg_replace_callback('/\{\{([\w\.]+)\}\}/', function( $matches ) {
            $path = explode('.', $matches[1]);
            $value = $this->context_data;
            
            foreach ( $path as $key ) {
                if ( is_array($value) && isset( $value[$key] ) ) {
                    $value = $value[$key];
                } else {
                    return $matches[0];
                }
            }
            
            return is_scalar($value) ? $value : $matches[0];
        }, $string);
    }
}