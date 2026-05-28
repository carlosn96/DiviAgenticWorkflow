<?php
/**
 * verify_page.php — Post-deploy verification for Divi 5 pages
 * ===========================================================
 * Checks that a deployed page is structurally sound and GCIDs render correctly.
 *
 * Usage:
 *   php verify_page.php --slug=mi-pagina
 *   php verify_page.php --slug=mi-pagina --url="https://example.com/mi-pagina"
 *   php verify_page.php --slug=mi-pagina --schema=page-defs/mi-pagina.json
 *
 * Exit codes:
 *   0 — All checks passed
 *   1 — One or more checks failed
 */

$DIR_SEP = DIRECTORY_SEPARATOR;
define('DAW_ROOT', str_replace('/', $DIR_SEP, dirname(__DIR__, 2)));
define('SITE', getenv('DAW_SITE') ?: 'bibliotheca');
define('SITE_DIR', DAW_ROOT . $DIR_SEP . 'site' . $DIR_SEP . SITE);
define('WP_BAT', DAW_ROOT . $DIR_SEP . 'wp.bat');

$opts = getopt('', ['slug::', 'url::', 'schema::', 'help']);

if (isset($opts['help']) || empty($opts['slug'])) {
    echo "Usage: php verify_page.php --slug=<page-slug> [options]\n";
    echo "\n";
    echo "  --slug=<slug>   Page slug to verify (required)\n";
    echo "  --url=<url>     Public URL for full visual check (optional)\n";
    echo "  --schema=<path> Path to page-defs JSON for structural comparison (optional)\n";
    echo "  --help          This message\n";
    exit(1);
}

$slug    = $opts['slug'];
$page_url = $opts['url'] ?? '';
$schema_path = $opts['schema'] ?? '';

$checks      = [];
$all_passed  = true;

function check(string $label, bool $pass, string $detail = ''): void {
    global $checks, $all_passed;
    $icon = $pass ? '[PASS]' : '[FAIL]';
    $checks[] = ['label' => $label, 'pass' => $pass, 'detail' => $detail];
    echo "  {$icon} {$label}" . ($detail ? ": {$detail}" : '') . "\n";
    if (!$pass) $all_passed = false;
}

echo "[VERIFY] Verifying page '{$slug}'...\n\n";

// ── Check 1: Page exists in WordPress ──────────────────────────────
$cmd = sprintf(
    '"%s" post list --post_type=page --name="%s" --field=ID --format=json',
    WP_BAT,
    $slug
);
$output = shell_exec($cmd);
$ids = json_decode($output ?? '[]', true);
$page_id = $ids[0] ?? null;

if (!$page_id) {
    check('Page exists in WordPress', false, "No page found with slug '{$slug}'");
    echo "\n[VERIFY] " . ($all_passed ? 'ALL PASSED' : 'SOME CHECKS FAILED') . "\n";
    exit($all_passed ? 0 : 1);
}
check('Page exists in WordPress', true, "ID: {$page_id}");

// ── Check 2: Page has content ─────────────────────────────────────
$cmd = sprintf(
    '"%s" post get %d --field=post_content --format=json',
    WP_BAT,
    $page_id
);
$content = shell_exec($cmd);
$content = trim($content ?? '');

if (empty($content)) {
    check('Page has content', false, 'post_content is empty');
} else {
    check('Page has content', true, strlen($content) . ' bytes');
}

// ── Check 3: Content contains Divi blocks ─────────────────────────
$has_divi_blocks = strpos($content, '<!-- wp:divi/') !== false;
check('Content contains Divi blocks', $has_divi_blocks,
    $has_divi_blocks ? 'Found divi/* blocks' : 'No divi/* blocks detected'
);

// ── Check 4: GCID variables present in content ────────────────────
$gcid_count = preg_match_all('/var\(--gcid-[\w-]+\)/', $content, $gcid_matches);
check('GCID variables applied', $gcid_count > 0,
    $gcid_count > 0 ? "Found {$gcid_count} gcid references" : 'No var(--gcid-*) found in content'
);

if ($gcid_count > 0) {
    $unique_gcids = array_unique($gcid_matches[0]);
    check('Unique GCIDs used', count($unique_gcids) > 0,
        count($unique_gcids) . ' unique: ' . implode(', ', array_slice($unique_gcids, 0, 5)) . (count($unique_gcids) > 5 ? '...' : '')
    );
}

// ── Check 5: No unresolved tokens ─────────────────────────────────
$unresolved = preg_match_all('/\{\{design:\w+:[\w-]+\}\}/', $content, $unresolved_matches);
check('No unresolved design tokens', $unresolved === 0,
    $unresolved > 0 ? "Found {$unresolved} unresolved tokens: " . implode(', ', array_unique($unresolved_matches[0])) : 'All tokens resolved'
);

// ── Check 6: Page is publicly accessible (if URL provided) ────────
if (!empty($page_url)) {
    $ctx = stream_context_create(['http' => ['timeout' => 10, 'method' => 'GET']]);
    $response = @file_get_contents($page_url, false, $ctx);
    $http_code = 0;
    if (isset($http_response_header[0])) {
        preg_match('/\s(\d+)\s/', $http_response_header[0], $code_match);
        $http_code = (int)($code_match[1] ?? 0);
    }
    $accessible = $http_code === 200;
    check('Page publicly accessible', $accessible,
        $accessible ? "HTTP {$http_code}" : "HTTP {$http_code} — page may not be published"
    );
    if ($accessible) {
        $body_gcid = preg_match_all('/var\(--gcid-[\w-]+\)/', $response, $body_matches);
        check('GCIDs render in HTML output', $body_gcid > 0,
            $body_gcid > 0 ? "Found {$body_gcid} gcid references in rendered HTML" : 'No gcid refs in rendered HTML (may be in JS-generated inline styles)'
        );
    }
}

// ── Check 7: Structural match vs schema (if provided) ────────────
if (!empty($schema_path)) {
    $def_path = strpos($schema_path, 'site/') === 0 || strpos($schema_path, '/') === false
        ? SITE_DIR . $DIR_SEP . 'page-defs' . $DIR_SEP . basename($schema_path)
        : $schema_path;
    if (file_exists($def_path)) {
        $def = json_decode(file_get_contents($def_path), true);
        $def_sections = count($def['sections'] ?? []);
        $actual_sections = preg_match_all('/<!-- wp:divi\/section\b/', $content);
        $section_match = $actual_sections >= $def_sections;
        check('Section count matches schema', $section_match,
            "Expected ~{$def_sections}, found {$actual_sections} in content"
        );
    } else {
        check('Schema file accessible', false, "Not found: {$def_path}");
    }
}

// ── Summary ────────────────────────────────────────────────────────
echo "\n[VERIFY] Results: " . count(array_filter($checks, fn($c) => $c['pass'])) . '/' . count($checks) . " passed\n";
if ($all_passed) {
    echo "[VERIFY] ALL CHECKS PASSED — page '{$slug}' is healthy.\n";
} else {
    $failures = array_filter($checks, fn($c) => !$c['pass']);
    echo "[VERIFY] FAILURES:\n";
    foreach ($failures as $f) {
        echo "  - {$f['label']}: {$f['detail']}\n";
    }
}

exit($all_passed ? 0 : 1);
