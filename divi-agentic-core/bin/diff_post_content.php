<?php
/**
 * diff_post_content.php — Compare post_content before and after rendering changes.
 *
 * Usage:
 *   # 1. Capture baseline from current Layout_Engine for a given page-def:
 *   php diff_post_content.php --def=home.json --baseline=baseline-home.txt
 *
 *   # 2. After modifying code, compare new output to the baseline:
 *   php diff_post_content.php --def=home.json --compare=baseline-home.txt
 *
 *   # 3. Direct A/B using two schema files:
 *   php diff_post_content.php --def-a=home-a.json --def-b=home-b.json
 *
 * Exit codes:
 *   0 = no diff or baseline saved.
 *   1 = structural diff detected.
 *   2 = error (missing file, invalid JSON, etc.).
 *
 * @package Divi_Agentic_Core
 */

require_once __DIR__ . DIRECTORY_SEPARATOR . 'env_loader.php';

$opts = getopt(
	'',
	[
		'def::',
		'baseline::',
		'compare::',
		'def-a::',
		'def-b::',
		'output::',
		'help',
	]
);

if ( isset( $opts['help'] ) ) {
	echo "Usage: php diff_post_content.php [options]\n\n";
	echo "Options:\n";
	echo "  --def=<file>          Page definition JSON (inside site/DAW_SITE/page-defs/)\n";
	echo "  --baseline=<file>    Save current rendered post_content to file\n";
	echo "  --compare=<file>     Compare current render against saved baseline\n";
	echo "  --def-a=<file>        Schema A for direct A/B comparison\n";
	echo "  --def-b=<file>        Schema B for direct A/B comparison\n";
	echo "  --output=<file>       Write diff report (default: STDOUT)\n";
	echo "\nExamples:\n";
	echo "  php diff_post_content.php --def=home.json --baseline=home-baseline.txt\n";
	echo "  php diff_post_content.php --def=home.json --compare=home-baseline.txt\n";
	exit( 0 );
}

// ── Load layout engine ──────────────────────────────────────────────
$engine_path = dirname( __DIR__ ) . DIRECTORY_SEPARATOR . 'inc' . DIRECTORY_SEPARATOR . 'core' . DIRECTORY_SEPARATOR . 'class-layout-engine.php';
if ( ! file_exists( $engine_path ) ) {
	fwrite( STDERR, "[ERROR] Layout engine not found: {$engine_path}\n" );
	exit( 2 );
}

// Load metadata traits required by the engine.
$metadata_trait = dirname( __DIR__ ) . DIRECTORY_SEPARATOR . 'inc' . DIRECTORY_SEPARATOR . 'core' . DIRECTORY_SEPARATOR . 'trait-module-metadata.php';
if ( file_exists( $metadata_trait ) ) {
	require_once $metadata_trait;
}
$metadata_attrs_trait = dirname( __DIR__ ) . DIRECTORY_SEPARATOR . 'inc' . DIRECTORY_SEPARATOR . 'core' . DIRECTORY_SEPARATOR . 'trait-module-metadata-attributes.php';
if ( file_exists( $metadata_attrs_trait ) ) {
	require_once $metadata_attrs_trait;
}

// The engine calls WordPress functions like get_site_url() / get_bloginfo().
// When running outside WP-CLI, load wp-load.php from the linked WordPress install.
if ( ! function_exists( 'get_site_url' ) ) {
	$wp_load = dirname( __DIR__, 3 ) . DIRECTORY_SEPARATOR . 'app' . DIRECTORY_SEPARATOR . 'public' . DIRECTORY_SEPARATOR . 'wp-load.php';
	if ( file_exists( $wp_load ) ) {
		require_once $wp_load;
	}
}

// Load renderers required by the engine.
$renderers = [
	'interface-block-renderer.php',
	'trait-block-helpers.php',
	'class-divi-base-renderer.php',
	'class-divi-structural-renderer.php',
	'class-dgpc-renderer.php',
];
$renderers_dir = dirname( __DIR__ ) . DIRECTORY_SEPARATOR . 'inc' . DIRECTORY_SEPARATOR . 'core' . DIRECTORY_SEPARATOR . 'renderers' . DIRECTORY_SEPARATOR;
foreach ( $renderers as $renderer ) {
	$path = $renderers_dir . $renderer;
	if ( file_exists( $path ) ) {
		require_once $path;
	}
}

require_once $engine_path;

// ── Resolve definition path ─────────────────────────────────────────
function resolve_def_path( string $def ): string {
	if ( file_exists( $def ) ) {
		return $def;
	}

	$site = getenv( 'DAW_SITE' );
	$root = dirname( __DIR__, 2 );
	$alt  = $root . DIRECTORY_SEPARATOR . 'site' . DIRECTORY_SEPARATOR . $site . DIRECTORY_SEPARATOR . 'page-defs' . DIRECTORY_SEPARATOR . $def;
	if ( file_exists( $alt ) ) {
		return $alt;
	}

	fwrite( STDERR, "[ERROR] Page definition not found: {$def}\n" );
	exit( 2 );
}

