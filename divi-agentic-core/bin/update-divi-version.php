<?php
/**
 * One-off updater: migrates stored _et_builder_version from 5.5.0 to 5.7.4.
 */

if ( ! class_exists( '\WP_CLI' ) ) {
    define( 'WP_CLI', true );
}

require_once __DIR__ . '/../../../../app/public/wp-load.php';

$version = $argv[1] ?? ( defined( 'DIVI_BUILDER_VERSION' ) ? DIVI_BUILDER_VERSION : '5.7.4' );
$clean_version = preg_replace( '/^VB\|Divi\|/', '', $version );

$post_types = [ 'page', 'et_template', 'et_header_layout', 'et_body_layout', 'et_footer_layout', 'et_pb_layout', 'project' ];
$updated = 0;

foreach ( $post_types as $pt ) {
    $posts = get_posts( [
        'post_type'      => $pt,
        'posts_per_page' => -1,
        'post_status'    => 'any',
        'fields'         => 'ids',
    ] );
    foreach ( $posts as $id ) {
        $v = get_post_meta( $id, '_et_builder_version', true );
        if ( $v && ( strpos( $v, '5.5.0' ) !== false || $v === '5.5.0' ) ) {
            update_post_meta( $id, '_et_builder_version', 'VB|Divi|' . $clean_version );
            echo "Updated post {$id} ({$pt}) to VB|Divi|{$clean_version}\n";
            $updated++;
        }
    }
}

echo "Done. Updated {$updated} posts.\n";
