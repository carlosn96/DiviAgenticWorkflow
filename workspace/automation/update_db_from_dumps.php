<?php
/**
 * update_db_from_dumps.php - Actualiza la DB Local desde archivos .txt
 * Uso: 
 *   .\php.bat workspace\automation\update_db_from_dumps.php --dir=local
 *   .\php.bat workspace\automation\update_db_from_dumps.php --dir=remote
 */

$options = getopt("", ["dir:", "slug:"]);
$dir_name = $options['dir'] ?? 'local';
$target_slug = $options['slug'] ?? null;
$target_dir = dirname(__DIR__) . '/content_state/' . $dir_name . '/';

if (!is_dir($target_dir)) {
    die("Error: El directorio $target_dir no existe.\n");
}

echo "--- Actualizando DB Local desde: " . strtoupper($dir_name) . " ---\n";
if ($target_slug) echo "Objetivo: Solo slug '$target_slug'\n";

// 1. Preparar lista de archivos y contenidos
$files = glob($target_dir . '*.txt');
if ($target_slug) {
    $files = array_filter($files, function($f) use ($target_slug) {
        return basename($f, '.txt') === $target_slug;
    });
}
$payload = [];

echo "Leyendo archivos...\n";
foreach ($files as $file) {
    $slug = basename($file, '.txt');
    $content = file_get_contents($file);
    
    $payload[] = [
        'slug' => $slug,
        'content' => base64_encode($content) // Evitamos problemas de escape en el transporte JSON
    ];
    echo " > Preparado para inyectar: $slug.txt\n";
}

if (empty($payload)) {
    die("No se encontraron archivos .txt para procesar.\n");
}

// 2. Ejecutar actualización masiva vía WP-CLI
$payload_file = __DIR__ . '/update_payload.json';
file_put_contents($payload_file, json_encode($payload));

$eval_code = '<?php
    global $wpdb;
    $table = $wpdb->prefix . "posts";
    $file_path = $args[0];
    $data = json_decode(file_get_contents($file_path), true);
    
    if (!$data) {
        echo "Error: No se pudo decodificar el payload JSON.\n";
        return;
    }

    foreach ($data as $item) {
        $slug = $item["slug"];
        $content = base64_decode($item["content"]);
        $hex_content = "0x" . bin2hex($content);
        
        // Buscamos el ID por el slug (post_name)
        // Intentamos en pages, posts y layouts
        $post_id = $wpdb->get_var($wpdb->prepare(
            "SELECT ID FROM $table WHERE post_name = %s LIMIT 1", 
            $slug
        ));

        if ($post_id) {
            // Actualización directa vía SQL para evitar filtros que puedan corromper el contenido
            $result = $wpdb->query($wpdb->prepare(
                "UPDATE $table SET post_content = $hex_content, post_modified = %s, post_modified_gmt = %s WHERE ID = %d",
                current_time("mysql"), current_time("mysql", 1), $post_id
            ));
            
            clean_post_cache($post_id);
            echo " [OK] Actualizado ID $post_id ($slug)\n";
        } else {
            echo " [SKIP] No se encontró el slug: $slug en la DB local\n";
        }
    }
';

$eval_file = __DIR__ . '/update_eval.php';
file_put_contents($eval_file, $eval_code);

echo "\nIniciando inyección en base de datos local (Modo Hex-Safe)...\n";
passthru('.\wp.bat eval-file ' . escapeshellarg($eval_file) . ' ' . escapeshellarg($payload_file));

// Limpieza de temporales
if (file_exists($payload_file)) unlink($payload_file);
if (file_exists($eval_file)) unlink($eval_file);

echo "\nProceso finalizado.\n";
