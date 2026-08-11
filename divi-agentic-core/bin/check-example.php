<?php
/**
 * check-example.php — Mantiene el template de marcas (site/example) sincronizado
 * con Token_Registry, y opcionalmente valida un site productivo contra el registry.
 *
 * Mecanismo ejecutable (no documental) que asegura consistencia del pipeline:
 *
 *   1. Las keys de brand/_design_vars.json del site objetivo coinciden EXACTAMENTE
 *      con las que define Token_Registry (get_validation_schema — única fuente de verdad,
 *      + customizer_* slots, que no son tokens pero son parte del contrato del archivo).
 *      → Si se agrega/quita un token en Token_Registry, este check falla.
 *   2. (Solo para site/example) La estructura de carpetas coincide con la documentada
 *      en AGENTS.md (brand/, components/, content_state/, design-system/, page-defs/,
 *      references/) y no contiene dirs obsoletos (briefs/, pages/).
 *
 * Uso:
 *   php divi-agentic-core/bin/check-example.php                     # site/example (exit 0/1)
 *   php divi-agentic-core/bin/check-example.php --site=<slug>      # valida un site productivo
 *   php divi-agentic-core/bin/check-example.php --active           # valida el site activo (DAW_SITE/.env)
 *   php divi-agentic-core/bin/check-example.php <slug>             # forma corta de --site=
 *   php divi-agentic-core/bin/check-example.php --fix              # repara site/example (vars + estructura)
 *   php divi-agentic-core/bin/check-example.php --all              # site/example + site activo
 *
 * Exit code: 0 = OK, 1 = desincronizado (sin --fix).
 */

$bundle = dirname(dirname(__DIR__));

require_once $bundle . '/divi-agentic-core/inc/loader.php';

use DAC\Core\Token_Registry;

$argv = array_slice($argv, 1);
$fix        = in_array('--fix', $argv, true);
$all        = in_array('--all', $argv, true);
$active     = in_array('--active', $argv, true);
$site_arg   = null;

foreach ($argv as $a) {
    if (str_starts_with($a, '--site=')) {
        $site_arg = substr($a, strlen('--site='));
    } elseif (!str_starts_with($a, '-') && !$site_arg) {
        $site_arg = $a;
    }
}

// ── Expectativa: keys del schema completo (todos los tokens no-derived) ──
// get_validation_schema() incluye TODOS los tokens del registry (a diferencia
// de generate_scaffold(), que omite opcionales sin default). El ejemplo debe
// listar todas las keys que brand-sync entiende.
$expected_keys = array_keys(Token_Registry::get_validation_schema());
$defaults      = Token_Registry::get_defaults();

// customizer_* no son tokens del registry (los inyecta generate_scaffold y los
// lee Brand_Sync_Handler::sync_global_colors() vía get_customizer_slots()).
// Son parte del contrato de _design_vars.json → deben estar en el ejemplo.
$customizer_keys = array_map(fn($k) => 'customizer_' . $k, array_keys(Token_Registry::get_customizer_slots()));
$expected_keys   = array_values(array_unique(array_merge($expected_keys, $customizer_keys)));

// ── Valores de ejemplo curados (necesarios porque el scaffold deja null
//    en keys required sin default — un ejemplo debe tener valores reales). ──
$EXAMPLE_BASE = [
    'brand_name'             => 'Mi Marca',
    'brand_description'      => 'Descripción del proyecto',

    'color_accent'           => '#8B6F47',
    'color_accent_hover'     => '#6D5536',
    'color_ink'              => '#1C1A17',
    'color_ink_soft'         => '#2E2B26',
    'color_surface_deep'     => '#1C1A17',
    'color_surface_mid'      => '#2E2B26',
    'color_surface_light'    => '#F5F1E8',
    'color_surface_white'    => '#FCFAF5',
    'color_text_primary'     => '#1C1A17',
    'color_text_secondary'   => '#5C5244',
    'color_text_on_dark'     => '#FCFAF5',
    'color_success'          => '#3D6B4F',
    'color_error'            => '#8B3A3A',

    'font_display'           => "'Cormorant Garamond', Georgia, serif",
    'font_body'              => "'IBM Plex Sans', system-ui, sans-serif",
    'font_ui'                => "'IBM Plex Sans', system-ui, sans-serif",

    'customizer_primary'     => 'accent',
    'customizer_secondary'   => 'surface_mid',
    'customizer_heading'     => 'text_primary',
    'customizer_body'        => 'text_primary',
    'customizer_link'        => 'accent',
];

