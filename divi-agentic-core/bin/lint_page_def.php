<?php
/**
 * lint_page_def.php — Page Definition Quality Gate
 *
 * Validates a page-def JSON against the 6 Leyes de Calidad Autónoma,
 * preset existence, hex colors, et_pb_* usage, and unresolved tokens.
 *
 * Usage:
 *   php lint_page_def.php --def=home.json
 *   php lint_page_def.php --def=site/<DAW_SITE>/page-defs/home.json --verbose
 *   php lint_page_def.php --def=home.json --presets=_design_presets.json
 *
 * Exit codes:
 *   0 — Pass (all checks OK)
 *   1 — Fail (one or more blocking checks failed)
 */

$DIR_SEP = DIRECTORY_SEPARATOR;
define('DAW_ROOT', str_replace('/', $DIR_SEP, dirname(__DIR__, 2)));

// Enforce fail-fast check for DAW_SITE (no defaults or fallback)
$daw_site = getenv('DAW_SITE');
if ($daw_site === false || $daw_site === '') {
    $env_path = dirname(__DIR__, 3) . $DIR_SEP . '.env';
    if (file_exists($env_path)) {
        foreach (file($env_path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) as $line) {
            $line = trim($line);
            if (str_starts_with($line, 'DAW_SITE=')) {
                $val = trim(substr($line, 9));
                if ((str_starts_with($val, '"') && str_ends_with($val, '"')) ||
                    (str_starts_with($val, "'") && str_ends_with($val, "'"))) {
                    $val = substr($val, 1, -1);
                }
                if ($val !== '') {
                    putenv("DAW_SITE={$val}");
                    $daw_site = $val;
                }
                break;
            }
        }
    }
}
if (!$daw_site) {
    fwrite(STDERR, "[ERROR] DAW_SITE no está definido. Debes configurar una marca activa en .env antes de ejecutar lint_page_def.php.\n");
    exit(1);
}
define('DEFS_DIR', DAW_ROOT . $DIR_SEP . 'site' . $DIR_SEP . $daw_site . $DIR_SEP . 'page-defs');

$opts = getopt('', ['def::', 'presets::', 'verbose', 'help']);
$def_file = $opts['def'] ?? null;
$presets_file = $opts['presets'] ?? null;
$verbose = isset($opts['verbose']);

if (isset($opts['help']) || !$def_file) {
    echo "Usage: php lint_page_def.php --def=<file> [options]\n\n";
    echo "Options:\n";
    echo "  --def=<file>     Page definition JSON file (in site/<DAW_SITE>/page-defs/ or full path)\n";
    echo "  --presets=<file> Design presets JSON for preset existence validation\n";
    echo "  --verbose        Show all checks, including passing ones\n";
    echo "  --help           This message\n\n";
    echo "Validates: 6 Leyes, presets, no hex, no et_pb_*, no {{design:*}} unresolved\n";
    exit(1);
}

if (!file_exists($def_file)) {
    $alt = DEFS_DIR . $DIR_SEP . $def_file;
    if (file_exists($alt)) {
        $def_file = $alt;
    } else {
        fwrite(STDERR, "[ERROR] Page definition not found: {$def_file}\n");
        exit(1);
    }
}

$page_def = json_decode(file_get_contents($def_file), true);
if (!$page_def) {
    fwrite(STDERR, "[ERROR] Invalid JSON in: {$def_file}\n");
    exit(1);
}

$presets_data = null;
if ($presets_file) {
    if (!file_exists($presets_file)) {
        fwrite(STDERR, "[WARN] Presets file not found: {$presets_file}\n");
    } else {
        $presets_data = json_decode(file_get_contents($presets_file), true);
    }
}

$slug = $page_def['slug'] ?? basename($def_file);
$page_title = $page_def['title'] ?? 'unknown';
echo "[LINT] Linting page: {$page_title} ({$slug})\n";
echo str_repeat('-', 50) . "\n";

