<?php
namespace DAC\Core;

class Page_Brain {

    private \DAC\Core\AI_Bridge $ai_bridge;
    private array $brief_context = [];

    public function __construct() { $this->ai_bridge = new \DAC\Core\AI_Bridge(); }

    public function build( string $prompt, array $overrides = [], string $brief_path = '' ): array {
        if ( $brief_path && file_exists( $brief_path ) ) { $this->load_brief( $brief_path ); }
        $pattern = $this->detect( strtolower( $prompt ) );
        $method  = "blueprint_{$pattern}";
        return method_exists( $this, $method ) ? $this->$method( $prompt, [] ) : $this->blueprint_landing( $prompt, [] );
    }

    public static function presets(): array {
        return [
            'hero' => [ 'spacing' => [ 'padding' => [ 'top' => '120px', 'bottom' => '120px' ] ], 'background' => [ 'color' => '{{token:bg_deep}}' ], 'layout' => [ 'width' => '100%' ] ],
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

    // ─── HELPERS ────────────────────────────────────────────────────
    private function load_brief( string $path ): void {
        $content = file_get_contents( $path );
        if ( ! $content ) return;
        if ( preg_match( '/\*\*H1\*\*:\s*(.+)/', $content, $m ) ) $this->brief_context['hero_title'] = trim( $m[1] );
        if ( preg_match_all( '/\*\*H2[^*]*\*\*:\s*(.+)/', $content, $m ) ) $this->brief_context['section_titles'] = array_map( 'trim', $m[1] );
    }

    private function detect( string $text ): string {
        $map = [
            'landing'    => ['landing','home','inicio','portada','principal','instituto'],
            'service'    => ['admisiones','inscripcion','becas','costos','requisitos'],
            'collection' => ['oferta','talleres','programas','materias','bachillerato','plan'],
            'about'      => ['nosotros','historia','mision','vision','valores','identidad'],
            'instalaciones' => ['instalaciones','campus','laboratorios','instalacion','espacios','mapa'],
            'gallery'    => ['galeria','fotos','imagenes','recorrido','album'],
            'perfil'     => ['perfil','ingreso','egreso','prospecto','transformacion'],
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

    private function section( array $rows, array $decoration = [], string $type = 'regular' ): array {
        $s = [ 'type' => $type, 'rows' => $rows ];
        if ( isset( $decoration['module_class'] ) ) { $s['module_class'] = $decoration['module_class']; unset( $decoration['module_class'] ); }
        if ( isset( $decoration['admin_label'] ) ) { $s['admin_label'] = $decoration['admin_label']; unset( $decoration['admin_label'] ); }
        if ( $decoration ) { $s['decoration'] = $decoration; }
        return $s;
    }

    private function row( string $cols, array $columns ): array { return [ 'column_structure' => $cols, 'columns' => $columns ]; }
    private function col( array $modules, string $type = '' ): array { return [ 'modules' => $modules, 'type' => $type ?: '4_4' ]; }
    private function mod( string $name, array $attrs = [] ): array { return array_merge( [ 'module' => $name ], $attrs ); }
    private function spacing( int $v = 80 ): array { return [ 'spacing' => [ 'padding' => [ 'top' => "{$v}px", 'right' => '0px', 'bottom' => "{$v}px", 'left' => '0px' ] ] ]; }

    private function image_card( string $label, string $alt, string $badge = '', string $desc = '' ): array {
        $html = '<div style="padding:0;overflow:hidden;border-radius:16px"><img src="/wp-content/uploads/2026/05/RLV-980x376.avif" alt="' . $alt . '" style="width:100%;height:200px;object-fit:cover;display:block"><div style="padding:20px">';
        if ( $badge ) $html .= '<span style="display:inline-block;background:var(--gold-soft);color:var(--gold);font-size:0.7rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;padding:4px 12px;border-radius:20px;margin-bottom:8px">' . $badge . '</span>';
        $html .= '<h3 style="font-family:var(--display);margin:0 0 6px;font-size:1.2rem">' . $label . '</h3>';
        if ( $desc ) $html .= '<p style="font-size:0.9rem;color:var(--text-secondary);margin:0;line-height:1.6">' . $desc . '</p>';
        $html .= '</div></div>';
        return $this->mod( 'divi/text', [ 'content' => $html, 'module_class' => 'sp5-card', 'preset' => 'card' ] );
    }

    // ═══════════════════════════════════════════════════════════════
    //  BLUEPRINTS
    // ═══════════════════════════════════════════════════════════════

    private function blueprint_landing( string $prompt, array $tokens ): array {
        return [ 'sections' => [
            $this->section( [ $this->row( '4_4', [ $this->col( [
                $this->mod( 'divi/text', [ 'content' => '<p class="sp5-eyebrow">Bachillerato General · Incorporado a la SEP</p>', 'module_class' => 'sp5-eyebrow sp5-fade-up-d1' ] ),
                $this->mod( 'divi/text', [ 'content' => '<h1 class="sp5-display">Formaci&oacute;n que impulsa tu futuro <br><em>acad&eacute;mico y personal</em></h1>', 'module_class' => 'sp5-display sp5-fade-up-d2' ] ),
                $this->mod( 'divi/text', [ 'content' => '<p class="sp5-lead">En Preparatoria Ram&oacute;n L&oacute;pez Velarde desarrollas conocimientos, habilidades y valores en un entorno que inspira crecimiento, liderazgo y preparaci&oacute;n universitaria.</p>', 'module_class' => 'sp5-lead sp5-fade-up-d3' ] ),
                $this->mod( 'divi/button', [ 'button_text' => 'QUIERO INSCRIBIRME', 'button_url' => '/admisiones', 'module_class' => 'et_pb_button sp5-btn-primary' ] ),
            ] )] )], [ 'background' => [ 'color' => '{{token:bg_deep}}' ], 'spacing' => [ 'padding' => [ 'top' => '120px', 'bottom' => '80px' ] ], 'module_class' => 'sp5-dark sp5-fade-up' ] ),
        ], '_meta' => [ 'pattern' => 'Landing', 'prompt' => $prompt ] ];
    }

    private function blueprint_gallery( string $prompt, array $tokens ): array {
        $s = [];
        $hero = $this->brief_context['hero_title'] ?? 'Galeria Institucional';
        $s[] = $this->section( [ $this->row( '4_4', [ $this->col( [
            $this->mod( 'divi/text', [ 'content' => '<p class="sp5-eyebrow">GALERIA</p>', 'module_class' => 'sp5-eyebrow sp5-fade-up-d1' ] ),
            $this->mod( 'divi/text', [ 'content' => '<h1 class="sp5-display">' . $hero . '</h1>', 'module_class' => 'sp5-display-red sp5-fade-up-d2' ] ),
            $this->mod( 'divi/text', [ 'content' => '<p class="sp5-lead">Imagenes que capturan la esencia de nuestra comunidad educativa.</p>', 'module_class' => 'sp5-lead sp5-fade-up-d3' ] ),
            $this->mod( 'divi/text', [ 'content' => '<div class="sp5-accent-line"></div>', 'module_class' => '' ] ),
        ] )] )], [ 'background' => [ 'color' => '{{token:bg_deep}}' ], 'spacing' => [ 'padding' => [ 'top' => '120px', 'bottom' => '80px' ] ], 'module_class' => 'sp5-dark sp5-fade-up' ] );
        $s[] = $this->section( [ $this->row( '4_4', [ $this->col( [
            $this->mod( 'divi/text', [ 'content' => '<p style="text-align:center"><span class="sp5-eyebrow">RECORRIDO</span></p><h2 class="sp5-headline" style="text-align:center">Nuestro Campus en Imagenes</h2>', 'module_class' => 'sp5-section-title' ] ),
        ] )] )], $this->spacing(80) );
        $s[] = $this->section( [ $this->row( '4_4', [ $this->col( [
            $this->mod( 'divi/gallery', [ 'gallery_ids' => '355,275,211,209,210,207,208,59,58,18', 'columns' => 3, 'admin_label' => 'Galeria Grid', 'module_class' => 'sp5-campus-gallery' ] ),
        ] )] )], [ 'spacing' => [ 'padding' => [ 'bottom' => '80px' ] ], 'module_class' => 'sp5-light' ] );
        $s[] = $this->section( [ $this->row( '4_4', [ $this->col( [
            $this->mod( 'divi/text', [ 'content' => '<h2 style="text-align:center;color:#ffffff">Visitanos y Conocenos</h2><p class="sp5-lead" style="text-align:center;color:rgba(255,255,255,0.7);margin-bottom:32px">Te invitamos a recorrer personalmente nuestras instalaciones.</p>', 'module_class' => 'sp5-center' ] ),
            $this->mod( 'divi/code', [ 'content' => "<div style='display:flex;gap:16px;justify-content:center;flex-wrap:wrap;'><a href='/contacto' class='et_pb_button sp5-btn-primary' style='margin:0;'>Agenda una Visita</a><a href='/nosotros-instalaciones' class='et_pb_button sp5-btn-ghost-light' style='margin:0;'>Ver Instalaciones</a></div>" ] ),
        ] )] )], [ 'background' => [ 'color' => '{{token:bg_deep}}' ], 'spacing' => [ 'padding' => [ 'top' => '80px', 'bottom' => '80px' ] ], 'module_class' => 'sp5-dark' ] );
        return [ 'sections' => $s, '_meta' => [ 'pattern' => 'Galeria', 'prompt' => $prompt ] ];
    }

    private function blueprint_instalaciones( string $prompt, array $tokens ): array {
        $s = [];
        $hero = $this->brief_context['hero_title'] ?? 'Instalaciones de Nivel Universitario';
        $s[] = $this->section( [ $this->row( '4_4', [ $this->col( [
            $this->mod( 'divi/text', [ 'content' => '<p class="sp5-eyebrow">Infraestructura de Vanguardia</p>', 'module_class' => 'sp5-eyebrow sp5-fade-up-d1' ] ),
            $this->mod( 'divi/text', [ 'content' => '<h1 class="sp5-display">' . $hero . '</h1>', 'module_class' => 'sp5-display-red sp5-fade-up-d2' ] ),
            $this->mod( 'divi/text', [ 'content' => '<p class="sp5-lead">Disenados para inspirar la creatividad y la cultura de la comunicacion.</p>', 'module_class' => 'sp5-lead sp5-fade-up-d3' ] ),
            $this->mod( 'divi/text', [ 'content' => '<div class="sp5-accent-line"></div>', 'module_class' => '' ] ),
        ] )] )], [ 'background' => [ 'color' => '{{token:bg_deep}}' ], 'spacing' => [ 'padding' => [ 'top' => '120px', 'bottom' => '80px' ] ], 'module_class' => 'sp5-dark sp5-fade-up' ] );
        return [ 'sections' => $s, '_meta' => [ 'pattern' => 'Instalaciones', 'prompt' => $prompt ] ];
    }

    private function blueprint_perfil( string $prompt, array $tokens ): array {
        $s = [];
        $hero = $this->brief_context['hero_title'] ?? 'Perfiles de Ingreso y Egreso';
        $s[] = $this->section( [ $this->row( '4_4', [ $this->col( [
            $this->mod( 'divi/text', [ 'content' => '<p class="sp5-eyebrow">Tu Proyecto de Vida</p>', 'module_class' => 'sp5-eyebrow sp5-fade-up-d1' ] ),
            $this->mod( 'divi/text', [ 'content' => '<h1 class="sp5-display">' . $hero . '</h1>', 'module_class' => 'sp5-display-red sp5-fade-up-d2' ] ),
            $this->mod( 'divi/text', [ 'content' => '<p class="sp5-lead">El camino de transformacion desde el primer dia hasta tu exito profesional.</p>', 'module_class' => 'sp5-lead sp5-fade-up-d3' ] ),
            $this->mod( 'divi/text', [ 'content' => '<div class="sp5-accent-line"></div>', 'module_class' => '' ] ),
        ] )] )], [ 'background' => [ 'color' => '{{token:bg_deep}}' ], 'spacing' => [ 'padding' => [ 'top' => '120px', 'bottom' => '80px' ] ], 'module_class' => 'sp5-dark sp5-fade-up' ] );
        return [ 'sections' => $s, '_meta' => [ 'pattern' => 'Perfil', 'prompt' => $prompt ] ];
    }

    private function blueprint_contact( string $prompt, array $tokens ): array {
        $s = [];
        $s[] = $this->section( [ $this->row( '4_4', [ $this->col( [
            $this->mod( 'divi/text', [ 'content' => '<p class="sp5-eyebrow">Comunicate con Nosotros</p>', 'module_class' => 'sp5-eyebrow sp5-fade-up-d1' ] ),
            $this->mod( 'divi/text', [ 'content' => '<h1 class="sp5-display">Contacto</h1>', 'module_class' => 'sp5-display-red sp5-fade-up-d2' ] ),
            $this->mod( 'divi/text', [ 'content' => '<p class="sp5-lead">Estamos para servirte y resolver tus dudas.</p>', 'module_class' => 'sp5-lead sp5-fade-up-d3' ] ),
            $this->mod( 'divi/text', [ 'content' => '<div class="sp5-accent-line"></div>', 'module_class' => '' ] ),
        ] )] )], [ 'background' => [ 'color' => '{{token:bg_deep}}' ], 'spacing' => [ 'padding' => [ 'top' => '120px', 'bottom' => '80px' ] ], 'module_class' => 'sp5-dark sp5-fade-up' ] );
        return [ 'sections' => $s, '_meta' => [ 'pattern' => 'Contacto', 'prompt' => $prompt ] ];
    }

    private function blueprint_collection( string $prompt, array $tokens ): array {
        $s = [];
        $s[] = $this->section( [ $this->row( '4_4', [ $this->col( [
            $this->mod( 'divi/text', [ 'content' => '<p class="sp5-eyebrow">Oferta Educativa</p>', 'module_class' => 'sp5-eyebrow sp5-fade-up-d1' ] ),
            $this->mod( 'divi/text', [ 'content' => '<h1 class="sp5-display">Planes de Estudio<br><em>de Alta Calidad</em></h1>', 'module_class' => 'sp5-display-red sp5-fade-up-d2' ] ),
            $this->mod( 'divi/text', [ 'content' => '<p class="sp5-lead">Descubre los programas academicos que preparamos para ti.</p>', 'module_class' => 'sp5-lead sp5-fade-up-d3' ] ),
        ] )] )], [ 'background' => [ 'color' => '{{token:bg_deep}}' ], 'spacing' => [ 'padding' => [ 'top' => '120px', 'bottom' => '80px' ] ], 'module_class' => 'sp5-dark sp5-fade-up' ] );
        return [ 'sections' => $s, '_meta' => [ 'pattern' => 'Coleccion', 'prompt' => $prompt ] ];
    }

    private function blueprint_service( string $prompt, array $tokens ): array {
        $hero = $this->brief_context['hero_title'] ?? 'Tu Futuro Comienza Aqui';
        return [ 'sections' => [
            $this->section( [ $this->row( '4_4', [ $this->col( [
                $this->mod( 'divi/text', [ 'content' => '<p class="sp5-eyebrow">Admisiones 2026</p>', 'module_class' => 'sp5-eyebrow sp5-fade-up-d1' ] ),
                $this->mod( 'divi/text', [ 'content' => '<h1 class="sp5-display">' . $hero . '</h1>', 'module_class' => 'sp5-display-red sp5-fade-up-d2' ] ),
                $this->mod( 'divi/text', [ 'content' => '<p class="sp5-lead">Asegura tu lugar en la institucion que ha formado lideres por generaciones.</p>', 'module_class' => 'sp5-lead sp5-fade-up-d3' ] ),
                $this->mod( 'divi/button', [ 'button_text' => 'Inicia tu Proceso', 'button_url' => '#', 'module_class' => 'et_pb_button sp5-btn-primary' ] ),
            ] )] )], [ 'background' => [ 'color' => '{{token:bg_deep}}' ], 'spacing' => [ 'padding' => [ 'top' => '120px', 'bottom' => '80px' ] ], 'module_class' => 'sp5-dark sp5-fade-up' ] ),
        ], '_meta' => [ 'pattern' => 'Admisiones', 'prompt' => $prompt ] ];
    }
}

