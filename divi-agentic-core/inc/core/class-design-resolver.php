<?php
namespace DAC\Core;

/**
 * Design Resolver v2.0 — Lee tokens desde stores nativos Divi 5
 *
 * gvid prefixes obtenidos dinámicamente de Token_Registry.
 * Si agregas un nuevo token gvid, solo tocas class-token-registry.php.
 *
 * Resuelve:
 *   - {{design:color:key}}       → var(--gcid-*) desde Global Colors
 *   - {{design:<prefix>:key}}    → valor desde Global Variables (numbers/fonts)
 *   - "$preset" en objetos       → deep-merge desde divitheme.json['presets']
 *
 * divitheme.json solo contiene presets + metadata.
 * Los tokens viven en los stores nativos de Divi 5.
 */
class Design_Resolver {

    private array $design;
    private array $flat_tokens = [];
    private ?array $brand_vars = null;

    public function __construct( string $design_system_path, ?string $brand_vars_path = null ) {
        if ( ! file_exists( $design_system_path ) ) {
            \WP_CLI::error( "Design system file not found: {$design_system_path}" );
        }

        $raw = file_get_contents( $design_system_path );
        $raw = ltrim( $raw, "\xEF\xBB\xBF" );
        $decoded = json_decode( $raw, true );

        if ( json_last_error() !== JSON_ERROR_NONE ) {
            \WP_CLI::error( 'Design system JSON error: ' . json_last_error_msg() );
        }

        $this->design = $decoded;

        if ( $brand_vars_path && file_exists( $brand_vars_path ) ) {
            $brand_raw = file_get_contents( $brand_vars_path );
            $brand_decoded = json_decode( $brand_raw, true );
            if ( json_last_error() === JSON_ERROR_NONE && is_array( $brand_decoded ) ) {
                $this->brand_vars = $brand_decoded;
            }
        }

        $this->flatten_tokens();
    }

    public function resolve_schema_string( string $raw_schema ): string {
        $raw_schema = ltrim( $raw_schema, "\xEF\xBB\xBF" );

        $schema = json_decode( $raw_schema, true );
        if ( json_last_error() === JSON_ERROR_NONE && is_array( $schema ) ) {
            $this->resolve_presets_recursive( $schema );
            $raw_schema = json_encode( $schema, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES );
        }

        $raw_schema = $this->replace_tokens( $raw_schema );

        return $raw_schema;
    }

    public function get_design(): array {
        return $this->design;
    }

    // ---------------------------------------------------------------
    // Token flattening — lee desde stores nativos Divi 5
    // ---------------------------------------------------------------

    private function flatten_tokens(): void {
        $this->flatten_colors_from_gcids();
        $this->flatten_from_global_variables();
    }

    private function flatten_colors_from_gcids(): void {
        $gcid_synced = ! empty( get_option( '_dac_gcid_hash', '' ) );
        if ( ! $gcid_synced ) return;

        if ( ! class_exists( '\ET\Builder\Packages\GlobalData\GlobalData' ) ) return;

        $global_colors = \ET\Builder\Packages\GlobalData\GlobalData::get_global_colors();
        if ( empty( $global_colors ) ) return;

        foreach ( $global_colors as $gcid => $data ) {
            $slug = preg_replace( '/^gcid-/', '', $gcid );
            // Skip customizer slots (gcid-primary-color, etc.) — desde Token_Registry
            if ( in_array( $slug, Token_Registry::get_gcid_slugs_to_skip(), true ) ) {
                continue;
            }
            $token = "{{design:color:{$slug}}}";
            $this->flat_tokens[ $token ] = "var(--gcid-{$slug})";
        }
    }

    private function flatten_from_global_variables(): void {
        // Try gvids from GlobalData (numbers, fonts, etc.)
        if ( class_exists( '\ET\Builder\Packages\GlobalData\GlobalData' ) ) {
            $global_vars = \ET\Builder\Packages\GlobalData\GlobalData::get_global_variables();
            if ( ! empty( $global_vars ) && ! empty( array_filter( $global_vars ) ) ) {
                $prefixes = Token_Registry::get_gvid_prefixes();
                if ( ! empty( $prefixes ) ) {
                    $gvid_pattern = '/^gvid-(' . implode( '|', $prefixes ) . ')-(.+)$/';
                    foreach ( $global_vars as $gvid_type => $items ) {
                        if ( ! is_array( $items ) ) continue;
                        foreach ( $items as $gvid => $item ) {
                            $value = $item['value'] ?? '';
                            if ( $value === '' ) continue;
                            if ( preg_match( $gvid_pattern, $gvid, $m ) ) {
                                $group = $m[1];
                                $key   = $m[2];
                                $token = "{{design:{$group}:{$key}}}";
                                $this->flat_tokens[ $token ] = $value;
                            }
                        }
                    }
                }
            }
        }

        // Fallback: resolver tokens que no vinieron de gvids usando brand_vars
        $this->flatten_gvid_defaults_from_registry();
    }

