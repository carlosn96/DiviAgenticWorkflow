<?php
/**
 * push_to_remote.php - Despliegue seguro de contenidos a Producción (SiteGround)
 * Genera un payload SQL hexadecimal para garantizar integridad total.
 */

$options = getopt("", ["slug:", "dir:"]);
$target_slug = $options['slug'] ?? null;
$dir_name = $options['dir'] ?? 'local';
$dir = dirname(__DIR__) . '/content_state/' . $dir_name . '/';

if (!is_dir($dir)) {
    die("Error: El directorio $dir no existe.\n");
}

echo "--- PREPARANDO DESPLIEGUE A PRODUCCIÓN ---\n";
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
    
    // Actualizamos por slug (post_name) en la tabla fxr_posts
    $sql_content .= "UPDATE fxr_posts SET ";
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
echo "¿Deseas proceder con el despliegue? (ejecutar manualmente o pedir al agente)\n";
