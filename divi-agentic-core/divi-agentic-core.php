<?php
/**
 * Plugin Name: Divi Agentic Core (DAW)
 * Description: Core engine for the Divi Agentic Workflow — Layout_Engine, Design_Resolver, Module_Metadata, and WP-CLI commands.
 * Version:     4.0.0
 * Author:      DAW Bundle (Local)
 * Requires PHP: 8.0
 */

if ( ! defined( 'ABSPATH' ) && ! defined( 'WP_CLI' ) ) {
    define( 'ABSPATH', true );
}

define( 'DIVI_AGENTIC_CORE_DIR', __DIR__ );
define( 'DIVI_AGENTIC_CORE_VERSION', '4.0.0' );

require_once __DIR__ . '/inc/loader.php';

if ( defined( 'WP_CLI' ) && WP_CLI ) {
	add_action( 'cli_init', function () {
		\DAC\CLI\Agentic_Command::register();
	} );
}

/**
 * Resolve project root by walking up from plugin dir looking for .env
 */
function daw_find_project_root(): ?string {
    $dir = __DIR__;
    for ($i = 0; $i < 10; $i++) {
        if (file_exists($dir . '/.env')) {
            return $dir;
        }
        $parent = dirname($dir);
        if ($parent === $dir) break;
        $dir = $parent;
    }
    return null;
}

/**
 * Get DAW_SITE from environment or .env
 */
function daw_get_active_site(): ?string {
    $site = getenv('DAW_SITE');
    if ($site) return $site;

    $root = daw_find_project_root();
    if (!$root) return null;

    $env_file = $root . '/.env';
    if (!file_exists($env_file)) return null;

    $lines = file($env_file, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    foreach ($lines as $line) {
        $line = trim($line);
        if (str_starts_with($line, 'DAW_SITE=')) {
            $val = trim(substr($line, 9));
            if ((str_starts_with($val, '"') && str_ends_with($val, '"')) ||
                (str_starts_with($val, "'") && str_ends_with($val, "'"))) {
                $val = substr($val, 1, -1);
            }
            return $val;
        }
    }
    return null;
}

/**
 * Get the design system path for the active brand
 */
function daw_get_design_system_path(): ?string {
    $root = daw_find_project_root();
    $site = daw_get_active_site();
    if (!$root || !$site) return null;

    $path = $root . '/DAW_bundle/site/' . $site . '/design-system/divitheme.json';
    return file_exists($path) ? $path : null;
}

/**
 * Generate CSS custom properties from design system tokens
 */
function daw_generate_css_vars(?string $ds_path = null): string {
    if ($ds_path === null) {
        $ds_path = daw_get_design_system_path();
    }
    if (!$ds_path) return '';

    $json = file_get_contents($ds_path);
    $design = json_decode($json, true);
    if (!$design || !isset($design['tokens'])) return '';

    $tokens = $design['tokens'];
    $css = ':root {' . "\n";

    $colors = $tokens['color'] ?? [];
    foreach ($colors as $name => $value) {
        $var_name = '--daw-' . str_replace('_', '-', $name);
        $css .= "  {$var_name}: {$value};\n";
    }

    $surface_deep = $colors['surface-deep'] ?? 'rgba(0,0,0,0.08)';
    $accent = $colors['accent'] ?? '#D4956A';
    $css .= "  --daw-shadow-card: 0 12px 40px {$surface_deep};\n";
    $css .= "  --daw-glow-accent: 0 8px 32px {$accent}22;\n";

    $fonts = $tokens['font'] ?? [];
    foreach ($fonts as $name => $value) {
        $var_name = '--daw-font-' . $name;
        $css .= "  {$var_name}: {$value};\n";
    }

    $radii = $tokens['radius'] ?? [];
    foreach ($radii as $name => $value) {
        $var_name = '--daw-radius-' . $name;
        $css .= "  {$var_name}: {$value};\n";
    }

    $spaces = $tokens['space'] ?? [];
    foreach ($spaces as $name => $value) {
        $var_name = '--daw-space-' . $name;
        $css .= "  {$var_name}: {$value};\n";
    }

    $surface_white = $colors['surface-white'] ?? '#FFFFFF';
    $text_on_dark  = $colors['text-on-dark']  ?? '#F5F5F7';

    $css .= "  --daw-accent: {$accent};\n";
    $css .= "  --daw-surface-deep: {$surface_deep};\n";
    $css .= "  --daw-surface-white: {$surface_white};\n";
    $css .= "  --daw-glass-bg: {$surface_white}e0;\n";
    $css .= "  --daw-glass-border: {$accent}1f;\n";
    $css .= "  --daw-glass-border-strong: {$accent}40;\n";
    $css .= "  --daw-text-on-dark: {$text_on_dark};\n";

    $css .= '}';
    return $css;
}

/**
 * Sync brand CSS + design tokens to WordPress Custom CSS.
 *
 * Run this after deploying pages so brand styles live in the database
 * (wp_custom_css post type), not in the filesystem.
 *
 *   wp agentic sync-css
 */
if ( function_exists( 'add_action' ) ) {
	add_action( 'wp_enqueue_scripts', function () {
		$vars = daw_generate_css_vars();
		if ( $vars ) {
			wp_register_style( 'daw-design-tokens', false, [], DIVI_AGENTIC_CORE_VERSION );
			wp_enqueue_style( 'daw-design-tokens' );
			wp_add_inline_style( 'daw-design-tokens', $vars );
		}
	} );
}