// ── Estructura esperada de site/example (AGENTS.md §1) ──
$EXPECTED_DIRS = ['brand', 'components', 'content_state', 'design-system', 'page-defs', 'references'];
$DROPPED_DIRS  = ['briefs', 'pages'];

/**
 * Valida un site: keys de _design_vars.json contra el expected_keys.
 * Returns: número de errores encontrados.
 */
function check_site_keys(string $site, string $bundle, array $expected_keys): int {
    $vars_path = $bundle . '/site/' . $site . '/brand/_design_vars.json';
    $vars = [];
    if (file_exists($vars_path)) {
        $raw = json_decode(file_get_contents($vars_path), true);
        if (json_last_error() === JSON_ERROR_NONE && is_array($raw)) {
            $vars = $raw;
        }
    }

    $missing = array_values(array_diff($expected_keys, array_keys($vars)));
    $extra   = array_values(array_diff(array_keys($vars), $expected_keys));
    $errors  = 0;

    echo "── site/{$site} vs Token_Registry ──\n";

    if (!file_exists($vars_path)) {
        echo "  [FAIL] Falta {$vars_path} (usa wp brand init <{$site}> o check --fix para example)\n";
        return 1;
    }

    if (!empty($missing)) {
        echo "  [FAIL] Keys faltantes (corrije o re-sincroniza):\n";
        foreach ($missing as $k) echo "         - {$k}\n";
        $errors++;
    }
    if (!empty($extra)) {
        echo "  [FAIL] Keys obsoletas (fuera del schema actual):\n";
        foreach ($extra as $k) echo "         - {$k}\n";
        $errors++;
    }
    if (empty($missing) && empty($extra)) {
        echo "  [OK]   _design_vars.json coincide con Token_Registry (" . count($expected_keys) . " keys)\n";
    }

    return $errors;
}

// ──────── Resolución de sites a validar ────────
$example_dir = $bundle . '/site/example';
$sites_to_check = [];

if ($site_arg) {
    $sites_to_check[] = $site_arg;
} elseif ($all || $active) {
    // site activo desde .env (DAW_SITE) o env var
    $env = getenv('DAW_SITE');
    if ($env === false) {
        $env_file = $bundle . '/../.env';
        if (file_exists($env_file)) {
            foreach (file($env_file, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) as $line) {
                if (str_starts_with(trim($line), 'DAW_SITE=')) {
                    $env = trim(substr(trim($line), strlen('DAW_SITE=')));
                    $env = trim($env, "\"'");
                    break;
                }
            }
        }
    }
    if (!$env) {
        fwrite(STDERR, "[ERROR] No se pudo determinar site activo (DAW_SITE). Usa --site=<slug>.\n");
        exit(1);
    }
    $sites_to_check[] = $env;
}

if (empty($sites_to_check)) {
    $sites_to_check[] = 'example';
}

// ──────── Acción nivel keys ────────
$total_errors = 0;
foreach ($sites_to_check as $site) {
    $total_errors += check_site_keys($site, $bundle, $expected_keys);
}

// ──────── Estructura (solo site/example) ────────
$is_example = in_array('example', $sites_to_check, true);