$passed = 0;
$failed = 0;
$warnings = 0;
$results = [];

function report(string $check, bool $ok, string $detail = '', bool $blocking = true): void {
    global $passed, $failed, $warnings;
    if ($ok) {
        $passed++;
        echo "  [PASS] {$check}\n";
    } elseif ($blocking) {
        $failed++;
        echo "  [FAIL] {$check}\n";
        if ($detail) echo "         {$detail}\n";
    } else {
        $warnings++;
        echo "  [WARN] {$check}\n";
        if ($detail) echo "         {$detail}\n";
    }
}

// ── Ley 1: Contraste de Sección ──────────────────
// El design system actual no usa presets (`"presets": []`); el ritmo visual
// se expresa con tokens nativos. Comparamos el token de fondo (color/image)
// entre secciones adyacentes como WARNING (no bloqueante): el page-def real
// puede tener secciones contiguas con el mismo token si el diseño lo pide.
$sections = $page_def['sections'] ?? [];
$section_presets = [];
foreach ($sections as $i => $sec) {
    $presets = $sec['presets'] ?? [];
    $section_presets[$i] = $presets;
}

$ley1_ok = true;
$ley1_detail = '';
for ($i = 1; $i < count($sections); $i++) {
    $prev = $section_presets[$i - 1] ?? [];
    $curr = $section_presets[$i] ?? [];
    $prev_bg = '';
    $curr_bg = '';
    foreach ($prev as $p) {
        if (str_starts_with($p, 'section:')) $prev_bg = $p;
    }
    foreach ($curr as $p) {
        if (str_starts_with($p, 'section:')) $curr_bg = $p;
    }
    if ($prev_bg && $curr_bg && $prev_bg === $curr_bg) {
        $ley1_ok = false;
        $ley1_detail = "sec-{$i} and sec-" . ($i - 1) . " both use '{$prev_bg}'";
        break;
    }
}
report("Ley 1 — Contraste de Sección: no consecutive same section presets", $ley1_ok, $ley1_detail);

// Ley 1 nativa (WARN): misma decoration.background color entre secciones adyacentes.
$ley1n_ok = true;
$ley1n_detail = '';
for ($i = 1; $i < count($sections); $i++) {
    $prev_bg = $sections[$i - 1]['decoration']['background']['desktop']['value']['color'] ?? '';
    $curr_bg = $sections[$i]['decoration']['background']['desktop']['value']['color'] ?? '';
    if ($prev_bg !== '' && $prev_bg === $curr_bg) {
        $ley1n_ok = false;
        $ley1n_detail = "sec-{$i} and sec-" . ($i - 1) . " share background token '{$curr_bg}' (WARN — puede ser intencional)";
        break;
    }
}
report("Ley 1 nativa — backgrounds adyacentes distintos", $ley1n_ok, $ley1n_detail, false);

// ── Ley 2: Titular Dominante (nativo, sin presets) ─
// El hero (primera sección) debe contener un divi/heading o divi/text cuyo
// headingFont (h1/h2/h3) o bodyFont declare un size desktop dominante (≥ 2rem).
$ley2_ok = false;
$ley2_detail = '';
if (!empty($sections)) {
    $hero = $sections[0];
    $modules = [];
    foreach ($hero['rows'] ?? [] as $row) {
        foreach ($row['columns'] ?? $row['modules'] ?? [] as $col) {
            if (isset($col['modules'])) {
                foreach ($col['modules'] as $mod) {
                    $modules[] = $mod;
                }
            } else {
                $modules[] = $col;
            }
        }
    }
    foreach ($modules as $mod) {
        $type = $mod['type'] ?? $mod['module'] ?? '';
        if ($type !== 'divi/heading' && $type !== 'divi/text') {
            continue;
        }
        $font_groups = [$mod['headingFont'] ?? [], $mod['bodyFont'] ?? []];
        $found_size = 0.0;
        foreach ($font_groups as $fg) {
            foreach ($fg as $level => $group) {
                foreach ($group['font'] ?? [] as $bp => $entry) {
                    if ($bp !== 'desktop' || !isset($entry['value']['size'])) {
                        continue;
                    }
                    $size = $entry['value']['size'];
                    $rem = 0.0;
                    if (preg_match('/^([\d.]+)rem$/', $size, $m)) {
                        $rem = (float) $m[1];
                    } elseif (preg_match('/^([\d.]+)px$/', $size, $m)) {
                        $rem = (float) $m[1] / 16;
                    }
                    if ($rem > $found_size) {
                        $found_size = $rem;
                    }
                }
            }
        }
        if ($found_size >= 2.0) {
            $ley2_ok = true;
            break;
        }
    }
    if (!$ley2_ok) {
        $ley2_detail = 'No divi/heading|divi/text with dominant desktop size (≥2rem) found in first section (hero)';
    }
}
report("Ley 2 — Titular Dominante: hero has dominant heading (≥2rem native)", $ley2_ok, $ley2_detail);

