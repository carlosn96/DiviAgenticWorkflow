<?php
/**
 * DAC Loader — Unified Architectural Entry Point
 * 
 * Centralizes the loading of Core, CLI, and DAC frameworks.
 */

namespace DAC;

class Loader {
    public static function init() {
        spl_autoload_register( [ self::class, 'autoload' ] );
    }

    public static function autoload( $class ) {
        $prefix = 'DAC\\';
        if ( strncmp( $prefix, $class, strlen( $prefix ) ) === 0 ) {
            $relative_class = substr( $class, strlen( $prefix ) );

            // Try PSR-4 path first (e.g., CLI/Agentic_Command.php)
            $file = __DIR__ . '/' . str_replace( '\\', '/', $relative_class ) . '.php';
            if ( file_exists( $file ) ) {
                require_once $file;
                return;
            }

            // Fallback to WordPress-style class-*.php naming
            $parts = explode( '\\', $relative_class );
            $class_name = array_pop( $parts );
            $dir = __DIR__ . '/' . str_replace( '\\', '/', implode( '\\', $parts ) );
            $class_slug = str_replace( '_', '-', $class_name );
            $wp_file = $dir . '/class-' . strtolower( $class_slug ) . '.php';
            if ( file_exists( $wp_file ) ) {
                require_once $wp_file;
                return;
            }
        }

        // Divi_Agentic_Core\Core\Renderers namespace
        if ( strncmp( 'Divi_Agentic_Core\\', $class, strlen( 'Divi_Agentic_Core\\' ) ) === 0 ) {
            $relative = substr( $class, strlen( 'Divi_Agentic_Core\\' ) );
            $parts    = explode( '\\', $relative );
            $name     = array_pop( $parts );
            $slug     = strtolower( preg_replace( '/([a-z0-9])([A-Z])/', '$1-$2', str_replace( '_', '-', $name ) ) );
            $dac_file = __DIR__ . '/core/renderers/class-' . $slug . '.php';
            if ( file_exists( $dac_file ) ) {
                require_once $dac_file;
                return;
            }
        }
    }
}

Loader::init();

// Autoloader for Divi_Agentic_Core renderer namespace.
spl_autoload_register( function ( $class ) {
	$prefix = 'Divi_Agentic_Core\\';
	if ( strncmp( $prefix, $class, strlen( $prefix ) ) !== 0 ) {
		return;
	}

	$relative = substr( $class, strlen( $prefix ) );
	$parts    = explode( '\\', $relative );
	$name     = array_pop( $parts );
	$slug     = strtolower( preg_replace( '/([a-z0-9])([A-Z])/', '$1-$2', str_replace( '_', '-', $name ) ) );
	$file     = __DIR__ . '/core/renderers/class-' . $slug . '.php';
	if ( file_exists( $file ) ) {
		require_once $file;
	}
} );

