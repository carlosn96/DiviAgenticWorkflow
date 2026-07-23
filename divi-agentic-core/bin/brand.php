<?php
/**
 * brand.php — LEGACY. Usar wp brand init|sync|reset|status
 *
 * Este script funciona via wp eval-file pero está obsoleto.
 * El plugin registra el comando WP-CLI nativo: wp brand <comando> [<slug>]
 *
 * Se mantiene por compatibilidad con flujos antiguos.
 * NO es necesario para nuevos proyectos.
 *
 * Uso legacy: wp eval-file bin/brand.php <comando> [<slug>]
 * Uso actual: wp brand <comando> [<slug>]
 */
namespace DAC\Bin;

require_once __DIR__ . '/env_loader.php';

use WP_CLI;
use DAC\Core\Token_Registry;

defined('ABSPATH') || exit;

function get_subcommand_and_site(): array {
    global $argv;
    $found_script = false;
    $args = [];
    foreach ($argv as $i => $arg) {
        if (!$found_script && str_ends_with($arg, '.php')) {
            $found_script = true;
            continue;
        }
        if ($found_script && !str_starts_with($arg, '--')) {
            $args[] = $arg;
        }
    }
    $cmd = $args[0] ?? 'status';
    $site = $args[1] ?? null;
    return [$cmd, $site];
}

// ─── Init ────────────────────────────────────────────────────────────────

function cmd_init(?string $site): void {
    $site = $site ?? getenv('DAW_SITE');
    if (!$site) WP_CLI::error('Especifica <slug> o define DAW_SITE en .env');

    $bundle_dir = defined('DIVI_AGENTIC_BUNDLE_NAME')
        ? dirname(__DIR__, 2)
        : dirname(__DIR__, 3);
    $out = $bundle_dir . '/site/' . $site . '/brand/_design_vars.json';

    if (file_exists($out)) {
        WP_CLI::warning("Ya existe: {$out}");
        WP_CLI::log('NO se sobreescribió. Edita el archivo existente.');
        WP_CLI::log('Si quieres regenerarlo desde cero, bórralo primero.');
        return;
    }

    $dir = dirname($out);
    if (!is_dir($dir)) {
        mkdir($dir, 0755, true);
        WP_CLI::log("Creado directorio: {$dir}");
    }

    $scaffold = Token_Registry::generate_scaffold();
    file_put_contents($out, json_encode($scaffold, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES));
    WP_CLI::success("Creado: {$out}");
    WP_CLI::log('Antes de sincronizar, cárgate un skill de dirección visual');
    WP_CLI::log('(hallmark, impeccable, high-end-visual-design) y edita los valores');
    WP_CLI::log('con criterio de diseño real.');
}

// ─── Sync ────────────────────────────────────────────────────────────────

function cmd_sync(?string $site): void {
    $site = $site ?? getenv('DAW_SITE');
    if (!$site) WP_CLI::error('Especifica <slug> o define DAW_SITE en .env');

    $bundle_dir = defined('DIVI_AGENTIC_BUNDLE_NAME')
        ? dirname(__DIR__, 2)
        : dirname(__DIR__, 3);
    $vars_path = $bundle_dir . '/site/' . $site . '/brand/_design_vars.json';

    if (!file_exists($vars_path)) {
        WP_CLI::error("No existe _design_vars.json para '{$site}'.");
        WP_CLI::log('Ejecuta primero: wp eval-file bin/brand.php init ' . $site);
        return;
    }

    \DAC\Core\Brand_Sync_Handler::run($site);
}

// ─── Reset ───────────────────────────────────────────────────────────────

function cmd_reset(?string $site): void {
    $site = $site ?? getenv('DAW_SITE');
    if (!$site) WP_CLI::error('Especifica <slug> o define DAW_SITE en .env');

    \DAC\Core\Brand_Reset_Handler::run($site);
}

// ─── Status ──────────────────────────────────────────────────────────────

function cmd_status(?string $site): void {
    $site = $site ?? getenv('DAW_SITE');
    if (!$site) WP_CLI::error('Especifica <slug> o define DAW_SITE en .env');

    $bundle_dir = defined('DIVI_AGENTIC_BUNDLE_NAME')
        ? dirname(__DIR__, 2)
        : dirname(__DIR__, 3);
    $vars_path = $bundle_dir . '/site/' . $site . '/brand/_design_vars.json';
    $design_system = $bundle_dir . '/site/' . $site . '/design-system/divitheme.json';

    WP_CLI::log(str_repeat('─', 50));
    WP_CLI::log("Brand: {$site}");
    WP_CLI::log(str_repeat('─', 50));

    WP_CLI::log('');
    WP_CLI::log('Archivos:');
    WP_CLI::log('  _design_vars.json: ' . (file_exists($vars_path) ? 'EXISTE' : 'NO EXISTE'));
    WP_CLI::log('  divitheme.json:    ' . (file_exists($design_system) ? 'EXISTE' : 'NO EXISTE'));

    WP_CLI::log('');
    WP_CLI::log('WordPress:');
    $divi = get_option('et_divi', []);
    $gd = get_option('et_global_data', null);
    $hash = get_option('_dac_gcid_hash', null);
    WP_CLI::log('  et_divi:       ' . count($divi) . ' keys');
    WP_CLI::log('  et_global_data: ' . ($gd ? 'PRESENTE' : 'AUSENTE'));
    WP_CLI::log('  _dac_gcid_hash: ' . ($hash ? 'PRESENTE' : 'AUSENTE'));

    if (file_exists($vars_path)) {
        $vars = json_decode(file_get_contents($vars_path), true);
        if ($vars) {
            $missing = [];
            $tokens = Token_Registry::get_all();
            foreach ($tokens as $key => $def) {
                if (!empty($def['required']) && (!array_key_exists($key, $vars) || $vars[$key] === null)) {
                    $missing[] = $key;
                }
            }
            if ($missing) {
                WP_CLI::log('');
                WP_CLI::warning(count($missing) . ' tokens required sin valor:');
                foreach ($missing as $k) WP_CLI::log("  - {$k}");
            }
        }
    }

    $accent = function_exists('et_get_option') ? et_get_option('accent_color', 'NO') : 'N/A';
    WP_CLI::log('');
    WP_CLI::log("et_get_option('accent_color'): {$accent}");
}

// ─── Main ────────────────────────────────────────────────────────────────

[$cmd, $site] = get_subcommand_and_site();

if ($site) {
    putenv("DAW_SITE={$site}");
}

switch ($cmd) {
    case 'init':
        cmd_init($site);
        break;
    case 'sync':
        cmd_sync($site);
        break;
    case 'reset':
        cmd_reset($site);
        break;
    case 'status':
        cmd_status($site);
        break;
    default:
        WP_CLI::error("Comando desconocido: {$cmd}");
        WP_CLI::log('Usa: wp eval-file bin/brand.php {init|sync|reset|status} [<slug>]');
}
