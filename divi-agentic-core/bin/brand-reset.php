<?php
/**
 * brand-reset.php — LEGACY wrapper
 *
 * Este script es un wrapper delgado que delega a Brand_Reset_Handler.
 * Usar: wp brand reset <slug>
 *
 * Mantenido por compatibilidad con flujos legacy.
 */

namespace DAC\Bin;

if (!defined('ABSPATH') && !defined('WP_CLI')) {
    exit;
}

$site = null;

global $argv;
$found_script = false;
foreach ($argv as $i => $arg) {
    if (!$found_script && str_ends_with($arg, '.php')) {
        $found_script = true;
        continue;
    }
    if ($found_script && !str_starts_with($arg, '--')) {
        $site = $arg;
        break;
    }
}

if (!$site) {
    $site = getenv('DAW_SITE');
}

if (class_exists('\DAC\Core\Brand_Reset_Handler')) {
    \DAC\Core\Brand_Reset_Handler::run($site);
} else {
    fwrite(STDERR, "ERROR: Brand_Reset_Handler not loaded.\n");
    exit(1);
}
