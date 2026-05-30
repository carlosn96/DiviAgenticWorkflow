<?php
namespace DAC\Core;

/**
 * UX_Engine v3.0 — El Cerebro de Diseño Absorbido.
 * 
 * Replica la lógica de razonamiento y generación de sistemas de diseño 
 * de UI/UX Pro Max de forma nativa en PHP.
 */
class UX_Engine {

    private $db_path;
    private $reasoning_data = [];

    public function __construct() {
        $this->db_path = get_stylesheet_directory() . '/inc/core/intelligence/db/';
        $this->load_reasoning();
    }

    private function load_reasoning() {
        $file = $this->db_path . 'ui-reasoning.csv';
        if ( file_exists( $file ) ) {
            if ( ( $handle = fopen( $file, "r" ) ) !== FALSE ) {
                $headers = fgetcsv( $handle, 1000, "," );
                while ( ( $data = fgetcsv( $handle, 1000, "," ) ) !== FALSE ) {
                    $this->reasoning_data[] = array_combine( $headers, $data );
                }
                fclose( $handle );
            }
        }
    }

    /**
     * Aplica lógica de razonamiento para encontrar la mejor estrategia.
     */
    public function get_reasoning( string $category ): array {
        $category_lower = strtolower( $category );
        foreach ( $this->reasoning_data as $rule ) {
            $ui_cat = strtolower( $rule['UI_Category'] ?? '' );
            if ( strpos( $category_lower, $ui_cat ) !== false || strpos( $ui_cat, $category_lower ) !== false ) {
                return $rule;
            }
        }
        return [];
    }

    /**
     * Realiza una búsqueda avanzada con scoring BM25 (simplificado).
     */
    public function search( string $query, string $domain = 'products' ): array {
        $file = $this->db_path . $domain . '.csv';
        if ( ! file_exists( $file ) ) return [];

        $results = [];
        $keywords = explode( ' ', strtolower( $query ) );
        
        if ( ( $handle = fopen( $file, "r" ) ) !== FALSE ) {
            $headers = fgetcsv( $handle, 1000, "," );
            while ( ( $data = fgetcsv( $handle, 1000, "," ) ) !== FALSE ) {
                if ( count($headers) !== count($data) ) continue;
                $row = array_combine( $headers, $data );
                $score = 0;
                
                $content = strtolower( implode( ' ', $data ) );
                foreach ( $keywords as $kw ) {
                    if ( strpos( $content, trim( $kw ) ) !== false ) $score += 10;
                }
                
                if ( $score > 0 ) {
                    $row['_score'] = $score;
                    $results[] = $row;
                }
            }
            fclose( $handle );
        }

        usort( $results, function( $a, $b ) { return $b['_score'] <=> $a['_score']; } );
        return array_slice( $results, 0, 3 );
    }

    /**
     * Genera un Brief Estratégico Pro Max.
     */
    public function generate_master_brief( string $query ): array {
        // 1. Detectar categoría de producto
        $product = $this->search( $query, 'products' )[0] ?? [];
        $category = $product['Product Type'] ?? 'General';

        // 2. Aplicar Razonamiento (La "Potencia" de UX Pro)
        $reasoning = $this->get_reasoning( $category );

        // 3. Obtener Componentes Técnicos
        $landing = $this->search( $query, 'landing' )[0] ?? [];
        $style = $this->search( $query, 'styles' )[0] ?? [];
        $colors = $this->search( $query, 'colors' )[0] ?? [];

        return [
            'strategy' => [
                'pattern' => $reasoning['Recommended_Pattern'] ?? $landing['Pattern Name'] ?? 'Hero + Features + CTA',
                'sections' => $landing['Section Order'] ?? $reasoning['Section_Order'] ?? 'Hero > Features > CTA',
                'effects' => $reasoning['Key_Effects'] ?? $style['Effects & Animation'] ?? 'Subtle transitions',
                'anti_patterns' => $reasoning['Anti_Patterns'] ?? 'No emojis, avoid low contrast',
            ],
            'design_tokens' => [
                'primary' => $colors['Primary (Hex)'] ?? '#002147',
                'secondary' => $colors['Secondary (Hex)'] ?? '#ca8a04',
                'radius' => '12px',
                'shadow' => '0 10px 15px rgba(0,0,0,0.1)',
            ],
            'components' => [
                'buttons' => [
                    'padding' => '12px 24px',
                    'transition' => 'all 200ms ease',
                    'hover' => 'translateY(-1px) opacity(0.9)',
                ],
                'cards' => [
                    'radius' => '12px',
                    'shadow_hover' => '0 20px 25px rgba(0,0,0,0.15)',
                ]
            ]
        ];
    }
}