function render_blocks( string $def_file ): string {
	$raw = file_get_contents( $def_file );
	if ( $raw === false ) {
		fwrite( STDERR, "[ERROR] Cannot read: {$def_file}\n" );
		exit( 2 );
	}

	$engine = new \DAC\Core\Layout_Engine();
	$blocks = $engine->compile( $raw );

	if ( $blocks === '' ) {
		fwrite( STDERR, "[WARN] Engine returned empty output for: {$def_file}\n" );
	}

	return $blocks;
}

// ── Block-level normalization for stable comparison ───────────────────
function normalize_block_attrs( string $block_json ): string {
	$attrs = json_decode( $block_json, true );
	if ( ! is_array( $attrs ) ) {
		return $block_json;
	}

	// Remove volatile/irrelevant keys that change between runs but do not
	// affect visual output.
	$remove = [ 'globalModuleId' ];
	foreach ( $remove as $key ) {
		unset( $attrs[ $key ] );
	}

	if ( isset( $attrs['module'] ) && $attrs['module'] === (object) [] ) {
		$attrs['module'] = new \stdClass();
	}

	return wp_json_encode( $attrs, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES );
}

function normalize_content( string $content ): string {
	// Split into individual block comments, normalize each block's attrs, and
	// rejoin deterministically.
	if ( ! preg_match_all( '/<!-- wp:([^\s]+)\s+({.*?})\s*-->/', $content, $matches, PREG_SET_ORDER ) ) {
		return $content;
	}

	foreach ( $matches as $match ) {
		$slug   = $match[1];
		$attrs  = $match[2];
		$normalized = normalize_block_attrs( $attrs );
		if ( $normalized !== $attrs ) {
			$content = str_replace( $match[0], "<!-- wp:{$slug} {$normalized} -->", $content );
		}
	}

	return $content;
}

// ── Diff helpers ────────────────────────────────────────────────────
function compute_diff( string $a, string $b ): array {
	$lines_a = explode( "\n", $a );
	$lines_b = explode( "\n", $b );

	$diff = [];
	$max  = max( count( $lines_a ), count( $lines_b ) );

	for ( $i = 0; $i < $max; $i++ ) {
		$line_a = $lines_a[ $i ] ?? '';
		$line_b = $lines_b[ $i ] ?? '';

		if ( $line_a !== $line_b ) {
			$diff[] = [
				'line' => $i + 1,
				'a'    => $line_a,
				'b'    => $line_b,
			];
		}
	}

	return $diff;
}

function write_report( array $diff, string $output, string $label_a = 'baseline', string $label_b = 'current' ): int {
	$report = "[DIFF] {$label_a} -> {$label_b}\n";
	$report .= "Total differing lines: " . count( $diff ) . "\n";
	$report .= str_repeat( '-', 60 ) . "\n";

	$limit = 50;
	$shown = 0;
	foreach ( $diff as $d ) {
		if ( $shown >= $limit ) {
			$report .= "\n... (truncated after {$limit} lines; full diff: {$output})\n";
			break;
		}
		$report .= "Line {$d['line']}:\n";
		$report .= "  -> {$d['a']}\n";
		$report .= "  +> {$d['b']}\n";
		$shown++;
	}

	if ( $output === '' || $output === '-' ) {
		echo $report;
	} else {
		file_put_contents( $output, $report );
		echo "[OK] Diff report written to: {$output}\n";
	}

	return count( $diff ) === 0 ? 0 : 1;
}

// ── Main ────────────────────────────────────────────────────────────
$def_file   = $opts['def'] ?? null;
$baseline   = $opts['baseline'] ?? null;
$compare    = $opts['compare'] ?? null;
$def_a      = $opts['def-a'] ?? null;
$def_b      = $opts['def-b'] ?? null;
$output     = $opts['output'] ?? '';

if ( $def_a && $def_b ) {
	$path_a = resolve_def_path( $def_a );
	$path_b = resolve_def_path( $def_b );
	$content_a = normalize_content( render_blocks( $path_a ) );
	$content_b = normalize_content( render_blocks( $path_b ) );

	$diff = compute_diff( $content_a, $content_b );
	exit( write_report( $diff, $output, $def_a, $def_b ) );
}

if ( ! $def_file ) {
	fwrite( STDERR, "[ERROR] Missing --def, --baseline/--compare, or --def-a/--def-b.\n" );
	fwrite( STDERR, "  Run with --help for usage.\n" );
	exit( 2 );
}

$path = resolve_def_path( $def_file );
$current = normalize_content( render_blocks( $path ) );

if ( $baseline ) {
	file_put_contents( $baseline, $current );
	echo "[OK] Baseline saved to: {$baseline}\n";
	exit( 0 );
}

if ( $compare ) {
	if ( ! file_exists( $compare ) ) {
		fwrite( STDERR, "[ERROR] Baseline not found: {$compare}\n" );
		exit( 2 );
	}
	$previous = file_get_contents( $compare );
	$diff     = compute_diff( $previous, $current );
	exit( write_report( $diff, $output, $compare, 'current' ) );
}

fwrite( STDERR, "[ERROR] Specify --baseline to save or --compare to diff.\n" );
exit( 2 );
