<?php
/**
 * extract_page.php — Extrae una página de WordPress por slug o ID
 *                  y la guarda estructurada junto al manifest.
 *
 * Uso:
 *   .\php.bat DAW_bundle\workspace\automation\extract_page.php <manifest> [--id=<ID>]
 *
 * Ejemplos:
 *   .\php.bat "DAW_bundle/site/sanpablo/references/Semana biblica/semana-biblica-2026.json"
 *   .\php.bat extract_page.php manifest.json --id=127774
 */

$args = array_slice($argv, 1);

if (empty($args) || in_array($args[0], ['-h', '--help', '/?'], true)) {
echo "Uso: .\\php.bat DAW_bundle\\workspace\\automation\\extract_page.php <manifest> [--id=<ID>]\n\n";
echo "  <manifest>    Ruta al manifest JSON de la p&aacute;gina.\n";
echo "                Relativo a la ra&iacute;z del proyecto (donde est&aacute; wp.bat).\n";
echo "  --id=<ID>     Opcional. ID num&eacute;rico de la p&aacute;gina (sobrescribe el slug del manifest).\n\n";
echo "Ejemplos:\n";
echo "  .\\php.bat \"DAW_bundle/site/sanpablo/references/Semana biblica/semana-biblica-2026.json\"\n";
echo "  .\\php.bat DAW_bundle\\workspace\\automation\\extract_page.php \"DAW_bundle/site/sanpablo/references/Semana biblica/semana-biblica-2026.json\" --id=127774\n";
    exit(0);
}

$manifest_path = $args[0];
$explicit_id   = null;

for ($i = 1; $i < count($args); $i++) {
    if (str_starts_with($args[$i], '--id=')) {
        $explicit_id = (int) substr($args[$i], 5);
    }
}

if (!is_readable($manifest_path)) {
    die("Error: No se encuentra el manifest en: $manifest_path\n");
}

$manifest = json_decode(file_get_contents($manifest_path), true);
if (!$manifest || !isset($manifest['_manifest'])) {
    die("Error: El archivo no es un manifest DAW v&aacute;lido (falta '_manifest').\n");
}

$slug  = $manifest['slug'] ?? '';
$title = $manifest['title'] ?? 'Sin t&iacute;tulo';

if (empty($slug) && !$explicit_id) {
    die("Error: El manifest no tiene 'slug' y no se proporcion&oacute; --id.\n");
}

$base_dir     = dirname(realpath($manifest_path));
$out_dir      = $base_dir . '/content_state';

if (!is_dir($out_dir)) {
    mkdir($out_dir, 0777, true);
}

// ─── Ruta relativa al proyecto ──────────────────────────────────────
$project_root = dirname(realpath($manifest_path));
for ($i = 0; $i < 15; $i++) {
    if (file_exists($project_root . '/wp.bat')) {
        break;
    }
    $project_root = dirname($project_root);
}

// ─── Obtener post ID ─────────────────────────────────────────────────
$post_id = $explicit_id;

if (!$post_id) {
    $cmd = sprintf(
        '.\\wp.bat post list --post_type=page --name=%s --field=ID --format=json 2>NUL',
        escapeshellarg($slug)
    );
    $output = trim(shell_exec($cmd));
    $ids = json_decode($output, true);

    if (is_array($ids) && count($ids) === 1) {
        $post_id = (int) $ids[0];
    } elseif (is_numeric($output)) {
        $post_id = (int) $output;
    }
}

if (!$post_id || $post_id <= 0) {
    die("Error: No se encontr&oacute; p&aacute;gina con slug '$slug' en WordPress.\n  Usa --id=<ID> para especificar el ID directamente.\n");
}

echo "P&aacute;gina:  $title\n";
echo "Slug:    $slug\n";
echo "ID:      $post_id\n\n";

// ─── Extraer post con WP-CLI (formato JSON) ──────────────────────────
$cmd = sprintf('.\\wp.bat post get %d --format=json 2>NUL', $post_id);
$output   = trim(shell_exec($cmd));
$post     = json_decode($output, true);
$content_raw = '';
$modified    = '';

if (!$post || !isset($post['post_content'])) {
    $content_raw = trim($output) !== '' ? $output : '';
} else {
    $content_raw = $post['post_content'] ?? '';
    $modified    = $post['post_modified'] ?? '';
}

$filename = $slug ?: "page-{$post_id}";

// Save post_content
$content_raw = trim($content_raw);
$txt_path    = $out_dir . '/' . $filename . '.txt';
file_put_contents($txt_path, $content_raw);

$rel_path = substr(realpath($txt_path), strlen($project_root) + 1);

echo " ✔ $rel_path";
if ($content_raw) {
    echo " (" . strlen($content_raw) . " bytes)";
}
echo "\n";

// ─── Extraer metas ──────────────────────────────────────────────────
$cmd = sprintf(
    '.\\wp.bat post meta list %d --keys=_et_pb_built_with_d5,_et_builder_version,_et_pb_custom_css,_wp_page_template --format=json 2>NUL',
    $post_id
);
$meta_output = trim(shell_exec($cmd));
$meta_list   = json_decode($meta_output, true);

$meta = ['id' => $post_id, 'slug' => $slug, 'title' => $title];

if (is_array($meta_list)) {
    foreach ($meta_list as $entry) {
        $key = $entry['meta_key'] ?? '';
        $val = $entry['meta_value'] ?? '';
        switch ($key) {
            case '_et_pb_built_with_d5': $meta['built_with_d5'] = $val; break;
            case '_et_builder_version':  $meta['builder_version'] = $val; break;
            case '_et_pb_custom_css':    $meta['custom_css'] = $val; break;
            case '_wp_page_template':    $meta['template'] = $val; break;
        }
    }
}

$meta_path = $out_dir . '/' . $filename . '-meta.json';
file_put_contents(
    $meta_path,
    json_encode($meta, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE)
);
$rel_meta = substr(realpath($meta_path), strlen($project_root) + 1);
echo " ✔ $rel_meta\n";

if ($modified) {
    echo "   Última modificaci&oacute;n: $modified\n";
}

echo "\n✅ Extracción completada.\n";