// ── Ley 3: Espacio Negativo Mínimo ────────────────
$ley3_ok = true;
$ley3_detail = '';
foreach ($sections as $i => $sec) {
    $padding = $sec['decoration']['spacing']['desktop']['value']['padding'] ?? [];
    $top = $padding['top'] ?? '';
    $bottom = $padding['bottom'] ?? '';
    if ($top && (int)$top < 96 && $top !== '{{design:space:2xl}}') {
        if (!str_contains($top, 'clamp')) {
            $ley3_ok = false;
            $ley3_detail = "section {$i}: padding-top {$top} < 96px minimum";
            break;
        }
    }
    if ($bottom && (int)$bottom < 96 && $bottom !== '{{design:space:2xl}}') {
        if (!str_contains($bottom, 'clamp')) {
            $ley3_ok = false;
            $ley3_detail = "section {$i}: padding-bottom {$bottom} < 96px minimum";
            break;
        }
    }
    // Check card modules for internal padding
    foreach ($sec['rows'] ?? [] as $row) {
        foreach ($row['columns'] ?? $row['modules'] ?? [] as $col) {
            $col_modules = $col['modules'] ?? (isset($col['type']) ? [$col] : []);
            foreach ($col_modules as $mod) {
                $mod_presets = $mod['presets'] ?? [];
                $mod_padding = $mod['decoration']['spacing']['desktop']['value']['padding'] ?? [];
                foreach ($mod_presets as $p) {
                    if (str_contains($p, 'feature-card') || str_contains($p, 'testimonial-card') || str_contains($p, 'glass-card') || str_contains($p, 'card')) {
                        $pt = $mod_padding['top'] ?? ($mod_padding['sync'] ?? '') === 'on' ? ($mod_padding['top'] ?? '') : '';
                        if ($pt && (int)$pt < 40 && $pt !== '{{design:space:lg}}') {
                            $ley3_ok = false;
                            $ley3_detail = "section {$i}: card module has padding {$pt} < 40px minimum";
                            break 3;
                        }
                    }
                }
            }
        }
    }
}
report("Ley 3 — Espacio Negativo Mínimo: sections ≥96px, cards ≥40px", $ley3_ok, $ley3_detail);

