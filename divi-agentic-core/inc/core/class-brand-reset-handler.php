<?php

namespace DAC\Core;

use WP_CLI;

class Brand_Reset_Handler {

    public static function run(?string $site = null): void {
        WP_CLI::log(str_repeat('─', 50));
        WP_CLI::log('Brand Reset');
        WP_CLI::log(str_repeat('─', 50));

        WP_CLI::log('');
        WP_CLI::log('1. Eliminando et_divi...');
        delete_option('et_divi');
        wp_cache_delete('et_divi', 'options');
        WP_CLI::success('et_divi eliminado.');

        WP_CLI::log('');
        WP_CLI::log('2. Eliminando gcids + gvids...');
        delete_option('et_global_data');
        delete_option('_dac_gcid_hash');
        WP_CLI::success('gcids, gvids y hash de sync eliminados.');

        WP_CLI::log('');
        WP_CLI::log('3. Opciones residuales _et_builder_* / et_divi_builder_*...');
        global $wpdb;
        $residual = $wpdb->get_col("
            SELECT option_name FROM {$wpdb->options}
            WHERE option_name LIKE '_et\\_builder\\_%'
               OR option_name LIKE 'et_divi\\_builder\\_%'
        ");
        foreach ($residual as $name) {
            delete_option($name);
            WP_CLI::log("   eliminada: {$name}");
        }
        WP_CLI::success(count($residual) . ' opciones residuales eliminadas.');

        WP_CLI::log('');
        WP_CLI::log('4. Restaurando divitheme.json...');
        if ($site) {
            $divitheme_path = dirname(DIVI_AGENTIC_CORE_DIR) . '/site/' . $site . '/design-system/divitheme.json';
            if (file_exists($divitheme_path)) {
                file_put_contents($divitheme_path, json_encode([
                    'presets'   => [],
                    'strategy'  => 'custom',
                    '_note'     => 'Restaurado por brand reset.',
                ], JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES));
                WP_CLI::success("divitheme.json vaciado: {$divitheme_path}");
            } else {
                WP_CLI::warning("no encontrado: {$divitheme_path}");
            }
        }

        WP_CLI::log('');
        WP_CLI::log('5. Limpiando cachés...');
        $upload_dir = wp_get_upload_dir();
        $et_cache = $upload_dir['basedir'] . '/et-cache';
        if (is_dir($et_cache)) {
            $count = 0;
            $iterator = new \RecursiveIteratorIterator(
                new \RecursiveDirectoryIterator($et_cache, \RecursiveDirectoryIterator::SKIP_DOTS),
                \RecursiveIteratorIterator::CHILD_FIRST
            );
            foreach ($iterator as $f) {
                if ($f->isFile()) { unlink($f->getRealPath()); $count++; }
                if ($f->isDir())  { rmdir($f->getRealPath()); }
            }
            WP_CLI::log("   et-cache: {$count} archivos eliminados");
        } else {
            WP_CLI::log('   et-cache: no existe');
        }

        delete_option('et_core_page_resource_auto_clear');
        wp_cache_flush();
        if (function_exists('et_core_clear_wp_cache')) {
            et_core_clear_wp_cache();
        }
        WP_CLI::success('Cachés limpiadas.');

        WP_CLI::log('');
        WP_CLI::log(str_repeat('─', 50));
        WP_CLI::success('Brand reset completado.');
    }
}
