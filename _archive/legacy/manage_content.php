<?php
/**
 * manage_content.php - Gestor de Estado de Contenido LOCAL
 * 
 * Uso: .\php.bat DAW_bundle\workspace\automation\manage_content.php [--mode=local]
 * 
 * Extrae un snapshot del contenido local de WordPress (pages, posts, layouts)
 * y lo guarda en site/<DAW_SITE>/content_state/local/ como archivos .txt.
 */

$site = getenv('DAW_SITE');

function load_dotenv_file($path)
{
    $result = [];
    if (!is_readable($path)) return $result;
    $lines = file($path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    foreach ($lines as $line) {
        $line = trim($line);
        if ($line === '' || $line[0] === '#') continue;
        if (strpos($line, '=') === false) continue;
        list($name, $value) = explode('=', $line, 2);
        $name = trim($name);
        $value = trim($value);
        $len = strlen($value);
        if ($len >= 2) {
            $first = $value[0];
            $last = $value[$len - 1];
            if (($first === '"' && $last === '"') || ($first === "'" && $last === "'")) {
                $value = substr($value, 1, $len - 2);
            }
        }
        $result[$name] = $value;
    }
    return $result;
}

if (!$site) {
    $env_path = dirname(__DIR__, 3) . '/.env';
    if (is_readable($env_path)) {
        echo "Cargando variables desde .env ($env_path)...\n";
        $env_vars = load_dotenv_file($env_path);
        if (!empty($env_vars['DAW_SITE'])) {
            $site = $env_vars['DAW_SITE'];
            putenv("DAW_SITE={$site}");
            $_ENV['DAW_SITE'] = $site;
            $_SERVER['DAW_SITE'] = $site;
        }
    }
}

if (!$site) {
    die("Error: La variable de entorno DAW_SITE no está definida. Por favor, configúrala antes de ejecutar el script.\n");
}


$target_dir = dirname(__DIR__, 2) . "/site/{$site}/content_state/local/";
if (!is_dir($target_dir)) mkdir($target_dir, 0777, true);

echo "--- MODO: LOCAL ---\n";
echo "Extrayendo snapshot local desde WordPress...\n";
$cmd = '.\wp.bat post list --post_type=page,post,et_pb_layout,et_header_layout,et_footer_layout --fields=ID,post_name,post_content,post_modified --format=json';
$output = shell_exec($cmd);

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
    echo " > Snap: $site/$slug.txt\n";
}
file_put_contents($target_dir . 'manifest.json', json_encode($manifest, JSON_PRETTY_PRINT));
echo "\nSnapshot local completado: " . count($manifest) . " archivos generados.\n";