if ($fix && $is_example) {
    $vars_path = $example_dir . '/brand/_design_vars.json';
    $vars = [];
    if (file_exists($vars_path)) {
        $raw = json_decode(file_get_contents($vars_path), true);
        if (json_last_error() === JSON_ERROR_NONE && is_array($raw)) {
            $vars = $raw;
        }
    }
    $schema = Token_Registry::get_validation_schema();

    // 1. Reconstruir vars: base curada + valores actuales + defaults del registry.
    $merged = [];
    foreach ($expected_keys as $key) {
        // Prioridad: base curada → valor actual no vacío → default del registry.
        $value = $EXAMPLE_BASE[$key] ?? null;
        if ($value === null || $value === '') {
            $current = $vars[$key] ?? null;
            if ($current !== null && $current !== '') {
                $value = $current;
            }
        }
        if ($value === null || $value === '') {
            $value = $defaults[$key] ?? null;
        }
        // Keys required sin default real: forzar un valor curável si quedó null.
        if ($value === null && str_starts_with($key, 'color_')) {
            $value = '#CCCCCC';
        }
        // Keys tipo id sin valor → null (validate_vars espera null o número).
        if ($value === '' && ($schema[$key]['type'] ?? '') === 'id') {
            $value = null;
        }
        if ($value === null && ($schema[$key]['type'] ?? '') !== 'id') {
            $value = '';
        }
        $merged[$key] = $value;
    }

    if (!is_dir(dirname($vars_path))) {
        mkdir(dirname($vars_path), 0755, true);
    }
    file_put_contents(
        $vars_path,
        json_encode($merged, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES) . "\n"
    );
    echo "[FIX] _design_vars.json regenerado ({$vars_path})\n";

    // 2. Estructura: crear faltantes, borrar dirs obsoletos.
    foreach ($EXPECTED_DIRS as $dir) {
        $p = $example_dir . '/' . $dir;
        if (!is_dir($p)) {
            mkdir($p, 0755, true);
            file_put_contents($p . '/.gitkeep', '');
            echo "[FIX] creado dir: {$dir}/\n";
        }
    }
    foreach ($DROPPED_DIRS as $dir) {
        $p = $example_dir . '/' . $dir;
        if (is_dir($p)) {
            $items = array_merge(glob($p . '/*') ?: [], glob($p . '/.[!.]*') ?: []);
            foreach ($items as $f) {
                is_dir($f) ? rrmdir($f) : @unlink($f);
            }
            @rmdir($p);
            echo "[FIX] eliminado dir obsoleto: {$dir}/\n";
        }
    }
}

// ──────── Estructura: verificación (solo site/example) ────────
if ($is_example) {
    echo "── estructura de carpetas (site/example) ──\n";
    foreach ($EXPECTED_DIRS as $dir) {
        if (!is_dir($example_dir . '/' . $dir)) {
            echo "  [FAIL] Falta dir: {$dir}/ (corre con --fix)\n";
            $total_errors++;
        } else {
            echo "  [OK]   {$dir}/\n";
        }
    }
    foreach ($DROPPED_DIRS as $dir) {
        if (is_dir($example_dir . '/' . $dir)) {
            echo "  [FAIL] Dir obsoleto presente: {$dir}/ (se elimina con --fix)\n";
            $total_errors++;
        }
    }
}

if ($total_errors > 0) {
    echo "\nDesincronizado. Corre: php divi-agentic-core/bin/check-example.php --fix  (para example)\n";
    exit(1);
}

echo "\n[OK] Sites validados están sincronizados con el registry.\n";
exit(0);

/**
 * Borra recursivamente un directorio (incluye archivos ocultos).
 */
function rrmdir(string $dir): void {
    foreach (glob($dir . '/*') ?: [] as $f) {
        is_dir($f) ? rrmdir($f) : @unlink($f);
    }
    foreach (glob($dir . '/.[!.]*') ?: [] as $f) {
        is_dir($f) ? rrmdir($f) : @unlink($f);
    }
    @rmdir($dir);
}