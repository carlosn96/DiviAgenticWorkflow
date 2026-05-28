<?php
/**
 * Plugin Name: Divi Agentic Core (DAW)
 * Description: Core engine for the Divi Agentic Workflow — Layout_Engine, Design_Resolver, Module_Metadata, and WP-CLI commands.
 * Version:     4.0.0
 * Author:      DAW Bundle (Local)
 * Requires PHP: 8.0
 */

defined( 'ABSPATH' ) || exit;

define( 'DIVI_AGENTIC_CORE_DIR', __DIR__ );
define( 'DIVI_AGENTIC_CORE_VERSION', '4.0.0' );

require_once __DIR__ . '/inc/loader.php';

add_action( 'cli_init', function () {
	if ( defined( 'WP_CLI' ) && WP_CLI ) {
		\DAC\CLI\Agentic_Command::register();
	}
} );
