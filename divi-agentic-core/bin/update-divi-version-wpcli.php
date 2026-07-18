<?php
/**
 * WP-CLI one-off command: migrate stored _et_builder_version from 5.5.0 to 5.7.4.
 */
if ( ! defined( 'WP_CLI' ) ) {
    return;
}

\WP_CLI::add_command( 'agentic update_divi_version', function( $args, $assoc_args ) {
    $version = $args[0] ?? DIVI_BUILDER_VERSION;
    $clean_version = preg_replace( '/^VB\|Divi\|/', '', $version );

    $post_types = [ 'page', 'et_template', 'et_header_layout', 'et_body_layout', 'et_footer_layout', 'et_pb_layout', 'project' ];
    $updated = 0;

    foreach ( $post_types as $pt ) {
        $posts = get_posts( array(
            'post_type'      => $pt,
            'posts_per_page' => -1,
            'post_status'    => 'any',
            'fields'         => 'ids',
        ) );
        foreach ( $posts as $id ) {
            $v = get_post_meta( $id, '_et_builder_version', true );
            if ( $v && ( strpos( $v, '5.5.0' ) !== false || $v === '5.5.0' ) ) {
                update_post_meta( $id, '_et_builder_version', 'VB|Divi|' . $clean_version );
                \WP_CLI::log( "Updated post {$id} ({$pt}) to VB|Divi|{$clean_version}" );
                $updated++;
            }
        }
    }

    \WP_CLI::success( "Done. Updated {$updated} posts." );
} );
