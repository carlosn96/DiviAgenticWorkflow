<?php
/**
 * push_to_remote.php - Exportador de contenidos para despliegue remoto
 * 
 * DEPRECATED: Para despliegue local usa .\wp.bat agentic deploy_page
 * Este script genera payload SQL para base de datos remota.
 * 
 * Uso: .\php.bat DAW_bundle\workspace\automation\push_to_remote.php [--slug=mi-pagina] [--dir=local]
 */

$options = getopt("", ["slug:", "dir:"]);
$target_slug = $options['slug'] ?? null;
$dir_name = $options['dir'] ?? 'local';
$site = getenv('DAW_SITE') ?: 'bibliotheca';
$dir = dirname(__DIR__, 2) . "/site/{$site}/content_state/{$dir_name}/";
$table_prefix = getenv('DAW_DB_TABLE_PREFIX') ?: 'fxr_';

if (!is_dir($dir)) {
    die("Error: El directorio $dir no existe.\n");
}

echo "--- PREPARANDO DESPLIEGUE A PRODUCCIÓN (prefijo: {$table_prefix}) ---\n";
echo "ADVERTENCIA: Esto genera SQL para base de datos REMOTA.\n";
echo "Para trabajo local usa: .\\wp.bat agentic deploy_page\n\n";
echo "Origen: Carpeta '$dir_name'\n";

if ($target_slug) {
    echo "Objetivo: Solo slug '$target_slug'\n";
    $files = glob($dir . '*.txt');
    $files = array_filter($files, function($f) use ($target_slug) {
        return basename($f, '.txt') === $target_slug;
    });
} else {
    echo "Objetivo: Todos los volcados en '$dir_name'\n";
    $files = glob($dir . '*.txt');
}

if (empty($files)) {
    die("Error: No se encontraron archivos .txt para procesar.\n");
}

echo "Leyendo archivos...\n";

$sql_content = "SET NAMES utf8mb4;\n";
$timestamp = date('Y_m_d_H_i_s');
$payload_file = __DIR__ . '/push_payload_' . $timestamp . '.sql';
$latest_file = __DIR__ . '/push_payload_latest.sql';

foreach ($files as $file) {
    $slug = basename($file, '.txt');
    $content = file_get_contents($file);
    $hex_content = '0x' . bin2hex($content);
    
    echo " > Procesando Payload: $slug\n";
    
    $sql_content .= "UPDATE {$table_prefix}posts SET ";
    $sql_content .= "post_content = $hex_content, ";
    $sql_content .= "post_modified = NOW(), ";
    $sql_content .= "post_modified_gmt = UTC_TIMESTAMP() ";
    $sql_content .= "WHERE post_name = '$slug' AND post_status = 'publish';\n";
}

file_put_contents($payload_file, $sql_content);
file_put_contents($latest_file, $sql_content);

echo "\nPayloads generados en:\n";
echo " > Timestamped: $payload_file\n";
echo " > Latest ref: $latest_file\n";
echo "--------------------------------------------------\n";
echo "ADVERTENCIA: Estás a punto de actualizar la base de datos de PRODUCCIÓN.\n";
echo "Comando a ejecutar:\n";
echo " .\\mysql_remote.bat < workspace\\automation\\push_payload_latest.sql\n";
echo "--------------------------------------------------\n";
