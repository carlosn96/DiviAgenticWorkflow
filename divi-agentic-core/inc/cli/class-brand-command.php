<?php
/**
 * Brand_Command — wp brand {init|sync|reset|status}
 *
 * Punto de entrada único para todo el sistema de diseño de marca:
 * diseño de la marca desde _design_vars.json → WordPress + Divi.
 *
 * Antes de usar brand.php, ahora wp brand (registrado como WP-CLI command).
 *
 * @package DAC\CLI
 */

namespace DAC\CLI;

use WP_CLI;
use DAC\Core\Token_Registry;
use DAC\Core\Brand_Sync_Handler;
use DAC\Core\Brand_Reset_Handler;

class Brand_Command {

    public static function register(): void {
        WP_CLI::add_command( 'brand', self::class );
    }

    // ─── Resolver de site ────────────────────────────────────────────────

    private function resolve_site( array $args, array $assoc_args ): string {
        // Args posicionales: wp brand sync netflix
        if ( ! empty( $args ) ) {
            return $args[0];
        }
        // Flag explícito
        if ( ! empty( $assoc_args['site'] ) ) {
            return $assoc_args['site'];
        }
        // Fallback a DAW_SITE de .env
        $env = function_exists( 'daw_get_active_site' ) ? daw_get_active_site() : getenv( 'DAW_SITE' );
        if ( $env ) {
            return $env;
        }
        WP_CLI::error( 'Especifica <slug> como argumento o define DAW_SITE en .env' );
    }

    private function bundle_dir(): string {
        return dirname( DIVI_AGENTIC_CORE_DIR );
    }

    private function vars_path( string $site ): string {
        return $this->bundle_dir() . '/site/' . $site . '/brand/_design_vars.json';
    }

    private function divitheme_path( string $site ): string {
        return $this->bundle_dir() . '/site/' . $site . '/design-system/divitheme.json';
    }

    // ─── init ────────────────────────────────────────────────────────────

    /**
     * Crea _design_vars.json (solo si no existe).
     *
     * ## OPTIONS
     *
     * [<slug>]
     * : Nombre del sitio. Si se omite, usa DAW_SITE del .env.
     *
     * @when after_wp_load
     */
    public function init( array $args, array $assoc_args ): void {
        $site = $this->resolve_site( $args, $assoc_args );
        $out  = $this->vars_path( $site );

        if ( file_exists( $out ) ) {
            WP_CLI::warning( "Ya existe: {$out}" );
            WP_CLI::log( 'NO se sobreescribió. Edita el archivo existente.' );
            WP_CLI::log( 'Si quieres regenerarlo, bórralo primero.' );
            return;
        }

        $dir = dirname( $out );
        if ( ! is_dir( $dir ) ) {
            mkdir( $dir, 0755, true );
        }

        $scaffold = Token_Registry::generate_scaffold();
        file_put_contents( $out, json_encode( $scaffold, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES ) );
        WP_CLI::success( "Creado: {$out}" );
        WP_CLI::log( 'Antes de sincronizar, carga un skill de dirección visual' );
        WP_CLI::log( '(hallmark, impeccable, high-end-visual-design) y edita los valores' );
        WP_CLI::log( 'con criterio de diseño real.' );
    }

    // ─── sync ────────────────────────────────────────────────────────────

    /**
     * Sincroniza _design_vars.json → Divi (Customizer + gcids + gvids + divitheme.json).
     *
     * ## OPTIONS
     *
     * [<slug>]
     * : Nombre del sitio. Si se omite, usa DAW_SITE del .env.
     *
     * @when after_wp_load
     */
    public function sync( array $args, array $assoc_args ): void {
        $site = $this->resolve_site( $args, $assoc_args );
        $vars = $this->vars_path( $site );

        if ( ! file_exists( $vars ) ) {
            WP_CLI::error( "No existe _design_vars.json para '{$site}'." );
            WP_CLI::log( 'Ejecuta primero: wp brand init ' . $site );
        }

        Brand_Sync_Handler::run( $site );
    }

    // ─── reset ───────────────────────────────────────────────────────────

    /**
     * Revierte TODO lo que sync escribió — valores de fábrica de Divi.
     *
     * ## OPTIONS
     *
     * [<slug>]
     * : Nombre del sitio. Si se omite, usa DAW_SITE del .env.
     *
     * @when after_wp_load
     */
    public function reset( array $args, array $assoc_args ): void {
        $site = $this->resolve_site( $args, $assoc_args );
        Brand_Reset_Handler::run( $site );
    }

    // ─── status ──────────────────────────────────────────────────────────

    /**
     * Muestra el estado actual del brand (archivos + BD).
     *
     * ## OPTIONS
     *
     * [<slug>]
     * : Nombre del sitio. Si se omite, usa DAW_SITE del .env.
     *
     * @when after_wp_load
     */
    public function status( array $args, array $assoc_args ): void {
        $site = $this->resolve_site( $args, $assoc_args );
        $vars_path = $this->vars_path( $site );
        $ds_path   = $this->divitheme_path( $site );

        WP_CLI::log( str_repeat( '─', 50 ) );
        WP_CLI::log( "Brand: {$site}" );
        WP_CLI::log( str_repeat( '─', 50 ) );

        WP_CLI::log( '' );
        WP_CLI::log( 'Archivos:' );
        WP_CLI::log( '  _design_vars.json: ' . ( file_exists( $vars_path ) ? 'EXISTE' : 'NO EXISTE' ) );
        WP_CLI::log( '  divitheme.json:    ' . ( file_exists( $ds_path ) ? 'EXISTE' : 'NO EXISTE' ) );

        WP_CLI::log( '' );
        WP_CLI::log( 'WordPress:' );
        $divi = get_option( 'et_divi', [] );
        $gd   = get_option( 'et_global_data', null );
        $hash = get_option( '_dac_gcid_hash', null );
        WP_CLI::log( '  et_divi:       ' . count( $divi ) . ' keys' );
        WP_CLI::log( '  et_global_data: ' . ( $gd ? 'PRESENTE' : 'AUSENTE' ) );
        WP_CLI::log( '  _dac_gcid_hash: ' . ( $hash ? 'PRESENTE' : 'AUSENTE' ) );

        if ( file_exists( $vars_path ) ) {
            $vars = json_decode( file_get_contents( $vars_path ), true );
            if ( $vars ) {
                $missing = [];
                $tokens  = Token_Registry::get_all();
                foreach ( $tokens as $key => $def ) {
                    if ( ! empty( $def['required'] ) && ( ! array_key_exists( $key, $vars ) || $vars[ $key ] === null ) ) {
                        $missing[] = $key;
                    }
                }
                if ( $missing ) {
                    WP_CLI::log( '' );
                    WP_CLI::warning( count( $missing ) . ' tokens required sin valor:' );
                    foreach ( $missing as $k ) {
                        WP_CLI::log( "  - {$k}" );
                    }
                }
            }
        }

        $accent = function_exists( 'et_get_option' ) ? et_get_option( 'accent_color', 'NO' ) : 'N/A';
        WP_CLI::log( '' );
        WP_CLI::log( "et_get_option('accent_color'): {$accent}" );
    }
}
