<?php
// Script mejorado para soportar rutas relativas y extensiones personalizadas
$scan_dir = isset($argv[1]) ? realpath($argv[1]) : dirname(__DIR__, 2);
$ext_list = isset($argv[2]) ? explode(',', $argv[2]) : ['txt', 'md', 'php', 'json', 'csv', 'yml'];

if (!$scan_dir || !is_dir($scan_dir)) {
    die("Directorio no valido\n");
}

$files = [];
$iterator = new RecursiveIteratorIterator(new RecursiveDirectoryIterator($scan_dir));
foreach ($iterator as $file) {
    if ($file->isFile() && in_array(strtolower($file->getExtension()), $ext_list)) {
        $path = $file->getPathname();
        // Evitar escanear dependencias y git
        if (preg_match('/(\\\\|\/)(\.git|node_modules|vendor)(\\\\|\/)/i', $path)) continue;
        $files[] = $path;
    }
}

$replacements = [
    'Comunicate' => 'Comunícate',
    'Direcci??n' => 'Dirección',
    'Direccion' => 'Dirección',
    'Tel??fono' => 'Teléfono',
    'Telefono' => 'Teléfono',
    'Escribenos' => 'Escríbenos',
    'Env??a' => 'Envía',
    'Envia' => 'Envía',
    'D??janos' => 'Déjanos',
    'Dejanos' => 'Déjanos',
    'electr??nico' => 'electrónico',
    'electronico' => 'electrónico',
    'Tambi??n' => 'También',
    'Tambien' => 'También',
    'Ubicaci??n' => 'Ubicación',
    'Ubicacion' => 'Ubicación',
    'Encu??ntranos' => 'Encuéntranos',
    'Encuentranos' => 'Encuéntranos',
    'Ll??manos ahora' => 'Llámanos ahora',
    'Llamanos ahora' => 'Llámanos ahora',
    '??Tienes' => '¿Tienes',
    '??Listo' => '¿Listo',
    'Acadómo' => 'Académico',
    'Categorías' => 'Categorías',
    'psicopedagogia' => 'psicopedagogía',
    'acompanamiento' => 'acompañamiento',
    'formacion' => 'formación',
    'informacion' => 'información',
    
    // Core UTF-8 Mojibake corrections 
    'Ã¡' => 'á',
    'Ã©' => 'é',
    'Ã­' => 'í',
    'Ã³' => 'ó',
    'Ãº' => 'ú',
    'Ã±' => 'ñ',
    'ÃA' => 'Á',
    'Ã‰' => 'É',
    'ÃM' => 'Í',
    'Ã“' => 'Ó',
    'Ãš' => 'Ú',
    'Ã‘' => 'Ñ',
    'Â¿' => '¿',
    'Â¡' => '¡',
    'Â·' => '·'
];

echo "Iniciando limpieza masiva en el directorio $scan_dir para " . count($files) . " archivos...\n";

foreach ($files as $file) {
    if (realpath($file) === realpath(__FILE__)) continue; // No autolimpiarse
    
    $content = file_get_contents($file);
    $original = $content;
    
    foreach ($replacements as $search => $replace) {
        $content = str_replace($search, $replace, $content);
    }
    
    if ($content !== $original) {
        file_put_contents($file, $content);
        echo " > Corregido: " . basename($file) . "\n";
    }
}

echo "Limpieza masiva completada.\n";
