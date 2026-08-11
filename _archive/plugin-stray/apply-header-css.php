<?php
$page_id = 121485;
$css_path = 'C:\Users\Departamento WEB\Local Sites\sanpablo-mx\DAW_bundle\site\sanpablo\page-defs\header-principal.css';
$css = file_get_contents($css_path);

update_post_meta($page_id, '_et_pb_custom_css', $css);
WP_CLI::success("Updated page $page_id meta _et_pb_custom_css (" . strlen($css) . " chars)");
