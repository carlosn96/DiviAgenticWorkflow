<?php
/**
 * create_page_remote.php - Genera un script SQL para CREAR una página en producción.
 */
$options = getopt("", ["slug:", "title:"]);
$slug = $options['slug'] ?? die("Error: --slug es requerido.\n");
$title = $options['title'] ?? ucfirst($slug);
$content_file = dirname(__DIR__) . '/content_state/local/' . $slug . '.txt';

if (!file_exists($content_file)) die("Error: $slug.txt no encontrado.\n");

$content = file_get_contents($content_file);
$hex_content = '0x' . bin2hex($content);
$hex_title = '0x' . bin2hex($title);

$sql = "SET NAMES utf8mb4;\n";

// 1. Insertar el post
$sql .= "INSERT INTO fxr_posts (post_author, post_date, post_date_gmt, post_content, post_title, post_status, comment_status, ping_status, post_name, post_modified, post_modified_gmt, post_type, post_mime_type) \n";
$sql .= "VALUES (1, NOW(), UTC_TIMESTAMP(), $hex_content, $hex_title, 'publish', 'closed', 'closed', '$slug', NOW(), UTC_TIMESTAMP(), 'page', '');\n";

// 2. Obtener el ID insertado (usando una variable de MySQL)
$sql .= "SET @last_id = LAST_INSERT_ID();\n";

// 3. Insertar metadatos Pro
$meta = [
    '_et_pb_use_builder' => 'on',
    '_et_pb_use_divi_5' => 'on',
    '_et_pb_page_layout' => 'et_full_width',
    '_et_pb_show_title' => 'off',
    '_et_builder_version' => '5.5.0'
];

foreach ($meta as $key => $val) {
    $sql .= "INSERT INTO fxr_postmeta (post_id, meta_key, meta_value) VALUES (@last_id, '$key', '$val');\n";
}

file_put_contents("create_{$slug}_remote.sql", $sql);
echo "SQL de creación generado: create_{$slug}_remote.sql\n";
