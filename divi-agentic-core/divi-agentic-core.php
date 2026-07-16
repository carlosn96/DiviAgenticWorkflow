<?php
/**
 * Plugin Name: Divi Agentic Core (DAW)
 * Description: Core engine for the Divi Agentic Workflow — Layout_Engine, Design_Resolver, Module_Metadata, and WP-CLI commands.
 * Version:     4.1.0
 * Author:      DAW Bundle (Local)
 * Requires PHP: 8.0
 */

if ( ! defined( 'ABSPATH' ) && ! defined( 'WP_CLI' ) ) {
    define( 'ABSPATH', true );
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
 * Get environment variable from environment, $_SERVER, $_ENV or .env file
 */
function daw_get_env_var(string $key, ?string $default = null): ?string {
    $val = getenv($key);
    if ($val !== false) return $val;

    if (isset($_ENV[$key])) return $_ENV[$key];
    if (isset($_SERVER[$key])) return $_SERVER[$key];

    $root = daw_find_project_root();
    if (!$root) return $default;

    $env_file = $root . '/.env';
    if (!file_exists($env_file)) return $default;

    $lines = file($env_file, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    $prefix = $key . '=';
    foreach ($lines as $line) {
        $line = trim($line);
        if (str_starts_with($line, $prefix)) {
            $val = trim(substr($line, strlen($prefix)));
            if ((str_starts_with($val, '"') && str_ends_with($val, '"')) ||
                (str_starts_with($val, "'") && str_ends_with($val, "'"))) {
                $val = substr($val, 1, -1);
            }
            return $val;
        }
    }
    return $default;
}

/**
 * Get DAW_SITE from environment or .env
 */
function daw_get_active_site(): ?string {
    return daw_get_env_var('DAW_SITE');
}

/**
 * Get the DAW bundle directory name (e.g. 'DAW_bundle' or 'DiviAgenticWorkflow')
 */
function daw_get_bundle_name(): string {
    $bundle = daw_get_env_var('DAW_BUNDLE_NAME');
    if ($bundle) return $bundle;

    $dir = realpath(__DIR__);
    if ($dir) {
        $parent = dirname($dir);
        $name = basename($parent);
        if ($name && $name !== 'plugins' && $name !== 'wp-content') {
            return $name;
        }
    }

    return 'DAW_bundle';
}

define( 'DIVI_AGENTIC_CORE_DIR', __DIR__ );
define( 'DIVI_AGENTIC_CORE_VERSION', '4.1.1' );
define( 'DIVI_AGENTIC_BUNDLE_NAME', daw_get_bundle_name() );

require_once __DIR__ . '/inc/loader.php';

if ( defined( 'WP_CLI' ) && WP_CLI ) {
	add_action( 'cli_init', function () {
		\DAC\CLI\Agentic_Command::register();
	} );
}

/**
 * Get the design system path for the active brand
 */
function daw_get_design_system_path(): ?string {
    $root = daw_find_project_root();
    $site = daw_get_active_site();
    if (!$root || !$site) return null;

    $path = $root . '/' . DIVI_AGENTIC_BUNDLE_NAME . '/site/' . $site . '/design-system/divitheme.json';
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
 * All module asset enqueuing and block registration delegated to Module_Registry.
 * Add a folder to modules/ with module.json or manifest.json — no core edits needed.
 */
/**
 * Newsletter subscription AJAX handler
 */
add_action( 'wp_ajax_daw_newsletter_subscribe', 'daw_newsletter_subscribe_handler' );
add_action( 'wp_ajax_nopriv_daw_newsletter_subscribe', 'daw_newsletter_subscribe_handler' );
function daw_newsletter_subscribe_handler() {
	$email = isset( $_POST['email'] ) ? sanitize_email( $_POST['email'] ) : '';
	if ( ! is_email( $email ) ) {
		wp_send_json_error( [ 'message' => 'Correo electrónico inválido.' ] );
	}

	$to      = get_option( 'admin_email' );
	$subject = 'Nueva suscripción al boletín - López Velarde';
	$message = "Nueva suscripción al boletín:\n\nCorreo: $email";
	wp_mail( $to, $subject, $message );

	setcookie( 'daw_newsletter_subscribed', '1', time() + YEAR_IN_SECONDS, COOKIEPATH, COOKIE_DOMAIN, is_ssl() );
	wp_send_json_success( [ 'message' => '¡Gracias por suscribirte!' ] );
}

/**
 * Localize AJAX URL for newsletter form
 */
add_action( 'wp_enqueue_scripts', function () {
	wp_register_script( 'daw-newsletter', false, [], DIVI_AGENTIC_CORE_VERSION, true );
	wp_localize_script( 'daw-newsletter', 'dawAjax', [
		'ajaxUrl' => admin_url( 'admin-ajax.php' ),
		'nonce'   => wp_create_nonce( 'daw_newsletter_nonce' ),
	] );
	wp_enqueue_script( 'daw-newsletter' );
}, 100 );

if ( function_exists( 'add_action' ) ) {
	add_action( 'wp_enqueue_scripts', function () {
		$deps = [];

		// Load brand fonts from design system dynamically
		$ds_path = daw_get_design_system_path();
		if ( $ds_path ) {
			$ds = json_decode( file_get_contents( $ds_path ), true );
			if ( $ds && isset( $ds['tokens']['font'] ) ) {
				$google_font_map = [
					'Cinzel'         => 'Cinzel:wght@400;500;600;700',
					'Jost'           => 'Jost:wght@300;400;500;600;700',
					'Fredoka'        => 'Fredoka:wght@400;500;600;700',
					'Nunito'         => 'Nunito:wght@300;400;500;600;700',
					'Inter'          => 'Inter:wght@300;400;500;600;700',
					'Space Grotesk'  => 'Space+Grotesk:wght@400;500;600;700',
					'Playfair Display' => 'Playfair+Display:wght@400;500;600;700',
					'DM Sans'        => 'DM+Sans:opsz,wght@9..40,100..1000',
					'Cormorant Garamond' => 'Cormorant+Garamond:wght@400;500;600;700',
					'Outfit'         => 'Outfit:wght@200;300;400;500;600;700;800;900',
					'Work Sans'      => 'Work+Sans:wght@300;400;500;600;700',
				];
				$seen = [];
				foreach ( $ds['tokens']['font'] as $key => $family_full ) {
					preg_match( "/'([^']+)'/", $family_full, $m );
					$base = $m[1] ?? '';
					if ( ! $base || isset( $seen[ $base ] ) ) continue;
					if ( isset( $google_font_map[ $base ] ) ) {
						$handle = 'daw-font-' . sanitize_title( $base );
						$url    = 'https://fonts.googleapis.com/css2?family=' . $google_font_map[ $base ] . '&display=swap';
						wp_enqueue_style( $handle, $url, [], null );
						$deps[] = $handle;
						$seen[ $base ] = true;
					}
				}
			}
		}



		$vars = daw_generate_css_vars();
		if ( $vars ) {
			wp_register_style( 'daw-design-tokens', false, $deps, DIVI_AGENTIC_CORE_VERSION );
			wp_enqueue_style( 'daw-design-tokens' );
			wp_add_inline_style( 'daw-design-tokens', $vars );
		}

		// Enqueue brand.css from disk (single source of truth — no DB duplication)
		$root = daw_find_project_root();
		$site = daw_get_active_site();
		if ( $root && $site ) {
			$brand_css_path = $root . '/' . DIVI_AGENTIC_BUNDLE_NAME . '/divi-agentic-core/assets/css/brand.css';
			// Check for brand-specific override
			$brand_site_path = $root . '/' . DIVI_AGENTIC_BUNDLE_NAME . '/site/' . $site . '/brand/assets/css/brand.css';
			if ( file_exists( $brand_site_path ) ) {
				$brand_css_path = $brand_site_path;
			}
			if ( file_exists( $brand_css_path ) ) {
				$brand_css_url = home_url( str_replace( $root, '', $brand_css_path ) );
				$brand_css_deps = [];
				if ( wp_style_is( 'daw-design-tokens', 'registered' ) ) {
					$brand_css_deps[] = 'daw-design-tokens';
				}
				wp_enqueue_style( 'daw-brand-css', $brand_css_url, $brand_css_deps, DIVI_AGENTIC_CORE_VERSION );
			}
		}
	} );

	\DAC\Core\Module_Registry::init();
}