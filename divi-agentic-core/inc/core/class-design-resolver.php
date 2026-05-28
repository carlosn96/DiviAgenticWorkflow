<?php
namespace DAC\Core;

/**
 * Design Resolver v1.0 — Project-Agnostic Token & Preset Resolver
 *
 * Reads any project's design-system JSON file and resolves:
 *   - {{design:type:key}}       → scalar token value (e.g. {{design:color:red}})
 *   - "$preset" key in objects  → deep-merge of a preset definition
 *
 * Zero knowledge of project-specific colors, fonts, or values.
 * All design data lives in the external DS file passed via constructor.
 */
class Design_Resolver {

    private array $design;
    private array $flat_tokens = [];

    public function __construct( string $design_system_path ) {
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
        $this->flatten_tokens();
    }

    /**
     * Resolve a raw schema string: merge presets + replace {{design:*}} tokens.
     */
    public function resolve_schema_string( string $raw_schema ): string {
        $raw_schema = ltrim( $raw_schema, "\xEF\xBB\xBF" );

        // Step 1: Structural preset merge (works on decoded array)
        $schema = json_decode( $raw_schema, true );
        if ( json_last_error() === JSON_ERROR_NONE && is_array( $schema ) ) {
            $this->resolve_presets_recursive( $schema );
            $raw_schema = json_encode( $schema, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES );
        }

        // Step 2: Scalar token replacement (works on string)
        $raw_schema = $this->replace_tokens( $raw_schema );

        return $raw_schema;
    }

    /**
     * Getter for external use (e.g., validation, inspection).
     */
    public function get_design(): array {
        return $this->design;
    }

    // ---------------------------------------------------------------
    // Token flattening & replacement
    // ---------------------------------------------------------------

    private function flatten_tokens(): void {
        $gcid_synced = ! empty( get_option( '_dac_gcid_hash', '' ) );

        $groups = $this->design['tokens'] ?? [];
        foreach ( $groups as $group => $values ) {
            if ( is_array( $values ) ) {
                foreach ( $values as $key => $value ) {
                    $token = "{{design:{$group}:{$key}}}";

                    // Color tokens: use var(--gcid-*) when global colors synced
                    if ( $gcid_synced && 'color' === $group ) {
                        $slug = sanitize_title( $key );
                        $this->flat_tokens[ $token ] = "var(--gcid-{$slug})";
                    } else {
                        $this->flat_tokens[ $token ] = $value;
                    }
                }
            }
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
    // Preset resolution (structural merge)
    // ---------------------------------------------------------------

    private function resolve_presets_recursive( array &$node ): void {
        // Merge presets if present
        if ( isset( $node['presets'] ) && is_array( $node['presets'] ) ) {
            // Process in reverse so deep_merge_preset($preset, $node)
            // correctly gives priority to later presets (node wins over preset).
            $reversed = array_reverse( $node['presets'] );
            foreach ( $reversed as $preset_path ) {
                $preset = $this->get_preset_by_path( $preset_path );
                if ( $preset !== null ) {
                    $node = $this->deep_merge_preset( $preset, $node );
                }
            }
            unset( $node['presets'] );
        }

        // Recurse into structural keys
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

    /**
     * Resolve a preset path like "section:hero-dark" or "text:eyebrow" or "module:card"
     * from the design file's "presets" section.
     */
    private function get_preset_by_path( string $path ): ?array {
        $parts = explode( ':', $path );
        if ( count( $parts ) < 2 ) {
            return null;
        }

        $category = $parts[0];     // "section", "text", "module"
        $name     = $parts[1];     // "hero-dark", "eyebrow", "card"

        $presets_section = $this->design['presets'] ?? [];

        if ( ! isset( $presets_section[ $category ][ $name ] ) ) {
            \WP_CLI::warning( "Preset not found: {$category}:{$name}" );
            return null;
        }

        // Deep-resolve any {{design:*}} tokens inside the preset itself
        $resolved = $this->resolve_preset_values( $presets_section[ $category ][ $name ] );

        return $resolved;
    }

    /**
     * Recursively replace {{design:*}} tokens inside a preset definition.
     */
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

    /**
     * Merge preset into node. Preset provides defaults; explicit node keys win.
     */
    private function deep_merge_preset( array $preset, array $node ): array {
        $merged = $preset;
        foreach ( $node as $key => $value ) {
            if ( isset( $merged[ $key ] ) && is_array( $merged[ $key ] ) && is_array( $value ) ) {
                $merged[ $key ] = $this->deep_merge_preset( $merged[ $key ], $value );
            } else {
                $merged[ $key ] = $value;
            }
        }
        return $merged;
    }
}
