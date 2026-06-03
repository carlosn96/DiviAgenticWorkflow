<?php
/**
 * create_page_remote.php - Genera script SQL para crear página en REMOTO
 * 
 * DEPRECATED: Este script genera SQL para base de datos remota (prefijo fxr_).
 * Para trabajo local, usar: .\wp.bat agentic deploy_page
 * 
 * Uso: .\php.bat DAW_bundle\workspace\automation\create_page_remote.php --slug=mi-pagina --title="Mi Página"
 */

$options = getopt("", ["slug:", "title:"]);
$slug = $options['slug'] ?? die("Error: --slug es requerido.\n");
$title = $options['title'] ?? ucfirst($slug);
$site = getenv('DAW_SITE') ?: 'bibliotheca';
$content_file = dirname(__DIR__, 2) . "/site/{$site}/content_state/local/{$slug}.txt";

if (!file_exists($content_file)) die("Error: $slug.txt no encontrado en content_state/local/.\n");

$content = file_get_contents($content_file);
$hex_content = '0x' . bin2hex($content);
$hex_title = '0x' . bin2hex($title);
$table_prefix = getenv('DAW_DB_TABLE_PREFIX') ?: 'fxr_';

echo "--- GENERANDO SQL PARA REMOTO (prefijo: {$table_prefix}) ---\n";
echo "ADVERTENCIA: Esto genera SQL para una base de datos remota.\n";
echo "Para trabajo local usa: .\\wp.bat agentic deploy_page\n\n";

$sql = "SET NAMES utf8mb4;\n";
$sql .= "INSERT INTO {$table_prefix}posts (post_author, post_date, post_date_gmt, post_content, post_title, post_status, comment_status, ping_status, post_name, post_modified, post_modified_gmt, post_type, post_mime_type) \n";
$sql .= "VALUES (1, NOW(), UTC_TIMESTAMP(), $hex_content, $hex_title, 'publish', 'closed', 'closed', '$slug', NOW(), UTC_TIMESTAMP(), 'page', '');\n";
$sql .= "SET @last_id = LAST_INSERT_ID();\n";

$meta = [
    '_et_pb_use_builder' => 'on',
    '_et_pb_use_divi_5' => 'on',
    '_et_pb_page_layout' => 'et_full_width',
    '_et_pb_show_title' => 'off',
    '_et_builder_version' => '5.5.0'
];

foreach ($meta as $key => $val) {
    $sql .= "INSERT INTO {$table_prefix}postmeta (post_id, meta_key, meta_value) VALUES (@last_id, '$key', '$val');\n";
}

$out_file = "create_{$slug}_remote.sql";
file_put_contents($out_file, $sql);
echo "SQL de creación generado: $out_file\n";
echo "Para aplicar: .\\mysql_remote.bat < $out_file\n";
