<?php
/**
 * env_loader.php — Loads .env from project root into environment
 *
 * Reads DAW_bundle/../.env (project root) and sets variables
 * via putenv() so getenv() works in all PHP scripts.
 * Only sets if not already in environment (env vars take precedence).
 *
 * Include at the top of any DAW CLI script:
 *   require_once __DIR__ . '/env_loader.php';
 */

$env_path = dirname(__DIR__, 3) . DIRECTORY_SEPARATOR . '.env';

if (file_exists($env_path)) {
    $lines = file($env_path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    foreach ($lines as $line) {
        $line = trim($line);
        if ($line === '' || $line[0] === '#') continue;
        if (str_starts_with($line, 'export ')) {
            $line = trim(substr($line, 7));
        }
        $eq = strpos($line, '=');
        if ($eq === false) continue;
        $key = trim(substr($line, 0, $eq));
        $val = trim(substr($line, $eq + 1));
        // Strip surrounding quotes
        if ((str_starts_with($val, '"') && str_ends_with($val, '"')) ||
            (str_starts_with($val, "'") && str_ends_with($val, "'"))) {
            $val = substr($val, 1, -1);
        }
        // Only set if not already in environment
        if (getenv($key) === false || getenv($key) === '') {
            putenv("{$key}={$val}");
        }
    }
}
