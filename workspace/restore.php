<?php
$rev = get_post(428);
$raw = $rev->post_content;

global $wpdb;
// Direct escape via quotes only
$safe = str_replace(["\\", "'"], ["\\\\", "\\'"], $raw);
$sql = "UPDATE {$wpdb->posts} SET post_content = '{$safe}' WHERE ID = 95";
$r = $wpdb->query($sql);

if ($r === false) {
    echo 'ERR: ' . $wpdb->last_error;
} else {
    echo 'OK:' . $r;
    clean_post_cache(95);
}