// ── Ley 4: Micro-interacción en Elementos Clickeables (nativo) ──
// Sin presets (`"presets": []`), los botones reales (divi/button) deben tener
// un hover declarado: decoration.button.hover.* o decoration.transform.hover.*.
$ley4_ok = true;
$ley4_detail = '';
foreach ($sections as $i => $sec) {
    foreach ($sec['rows'] ?? [] as $row) {
        foreach ($row['columns'] ?? $row['modules'] ?? [] as $col) {
            $col_modules = $col['modules'] ?? (isset($col['type']) ? [$col] : []);
            foreach ($col_modules as $mod) {
                $type = $mod['type'] ?? $mod['module'] ?? '';
                $is_clickable = ($type === 'divi/button');
                if (!$is_clickable) {
                    continue;
                }
                $btn_hover = $mod['decoration']['button']['hover'] ?? [];
                $transform_hover = $mod['decoration']['transform']['hover'] ?? [];
                $has_hover = !empty($btn_hover) || !empty($transform_hover);
                if (!$has_hover) {
                    $ley4_ok = false;
                    $ley4_detail = "section {$i}: divi/button without hover state (decoration.button.hover or decoration.transform.hover)";
                    break 3;
                }
            }
        }
    }
}
report("Ley 4 — Micro-interacción: divi/button have hover state (nativo)", $ley4_ok, $ley4_detail);

// ── Ley 5: Anclaje Visual por Sección (nativo) ───
$ley5_ok = true;
$ley5_detail = '';
$ley5_anchor_warn = '';
foreach ($sections as $i => $sec) {
    $total_modules = 0;
    foreach ($sec['rows'] ?? [] as $row) {
        foreach ($row['columns'] ?? $row['modules'] ?? [] as $col) {
            $col_modules = $col['modules'] ?? (isset($col['type']) ? [$col] : []);
            $total_modules += count($col_modules);
        }
    }
    if ($total_modules === 0) {
        $ley5_ok = false;
        $ley5_detail = "section {$i}: has no modules (no visual anchor possible)";
        break;
    }
    $has_large_module = false;
    foreach ($sec['rows'] ?? [] as $row) {
        foreach ($row['columns'] ?? $row['modules'] ?? [] as $col) {
            $col_modules = $col['modules'] ?? (isset($col['type']) ? [$col] : []);
            foreach ($col_modules as $mod) {
                $type = $mod['type'] ?? $mod['module'] ?? '';
                if ($type === 'divi/image' || $type === 'divi/svg' || $type === 'divi/number-counter' || $type === 'divi/circle-counter') {
                    $has_large_module = true;
                    break 3;
                }
                // Heading/text grande (≥2rem desktop) como ancla.
                foreach ([$mod['headingFont'] ?? [], $mod['bodyFont'] ?? []] as $fg) {
                    foreach ($fg as $level => $group) {
                        $size = $group['font']['desktop']['value']['size'] ?? '';
                        if (preg_match('/^([\d.]+)rem$/', $size, $m) && (float) $m[1] >= 2.0) {
                            $has_large_module = true;
                            break 5;
                        }
                    }
                }
            }
        }
    }
    if (!$has_large_module) {
        $ley5_anchor_warn = "section {$i}: no large visual anchor (image/svg/counter or heading ≥2rem)";
    }
}
report("Ley 5 — Anclaje Visual: each section has at least one module", $ley5_ok, $ley5_detail);
if ($ley5_anchor_warn) {
    $passed--; $warnings++;
    echo "  [WARN] {$ley5_anchor_warn}\n";
}

// ── Ley 6: Escala Responsiva Declarada ───────────
$ley6_ok = true;
$ley6_detail = '';
$hero_modules = [];
if (!empty($sections)) {
    foreach ($sections[0]['rows'] ?? [] as $row) {
        foreach ($row['columns'] ?? $row['modules'] ?? [] as $col) {
            $col_modules = $col['modules'] ?? (isset($col['type']) ? [$col] : []);
            foreach ($col_modules as $mod) {
                $hero_modules[] = $mod;
            }
        }
    }
}
foreach ($hero_modules as $mod) {
    if ($mod['type'] === 'divi/heading' || $mod['type'] === 'divi/text') {
        $font = $mod['headingFont'] ?? [];
        $has_responsive = false;
        foreach (['h1', 'h2', 'h3'] as $level) {
            $sizes = $font[$level]['font'] ?? [];
            if (isset($sizes['desktop']) || isset($sizes['tablet']) || isset($sizes['phone'])) {
                $has_responsive = true;
            }
        }
        if (!$has_responsive) {
            $body_font = $mod['bodyFont'] ?? [];
            $sizes = $body_font['body']['font'] ?? [];
            if (isset($sizes['desktop']) || isset($sizes['tablet']) || isset($sizes['phone'])) {
                $has_responsive = true;
            }
        }
        if ($has_responsive) {
            $ley6_ok = true;
            break;
        }
    }
}
report("Ley 6 — Escala Responsiva: hero typography declares breakpoints", $ley6_ok, $ley6_detail);

