<?php
$dir_local = 'c:/Users/CORE I9/Local Sites/institutoramonlopezvelarde-migracion/workspace/content_state/local/';
$dir_remote = 'c:/Users/CORE I9/Local Sites/institutoramonlopezvelarde-migracion/workspace/content_state/remote/';
$directories = [$dir_local, $dir_remote];
$files = [];
foreach ($directories as $d) {
    $files = array_merge($files, glob($d . '*.txt'));
}


$replacements = [
    // La lista exacta del usuario
    'Comunicate' => 'Comun\u00edcate',
    'Direcci??n' => 'Direcci\u00f3n',
    'Direccion' => 'Direcci\u00f3n',
    'Tel??fono' => 'Tel\u00e9fono',
    'Telefono' => 'Tel\u00e9fono',
    'Escribenos' => 'Escr\u00edbenos',
    'Env??a' => 'Env\u00eda',
    'Envia' => 'Env\u00eda',
    'D??janos' => 'D\u00e9janos',
    'Dejanos' => 'D\u00e9janos',
    'electr??nico' => 'electr\u00f3nico',
    'electronico' => 'electr\u00f3nico',
    'Tambi??n' => 'Tambi\u00e9n',
    'Tambien' => 'Tambi\u00e9n',
    'Ubicaci??n' => 'Ubicaci\u00f3n',
    'Ubicacion' => 'Ubicaci\u00f3n',
    'Encu??ntranos' => 'Encu\u00e9ntranos',
    'Encuentranos' => 'Encu\u00e9ntranos',
    'Ll??manos ahora' => 'Ll\u00e1manos ahora',
    'Llamanos ahora' => 'Ll\u00e1manos ahora',
    
    // Corrupciones comunes detectadas en el grep
    '??Tienes' => '\u00bfTienes',
    '??Listo' => '\u00bfListo',
    'Acad¿mico' => 'Acad\u00e9mico',
    'Categor¿as' => 'Categor\u00edas',
    'psicopedagogia' => 'psicopedagog\u00eda',
    'acompanamiento' => 'acompa\u00f1amiento',
    'formacion' => 'formaci\u00f3n',
    'informacion' => 'informaci\u00f3n',
    // New corrections for garbled UTF‑8 sequences
    'Â·' => '·',
    'FormaciÃ³n' => 'Formaci\u00f3n',
    'acadÃ©mico' => 'acad\u00e9mico',
    'RamÃ³n' => 'Ram\u00f3n',
    'LÃ³pez' => 'L\u00f3pez',
    'preparaciÃ³n' => 'preparaci\u00f3n',
    'AÃ±os' => 'A\u00f1os',
    'Descubre mÃ¡s' => 'Descubre m\u00e1s',
    'CurrÃ­culo' => 'Curr\u00edculo'
];

echo "Iniciando limpieza masiva en " . count($files) . " archivos...\n";

foreach ($files as $file) {
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
