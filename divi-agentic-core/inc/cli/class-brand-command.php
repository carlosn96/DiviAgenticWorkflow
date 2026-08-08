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
use DAC\Core\Design_Validator;
use DAC\Core\Skills\Skill_Interface;
use DAC\Core\Skills\Hallmark_Skill;
use DAC\Core\Skills\Impeccable_Skill;
use DAC\Core\Skills\High_End_Skill;

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
     * [--skill=<skill>]
     * : Skill de diseño para generar valores con intención (hallmark, impeccable, high-end-visual-design).
     *
     * @when after_wp_load
     */
    public function init( array $args, array $assoc_args ): void {
        $site       = $this->resolve_site( $args, $assoc_args );
        $out        = $this->vars_path( $site );
        $skill_name = $assoc_args['skill'] ?? null;

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

        if ( $skill_name ) {
            $skill = self::resolve_skill( $skill_name );
            if ( ! $skill ) {
                WP_CLI::error( "Skill desconocido: {$skill_name}. Usa: hallmark, impeccable, high-end-visual-design" );
            }
            $scaffold = $skill->get_scaffold();
            WP_CLI::log( "Generando con skill: {$skill->get_name()} — {$skill->get_description()}" );
        } else {
            $scaffold = Token_Registry::generate_scaffold();
            WP_CLI::log( 'Generando scaffold genérico. Usa --skill para valores con intención de diseño.' );
        }

        file_put_contents( $out, json_encode( $scaffold, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES ) );
        WP_CLI::success( "Creado: {$out}" );
    }

    private function design_pass_path( string $site ): string {
        $dir = dirname( $this->vars_path( $site ) );
        return $dir . '/.design-pass';
    }

    // ─── approve ───────────────────────────────────────────────────────────

    /**
     * Aprueba el diseño tras evaluación (mecánica + skill opcional).
     *
     * ## OPTIONS
     *
     * [<slug>]
     * : Nombre del sitio.
     *
     * [--skill=<skill>]
     * : Skill de diseño para validación adicional (hallmark, impeccable, high-end-visual-design).
     *
     * @when after_wp_load
     */
    public function approve( array $args, array $assoc_args ): void {
        $site       = $this->resolve_site( $args, $assoc_args );
        $skill_name = $assoc_args['skill'] ?? null;

        $skill = null;
        if ( $skill_name ) {
            $skill = self::resolve_skill( $skill_name );
            if ( ! $skill ) {
                WP_CLI::error( "Skill desconocido: {$skill_name}. Usa: hallmark, impeccable, high-end-visual-design" );
            }
        }

        $vars_path = $this->vars_path( $site );
        if ( ! file_exists( $vars_path ) ) {
            WP_CLI::error( "No existe _design_vars.json para '{$site}'." );
        }

        $vars = json_decode( file_get_contents( $vars_path ), true );

        $mechanical = Design_Validator::run( $vars );
        $skill_result = $skill ? $skill->validate( $vars ) : null;

        $all_pass = $mechanical['summary']['gate'] && ( $skill ? $skill_result['summary']['gate'] : true );

        $vars_hash = md5_file( $vars_path );

        $pass_path = $this->design_pass_path( $site );
        $dir       = dirname( $pass_path );
        if ( ! is_dir( $dir ) ) {
            mkdir( $dir, 0755, true );
        }

        $pass = [
            'vars_hash'   => $vars_hash,
            'skill'       => $skill_name,
            'approved_at' => gmdate( 'Y-m-d\TH:i:s\Z' ),
            'gate'        => $all_pass,
            'mechanical'  => $mechanical['summary'],
            'skill_checks' => $skill_result['summary'] ?? null,
        ];

        file_put_contents(
            $pass_path,
            json_encode( $pass, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES )
        );

        if ( $all_pass ) {
            $label = $skill_name ?: 'mecánico';
            WP_CLI::success( "Diseño aprobado ({$label}). Sync permitido." );
        } else {
            $fails = $mechanical['summary']['fail'] + ( $skill_result['summary']['fail'] ?? 0 );
            $warns = $mechanical['summary']['warn'] + ( $skill_result['summary']['warn'] ?? 0 );
            $label = $skill_name ?: 'mecánico';
            WP_CLI::warning( "Aprobado con {$fails} fail(s) y {$warns} warn(s). Usa --force en sync para bypass." );
            WP_CLI::log( "Detalles: wp brand validate {$site}" . ( $skill_name ? " --skill={$skill_name}" : '' ) );
        }
    }

    // ─── revoke ────────────────────────────────────────────────────────────

    /**
     * Revoca la aprobación de diseño.
     *
     * ## OPTIONS
     *
     * [<slug>]
     * : Nombre del sitio.
     *
     * @when after_wp_load
     */
    public function revoke( array $args, array $assoc_args ): void {
        $site      = $this->resolve_site( $args, $assoc_args );
        $pass_path = $this->design_pass_path( $site );

        if ( ! file_exists( $pass_path ) ) {
            WP_CLI::warning( 'No hay aprobación vigente.' );
            return;
        }

        unlink( $pass_path );
        WP_CLI::success( 'Aprobación revocada. Sync requerirá nueva aprobación.' );
    }

    private static function resolve_skill( ?string $name ): ?Skill_Interface {
        $skills = [
            'hallmark'               => Hallmark_Skill::class,
            'impeccable'             => Impeccable_Skill::class,
            'high-end-visual-design' => High_End_Skill::class,
        ];

        if ( $name && isset( $skills[ $name ] ) ) {
            $class = $skills[ $name ];
            return new $class();
        }

        return null;
    }

    // ─── validate ──────────────────────────────────────────────────────────

    /**
     * Valida _design_vars.json contra reglas de diseño (contraste, escala, pairing).
     *
     * ## OPTIONS
     *
     * [<slug>]
     * : Nombre del sitio. Si se omite, usa DAW_SITE del .env.
     *
     * [--skill=<skill>]
     * : Validar contra un skill específico (hallmark, impeccable, high-end-visual-design).
     *
     * [--json]
     * : Output en JSON machine-readable.
     *
     * [--suggest]
     * : Mostrar sugerencias correctivas para fails y warns.
     *
     * @when after_wp_load
     */
    public function validate( array $args, array $assoc_args ): void {
        $site      = $this->resolve_site( $args, $assoc_args );
        $vars_path = $this->vars_path( $site );
        $skill_name = $assoc_args['skill'] ?? null;

        if ( ! file_exists( $vars_path ) ) {
            WP_CLI::error( "No existe _design_vars.json para '{$site}'." );
        }

        $vars  = json_decode( file_get_contents( $vars_path ), true );
        $valid = json_last_error() === JSON_ERROR_NONE && is_array( $vars );

        if ( ! $valid ) {
            WP_CLI::error( "Error al parsear _design_vars.json." );
        }

        // Checks mecánicos universales
        $result = Design_Validator::run( $vars );

        // Checks específicos del skill
        $skill = $skill_name ? self::resolve_skill( $skill_name ) : null;
        if ( $skill ) {
            $skill_result = $skill->validate( $vars );
            $result['checks']  = array_merge( $result['checks'], $skill_result['checks'] );
            $result['summary']['total'] += $skill_result['summary']['total'];
            $result['summary']['pass']  += $skill_result['summary']['pass'];
            $result['summary']['warn']  += $skill_result['summary']['warn'];
            $result['summary']['fail']  += $skill_result['summary']['fail'];
            $result['summary']['gate']   = $result['summary']['gate'] && $skill_result['summary']['gate'];
            $result['_skill'] = [
                'name'        => $skill->get_name(),
                'description' => $skill->get_description(),
                'checks'      => $skill_result['summary'],
            ];
        }

        if ( ! empty( $assoc_args['json'] ) ) {
            WP_CLI::line( json_encode( $result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES ) );
            return;
        }

        WP_CLI::log( str_repeat( '─', 50 ) );

        $title = $skill ? "Validación ({$skill->get_name()})" : 'Validación mecánica';
        WP_CLI::log( "{$title}: {$site}" );
        WP_CLI::log( str_repeat( '─', 50 ) );

        $s = $result['summary'];
        WP_CLI::log( "Total: {$s['total']} | ✓ Pass: {$s['pass']} | ⚠ Warn: {$s['warn']} | ✗ Fail: {$s['fail']}" );
        WP_CLI::log( '' );

        if ( $skill ) {
            WP_CLI::log( "Skill: {$skill->get_name()} — {$skill->get_description()}" );
            WP_CLI::log( '' );
        }

        foreach ( $result['checks'] as $check ) {
            $icon = $check['status'] === 'pass' ? '✓' : ( $check['status'] === 'warn' ? '⚠' : '✗' );
            WP_CLI::log( "  {$icon} [{$check['status']}] {$check['message']}" );
        }

        WP_CLI::log( '' );

        if ( ! empty( $assoc_args['suggest'] ) && $s['fail'] + $s['warn'] > 0 ) {
            WP_CLI::log( '── Sugerencias ──' );
            foreach ( self::suggest_fixes( $result['checks'], $vars ) as $suggestion ) {
                WP_CLI::log( "  → {$suggestion}" );
            }
            WP_CLI::log( '' );
        }

        if ( $s['gate'] ) {
            WP_CLI::success( 'Validación de diseño pasada. Puedes ejecutar wp brand approve.' );
        } else {
            WP_CLI::error( 'La validación de diseño tiene errores. Corrígelos o usa --force en sync.' );
        }
    }

    private static function suggest_fixes( array $checks, array $vars ): array {
        $hints = [];
        foreach ( $checks as $c ) {
            if ( $c['status'] === 'pass' ) continue;

            $rule = $c['rule'] ?? '';

            if ( str_starts_with( $rule, 'contrast:' ) && $c['status'] === 'fail' ) {
                $parts = explode( ':', $rule );
                $source = $parts[1] ?? '?';
                $target = $parts[2] ?? '?';
                $min = $c['min'] ?? 4.5;
                $actual = $c['actual'] ?? 0;
                $hints[] = "{$source} vs {$target}: actual {$actual}:1, objetivo ≥{$min}:1. Prueba oscurecer {$source} o aclarar {$target}.";
            }

            if ( str_starts_with( $rule, 'pairing:' ) && $c['status'] === 'fail' ) {
                $hints[] = $c['message'] . ' Sugerencia: cambia una fuente a serif o display si la otra es sans, o viceversa.';
            }

            if ( str_starts_with( $rule, 'scale:heading' ) && $c['status'] === 'fail' ) {
                $hints[] = 'La progresión de headings no sigue la escala ~1.25. Ajusta los valores para que cada nivel sea ~1.25× el siguiente.';
            }

            if ( str_starts_with( $rule, 'high-end:banned-fonts' ) ) {
                $hints[] = 'Reemplaza las fuentes prohibidas (Inter, Roboto, Arial, Helvetica, Open Sans) por alternativas premium como Clash Display, Plus Jakarta Sans, DM Sans.';
            }

            if ( $rule === 'hallmark:font-count' && $c['status'] === 'fail' ) {
                $hints[] = 'Define al menos 2 fuentes distintas (font_display + font_body). Recomendación: serif + sans o display + sans.';
            }
        }
        return $hints;
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
     * [--force]
     * : Bypass la validación de diseño.
     *
     * @when after_wp_load
     */
    public function sync( array $args, array $assoc_args ): void {
        $site  = $this->resolve_site( $args, $assoc_args );
        $vars  = $this->vars_path( $site );
        $force = ! empty( $assoc_args['force'] );

        if ( ! file_exists( $vars ) ) {
            WP_CLI::log( 'Ejecuta primero: wp brand init ' . $site );
            WP_CLI::error( "No existe _design_vars.json para '{$site}'." );
        }

        Brand_Sync_Handler::run( $site, $force );
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
        $pass_path = $this->design_pass_path( $site );
        $pass      = file_exists( $pass_path ) ? json_decode( file_get_contents( $pass_path ), true ) : null;
        WP_CLI::log( '  _design_vars.json: ' . ( file_exists( $vars_path ) ? 'EXISTE' : 'NO EXISTE' ) );
        WP_CLI::log( '  divitheme.json:    ' . ( file_exists( $ds_path ) ? 'EXISTE' : 'NO EXISTE' ) );
        $pass_label = $pass ? "APROBADO (" . ( $pass['skill'] ?? 'mecánico' ) . ", {$pass['approved_at']})" : 'AUSENTE';
        WP_CLI::log( '  .design-pass:      ' . $pass_label );

        WP_CLI::log( '' );
        WP_CLI::log( 'WordPress:' );
        $divi = get_option( 'et_divi', [] );
        $gd   = $divi['et_global_data'] ?? null;
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