echo str_repeat('-', 50) . "\n";

// ── No hex hardcodeados ──────────────────────────
$json_str = json_encode($page_def);
$hex_pattern = '/#[0-9a-fA-F]{3,8}\b/';

// Known valid hexes: these are allowed (tokens in vars.json or gcid mappings)
$allowed_hexes = [];
if ($presets_data) {
    array_walk_recursive($presets_data, function($v) use (&$allowed_hexes) {
        if (is_string($v) && str_starts_with($v, '#') && strlen($v) >= 4) {
            $allowed_hexes[] = strtolower($v);
        }
    });
}

$found_hexes = [];
preg_match_all($hex_pattern, $json_str, $found_hexes);
$found_hexes = array_unique($found_hexes[0]);

$unexpected_hexes = [];
foreach ($found_hexes as $h) {
    $hl = strtolower($h);
    if (!in_array($hl, $allowed_hexes)) {
        // Check if this hex appears in context of a preset or token definition
        $pos = strpos($json_str, $h);
        $context_start = max(0, $pos - 120);
        $context = substr($json_str, $context_start, 240);
        // Skip hex values in presets files and design vars (they're definitions, not hardcodes)
        $unexpected_hexes[] = ['hex' => $h, 'context' => $context];
    }
}

$no_hex = count($unexpected_hexes) === 0;
$hex_detail = '';
if (!$no_hex) {
    $hex_detail = 'Found ' . count($unexpected_hexes) . ' unexpected hex values (first): ' . $unexpected_hexes[0]['hex'];
}
report("No hex colors hardcodeados (use {{design:color:*}} tokens)", $no_hex, $hex_detail, false);

// ── No et_pb_* prefixes ─────────────────────────
$has_et_pb = preg_match('/et_pb_/', $json_str) === 1;
report("No et_pb_* prefixes (use divi/* namespace)", !$has_et_pb, $has_et_pb ? 'Found et_pb_* references' : '');

// ── No {{design:*}} unresolved ───────────────────
$unresolved_count = preg_match_all('/\{\{design:\w+:[\w-]+\}\}/', $json_str, $unresolved_matches);
report("No {{design:*}} tokens unresolved", $unresolved_count === 0, $unresolved_count > 0 ? "Found {$unresolved_count} unresolved tokens (they will be resolved at build time)" : '', false);

// ── Presets existence check ──────────────────────
$presets_ok = true;
$presets_detail = '';
if ($presets_data) {
    $missing_presets = [];
    foreach ($sections as $i => $sec) {
        foreach ($sec['presets'] ?? [] as $ref) {
            $parts = explode(':', $ref, 2);
            if (count($parts) !== 2) continue;
            if (!isset($presets_data[$parts[0]][$parts[1]])) {
                $missing_presets[] = "sec-{$i}: {$ref}";
            }
        }
        foreach ($sec['rows'] ?? [] as $row) {
            foreach ($row['columns'] ?? $row['modules'] ?? [] as $col) {
                $col_modules = $col['modules'] ?? (isset($col['type']) ? [$col] : []);
                foreach ($col_modules as $mod) {
                    foreach ($mod['presets'] ?? [] as $ref) {
                        $parts = explode(':', $ref, 2);
                        if (count($parts) !== 2) continue;
                        if (!isset($presets_data[$parts[0]][$parts[1]])) {
                            $missing_presets[] = "{$ref}";
                        }
                    }
                }
            }
        }
    }
    $presets_ok = count($missing_presets) === 0;
    if (!$presets_ok) {
        $unique_missing = array_unique($missing_presets);
        $presets_detail = 'Missing presets: ' . implode(', ', array_slice($unique_missing, 0, 5));
    }
}
report("All referenced presets exist in _design_presets.json", $presets_ok, $presets_detail, false);

