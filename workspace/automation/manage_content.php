<?php
/**
 * manage_content.php - Gestor de Estado de Contenido (Ultra-Eficiente)
 * Instituto Ramón López Velarde
 */

$options = getopt("", ["mode:"]);
$mode = $options['mode'] ?? 'remote';
$base_dir = dirname(__DIR__) . '/content_state/';
$target_dir = ($mode === 'remote') ? $base_dir . 'remote/' : $base_dir . 'local/';

if (!is_dir($target_dir)) mkdir($target_dir, 0777, true);

echo "--- MODO: " . strtoupper($mode) . " ---\n";

if ($mode === 'local') {
    echo "Extrayendo snapshot local (Arranque Único)...\n";
    $cmd = '.\wp.bat post list --post_type=page,post,et_pb_layout,et_header_layout,et_footer_layout --fields=ID,post_name,post_content,post_modified --format=json';
    $output = shell_exec($cmd);
    
    // Clean output: extract only the valid JSON array part
    $start = strpos($output, '[');
    $end = strrpos($output, ']');
    if ($start !== false && $end !== false) {
        $json_clean = substr($output, $start, $end - $start + 1);
    } else {
        $json_clean = $output;
    }
    
    $data = json_decode($json_clean, true);
    
    if (!$data) {
        echo "Error detail: " . json_last_error_msg() . "\n";
        echo "Raw output was: " . substr($output, 0, 500) . "...\n";
        die("Error: No se pudo obtener datos locales o el formato JSON es inválido.\n");
    }

    $manifest = [];
    foreach ($data as $p) {
        $slug = $p['post_name'];
        if (empty($slug)) {
            $slug = 'id-' . $p['ID'];
        }
        file_put_contents($target_dir . $slug . '.txt', $p['post_content']);
        $manifest[] = [
            'id' => $p['ID'], 
            'slug' => $slug, 
            'modified' => $p['post_modified']
        ];
        echo " > Snap: $slug.txt\n";
    }
    file_put_contents($target_dir . 'manifest.json', json_encode($manifest, JSON_PRETTY_PRINT));
    echo "\nSnapshot local completado: " . count($manifest) . " archivos generados.\n";

} else {
    echo "Consultando producción (MySQL Remote)...\n";
    $sep = "|||SEP|||";
    // Forzamos UTF-8 en la conexión y en la extracción
    $query = "SET NAMES utf8mb4; SELECT CONCAT(post_title, '$sep', post_name, '$sep', REPLACE(REPLACE(post_content, '\r', ''), '\n', '[[BR]]'), '$sep', post_type, '$sep', post_status) FROM fxr_posts WHERE post_type IN ('page', 'post', 'et_pb_layout', 'et_header_layout', 'et_footer_layout') AND post_status = 'publish'";
    
    $sql_file = __DIR__ . '/r.sql';
    $out_file = __DIR__ . '/r.out';
    file_put_contents($sql_file, $query);
    
    // Usamos redirección a archivo para evitar problemas de encoding en shell_exec de Windows
    shell_exec('.\mysql_remote.bat -N -s -r --default-character-set=utf8mb4 < ' . escapeshellarg($sql_file) . ' > ' . escapeshellarg($out_file));
    $remote_raw = file_get_contents($out_file);
    
    if (file_exists($sql_file)) unlink($sql_file);
    if (file_exists($out_file)) unlink($out_file);

    if (!$remote_raw) {
        die("Error: No se recibió respuesta de producción.\n");
    }

    $remote_posts = [];
    $lines = explode("\n", trim($remote_raw));
    foreach ($lines as $line) {
        $line = trim($line);
        $parts = explode($sep, $line);
        if (count($parts) < 5) continue;
        
        $slug = $parts[1];
        if (empty($slug)) {
            $slug = strtolower(trim(preg_replace('/[^A-Za-z0-9-]+/', '-', $parts[0]), '-'));
            if (empty($slug)) continue; 
        }

        $content = str_replace('[[BR]]', "\n", $parts[2]);
        $remote_posts[] = [
            'title' => $parts[0], 
            'slug' => $slug, 
            'content' => base64_encode($content), // Encode content to avoid escaping issues
            'type' => $parts[3], 
            'status' => $parts[4]
        ];
        
        file_put_contents($target_dir . $slug . '.txt', $content);
    }

    echo "Sincronizando " . count($remote_posts) . " posts con DB Local vía eval-file (Safe Mode)...\n";
    
    $payload_file = __DIR__ . '/sync_payload.json';
    file_put_contents($payload_file, json_encode($remote_posts, JSON_UNESCAPED_UNICODE));

    $eval_code = '<?php
        global $wpdb;
        $file = $args[0];
        $posts = json_decode(file_get_contents($file), true);
        foreach ($posts as $p) {
            $content = base64_decode($p["content"]);
            $hex_content = "0x" . bin2hex($content);
            $table = $wpdb->prefix . "posts";
            
            $existing_id = $wpdb->get_var($wpdb->prepare(
                "SELECT ID FROM $table WHERE post_name = %s AND post_type = %s LIMIT 1",
                $p["slug"], $p["type"]
            ));

            if ($existing_id) {
                $wpdb->query($wpdb->prepare(
                    "UPDATE $table SET post_title = %s, post_content = $hex_content, post_status = %s, post_modified = %s, post_modified_gmt = %s WHERE ID = %d",
                    $p["title"], $p["status"], current_time("mysql"), current_time("mysql", 1), $existing_id
                ));
                echo " [UPDATED] " . $p["slug"] . "\n";
            } else {
                $wpdb->query($wpdb->prepare(
                    "INSERT INTO $table (post_title, post_name, post_content, post_type, post_status, post_modified, post_modified_gmt) VALUES (%s, %s, $hex_content, %s, %s, %s, %s)",
                    $p["title"], $p["slug"], $p["type"], $p["status"], current_time("mysql"), current_time("mysql", 1)
                ));
                echo " [CREATED] " . $p["slug"] . "\n";
            }
            
            clean_post_cache($existing_id);
        }
    ';
    
    $eval_file = __DIR__ . '/sync_logic.php';
    file_put_contents($eval_file, $eval_code);
    
    // Ejecutar todo en un solo bootstrap de WP
    passthru('.\wp.bat eval-file ' . escapeshellarg($eval_file) . ' ' . escapeshellarg($payload_file));
    
    if (file_exists($eval_file)) unlink($eval_file);
    if (file_exists($payload_file)) unlink($payload_file);

    echo "\nSincronización remota completada.\n";
}
