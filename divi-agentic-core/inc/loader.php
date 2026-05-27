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
        if ( strncmp( $prefix, $class, strlen( $prefix ) ) !== 0 ) {
            return;
        }

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
        }
    }
}

Loader::init();