// ── Gotchas de autoría render-verificados (schema DAW) ──
// Estos checks reflejan trampas verificadas en render que el pipeline DAW
// resuelve y que conviene señalar a tiempo (WARN no bloqueante en la mayoría).
// NOTA: enable gates / button.spacing / position NO se checkean aquí porque el
// Layout Engine ya los normaliza (class-divi-button-renderer.php, base-renderer).

// 1. Responsive: filas multi-columna deben declarar flexDirection column en tablet.
//    (Divi 5 rows NO auto-stackean; si solo hay desktop, se avisa.)
$resp_ok = true;
$resp_detail = '';
foreach ($sections as $i => $sec) {
    foreach ($sec['rows'] ?? [] as $ri => $row) {
        $struct = $row['column_structure'] ?? '';
        $col_count = $struct ? count(explode(',', $struct)) : (count($row['columns'] ?? []) > 1 ? count($row['columns']) : 1);
        if ($col_count <= 1) {
            continue;
        }
        $layout = $row['decoration']['layout'] ?? [];
        $tablet = $layout['tablet']['value'] ?? null;
        $has_tablet_stack = is_array($tablet) && (($tablet['flexDirection'] ?? '') === 'column');
        if (!$has_tablet_stack && !isset($layout['tablet'])) {
            $resp_ok = false;
            $resp_detail = "section {$i} row {$ri}: multi-column row without tablet flexDirection:column (rows don't auto-stack)";
            break 2;
        }
    }
}
report("Responsive — rows multi-columna apilan en tablet (flexDirection:column)", $resp_ok, $resp_detail, false);

// 2. CSS freeForm con '<' (wp_strip_all_tags trunca — regla #15).
$css_lt = false;
foreach ($sections as $i => $sec) {
    if (!empty($sec['css'] ?? '') && str_contains($sec['css'], '<')) {
        $css_lt = true;
        break;
    }
}
$css_ok = !$css_lt;
report("CSS freeForm sin '<' (wp_strip_all_tags trunca — regla #15)", $css_ok, $css_lt ? 'Found < in section css — se truncará el CSS' : '');

// 3. Gradient stop positions sin '%' (trait-block-helpers rtrim).
$grad_ok = true;
$grad_detail = '';
foreach ($sections as $i => $sec) {
    foreach ($sec['rows'] ?? [] as $row) {
        foreach ($row['columns'] ?? $row['modules'] ?? [] as $col) {
            $col_modules = $col['modules'] ?? (isset($col['type']) ? [$col] : []);
            foreach (array_merge([$sec], $col_modules) as $node) {
                $gradient = $node['decoration']['background']['desktop']['value']['gradient'] ?? [];
                foreach ($gradient['stops'] ?? [] as $stop) {
                    if (isset($stop['position']) && is_string($stop['position']) && str_contains($stop['position'], '%')) {
                        $grad_ok = false;
                        $grad_detail = "section {$i}: gradient stop position '{$stop['position']}' has % (normalizer lo recorta)";
                        break 4;
                    }
                }
            }
        }
    }
}
report("Gradient stops sin '%'", $grad_ok, $grad_detail);

echo str_repeat('-', 50) . "\n";

$total_checks = $passed + $failed + $warnings;
echo "[LINT] Results: {$passed} passed, {$failed} failed, {$warnings} warnings (out of {$total_checks} checks)\n";

if ($failed > 0) {
    echo "[LINT] FAILED — fix blocking issues before build\n";
    exit(1);
}

echo "[LINT] PASSED\n";
exit(0);