    /**
     * Fallback cuando no hay gvids sincronizados.
     * Lee defaults de Token_Registry::get_gvid_groups() para producir los mismos tokens
     * que brand-sync.php registraría como gvids.
     * Garantizado en sincronía porque usa el mismo método del Registry.
     */
    private function flatten_gvid_defaults_from_registry(): void {
        $groups = Token_Registry::get_gvid_groups();
        $defaults = Token_Registry::get_defaults();

        // Numbers group: radius, space, shadow, easing, duration
        $numbers = $groups['numbers'] ?? [];
        foreach ( $numbers as $source_key => $def ) {
            $value = $this->brand_vars[ $source_key ] ?? $defaults[ $source_key ] ?? null;
            if ( empty( $value ) ) continue;
            $parts = explode( '_', $source_key );
            $type = $parts[0];
            $slug = implode( '_', array_slice( $parts, 1 ) );
            $token = "{{design:{$type}:{$slug}}}";
            $this->flat_tokens[ $token ] = $value;
        }

        // Fonts group
        $fonts = $groups['fonts'] ?? [];
        foreach ( $fonts as $source_key => $def ) {
            $value = $this->brand_vars[ $source_key ] ?? $defaults[ $source_key ] ?? null;
            if ( empty( $value ) ) continue;
            $family = explode( ',', $value )[0];
            $family = trim( $family, "'\" " );
            $slug = substr( $source_key, 5 ); // 'font_display' → 'display'
            $token = "{{design:font:{$slug}}}";
            $this->flat_tokens[ $token ] = $family;
        }
    }

    private function replace_tokens( string $input ): string {
        return str_replace(
            array_keys( $this->flat_tokens ),
            array_values( $this->flat_tokens ),
            $input
        );
    }

    // ---------------------------------------------------------------
    // Preset resolution (structural merge) — desde divitheme.json
    // ---------------------------------------------------------------

    private function resolve_presets_recursive( array &$node ): void {
        if ( isset( $node['presets'] ) && is_array( $node['presets'] ) ) {
            $reversed = array_reverse( $node['presets'] );
            foreach ( $reversed as $preset_path ) {
                $preset = $this->get_preset_by_path( $preset_path );
                if ( $preset !== null ) {
                    $node = $this->deep_merge_preset( $preset, $node );
                }
            }
            unset( $node['presets'] );
        }

        $recurse_keys = [ 'sections', 'rows', 'columns', 'modules', 'children' ];
        foreach ( $recurse_keys as $key ) {
            if ( isset( $node[ $key ] ) && is_array( $node[ $key ] ) ) {
                foreach ( $node[ $key ] as &$child ) {
                    if ( is_array( $child ) ) {
                        $this->resolve_presets_recursive( $child );
                    }
                }
            }
        }
    }

    private function get_preset_by_path( string $path ): ?array {
        $parts = explode( ':', $path );
        if ( count( $parts ) < 2 ) return null;

        $category = $parts[0];
        $name     = $parts[1];

        $presets_section = $this->design['presets'] ?? [];
        if ( ! isset( $presets_section[ $category ][ $name ] ) ) {
            \WP_CLI::warning( "Preset not found: {$category}:{$name}" );
            return null;
        }

        return $this->resolve_preset_values( $presets_section[ $category ][ $name ] );
    }

    private function resolve_preset_values( $value ) {
        if ( is_string( $value ) ) {
            return $this->replace_tokens( $value );
        }
        if ( is_array( $value ) ) {
            $result = [];
            foreach ( $value as $k => $v ) {
                $result[ $k ] = $this->resolve_preset_values( $v );
            }
            return $result;
        }
        return $value;
    }

    private function deep_merge_preset( array $preset, array $node ): array {
        $merged = $preset;
        foreach ( $node as $key => $value ) {
            if ( isset( $merged[ $key ] ) && is_array( $merged[ $key ] ) && is_array( $value ) ) {
                $merged[ $key ] = $this->deep_merge_preset( $merged[ $key ], $value );
            } elseif ( isset( $merged[ $key ] ) && is_array( $merged[ $key ] ) && is_scalar( $value ) ) {
                continue;
            } else {
                $merged[ $key ] = $value;
            }
        }
        return $merged;
    }
}
