<?php
/**
 * Deploy compiled schema to Theme Builder header layout (et_header_layout)
 * Usage: wp eval-file deploy-to-header.php
 */

// Load plugin classes
if ( ! defined( 'ABSPATH' ) ) {
    require_once dirname( __DIR__, 5 ) . '/app/public/wp-load.php';
}

require_once dirname( __DIR__ ) . '/inc/core/trait-module-metadata.php';
require_once dirname( __DIR__ ) . '/inc/core/class-layout-engine.php';

$schema_path = __DIR__ . '/temp_header_schema.json';
$header_post_id = 121485;

if ( ! file_exists( $schema_path ) ) {
    WP_CLI::error( "Schema file not found: {$schema_path}" );
}

$raw = file_get_contents( $schema_path );
$engine = new DAC\Core\Layout_Engine();
$blocks = $engine->compile( $raw );

WP_CLI::log( "Compiled " . strlen( $blocks ) . " chars of block markup" );

$post_data = [
    'ID'            => $header_post_id,
    'post_content'  => wp_slash( $blocks ),
    'post_status'   => 'publish',
    'post_type'     => 'et_header_layout',
];

$post_id = wp_update_post( $post_data, true );
if ( is_wp_error( $post_id ) ) {
    WP_CLI::error( "Failed to update post: " . $post_id->get_error_message() );
}

// Apply Divi meta flags
update_post_meta( $post_id, '_et_pb_use_builder', 'on' );
update_post_meta( $post_id, '_et_pb_use_divi_5', 'on' );
update_post_meta( $post_id, '_et_pb_show_page_creation', 'off' );
update_post_meta( $post_id, '_et_pb_built_with_d5', '1' );
update_post_meta( $post_id, '_et_builder_version', DIVI_BUILDER_VERSION );

WP_CLI::success( "Header layout {$post_id} updated successfully!" );
