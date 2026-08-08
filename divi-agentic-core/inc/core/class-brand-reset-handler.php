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
        WP_CLI::log('3. Restaurando divitheme.json...');
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
        WP_CLI::log('4. Limpiando caché de CSS Divi...');
        $upload_dir = wp_get_upload_dir();
        $et_cache = $upload_dir['basedir'] . '/et-cache';
        $count = 0;
        if (is_dir($et_cache)) {
            $iterator = new \RecursiveIteratorIterator(
                new \RecursiveDirectoryIterator($et_cache, \RecursiveDirectoryIterator::SKIP_DOTS),
                \RecursiveIteratorIterator::CHILD_FIRST
            );
            foreach ($iterator as $f) {
                if ($f->isFile()) { unlink($f->getRealPath()); $count++; }
            }
            WP_CLI::log("   et-cache: {$count} archivos eliminados");
        } else {
            WP_CLI::log('   et-cache: no existe');
        }

        delete_option('et_core_page_resource_auto_clear');
        update_option('et_core_page_resource_auto_clear', time());
        if (function_exists('et_core_clear_wp_cache')) {
            et_core_clear_wp_cache();
        }
        WP_CLI::success('Cachés de CSS limpiadas y marcadas para regeneración.');

        WP_CLI::log('');
        WP_CLI::log(str_repeat('─', 50));
        WP_CLI::success('Brand reset completado.');
    }
}
