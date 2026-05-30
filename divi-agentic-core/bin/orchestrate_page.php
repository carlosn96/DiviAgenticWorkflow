<?php
/**
 * orchestrate_page.php — Design Orquestador v1
 *
 * Unifies: brief → design-patterns → variant selection → compose → build → deploy
 *
 * Usage:
 *   php orchestrate_page.php --brief=mi-pagina.yml [--deploy]
 *   php orchestrate_page.php --help
 *
 * Pipeline:
 *   brief.yml → [orquestador]
 *     ├── Consulta design-patterns.json (composición ideal)
 *     ├── Mapea tone → variant de decoración
 *     ├── Genera .page.json en compositions/
 *     ├── Ejecuta compose_page.php
 *     └── [--deploy] Ejecuta build_page.php --deploy
 */

require_once __DIR__ . '/env_loader.php';
$DIR_SEP = DIRECTORY_SEPARATOR;
define('DAW_ROOT', str_replace('/', $DIR_SEP, dirname(__DIR__, 2)));
define('DAW_SITE', getenv('DAW_SITE') ?: 'bibliotheca');
define('BRIEFS_DIR', DAW_ROOT . $DIR_SEP . 'site' . $DIR_SEP . DAW_SITE . $DIR_SEP . 'briefs');
define('COMPOSITIONS_DIR', DAW_ROOT . $DIR_SEP . 'site' . $DIR_SEP . DAW_SITE . $DIR_SEP . 'compositions');
define('PATTERNS_PATH', DAW_ROOT . $DIR_SEP . 'workspace' . $DIR_SEP . 'design-patterns.json');
define('SECTIONS_DIR', DAW_ROOT . $DIR_SEP . 'workspace' . $DIR_SEP . 'sections');
define('DEFS_DIR', DAW_ROOT . $DIR_SEP . 'site' . $DIR_SEP . DAW_SITE . $DIR_SEP . 'page-defs');

// ─── Tone → Variant Mapping ──────────────────────────
// Each tone gets a distinct visual direction via variants.
// undefined = base template without variant
$TONE_VARIANTS = [
    'editorial'    => ['hero-split' => 'editorial-grid', 'content-split' => 'editorial-grid', 'content-split-icon-list' => 'editorial-list', 'stats-4col' => 'glass-metric'],
    'modern'       => ['hero-centered' => 'liquid-glass', 'features-3col' => 'monochrome-brutalist', 'testimonials-3col' => 'minimal-card', 'logos-4col' => 'dark-scroll', 'cta-centered' => 'glass-cta'],
    'premium'      => ['hero-centered' => 'liquid-glass', 'cta-centered' => 'glass-cta', 'testimonials-3col' => 'minimal-card'],
    'minimal'      => ['hero-centered' => 'liquid-glass', 'logos-4col' => 'dark-scroll', 'stats-4col' => 'glass-metric'],
    'dramatic'     => ['hero-split' => 'editorial-grid', 'content-split' => 'editorial-grid'],
    'playful'      => ['features-3col' => 'monochrome-brutalist', 'logos-4col' => 'dark-scroll'],
];

// ─── Section Type → Template Mapping ─────────────────
$SECTION_TEMPLATES = [
    'hero'          => 'hero-split',
    'hero-centered' => 'hero-centered',
    'features'      => 'features-3col',
    'stats'         => 'stats-4col',
    'testimonials'  => 'testimonials-3col',
    'cta'           => 'cta-centered',
    'content'       => 'content-split',
    'content-list'  => 'content-split-icon-list',
    'logos'         => 'logos-4col',
    'about'         => 'content-split',
    'contact'       => 'content-split',
    'team'          => 'features-3col',
    'gallery'       => 'features-3col',
    'blog'          => 'features-3col',
    'faq'           => 'content-split',
    'timeline'      => 'content-split',
];

// ─── Helpers ─────────────────────────────────────────
function load_json(string $path): ?array {
    if (!file_exists($path)) return null;
    $data = json_decode(file_get_contents($path), true);
    return $data ?: null;
}

function load_patterns(): array {
    $patterns = load_json(PATTERNS_PATH);
    if (!$patterns) {
        fwrite(STDERR, "[ORCH] WARNING: design-patterns.json not found. Run extract_patterns.py first.\n");
        return [];
    }
    return $patterns;
}

function recommend_section_structure(string $section_type, array $patterns): array {
    $archetype = $patterns['composition_archetypes'][$section_type] ?? null;
    if (!$archetype) return [];
    return [
        'column_structures' => array_map(fn($c) => $c['structure'], array_slice($archetype['common_column_structures'] ?? [], 0, 3)),
        'gradient_frequency' => $archetype['gradient_frequency'] ?? 0,
        'divider_frequency' => $archetype['divider_frequency'] ?? 0,
        'avg_modules' => $archetype['avg_modules'] ?? 0,
    ];
}

function suggest_variant(string $tone, string $template): string {
    global $TONE_VARIANTS;
    $tone = strtolower($tone);
    $variants = $TONE_VARIANTS[$tone] ?? $TONE_VARIANTS['editorial'] ?? [];
    $variant = $variants[$template] ?? null;
    return $variant ? "{$template}@{$variant}" : $template;
}

function parse_brief(string $path): array {
    $content = file_get_contents($path);
    if (!$content) {
        fwrite(STDERR, "[ERROR] Cannot read: {$path}\n"); exit(1);
    }

    $brief = ['title' => '', 'slug' => '', 'tone' => 'editorial', 'description' => '', 'sections' => []];
    $lines = explode("\n", $content);

    $state = 'top';        // 'top', 'section', 'section_list'
    $current_sec = null;
    $current_list_key = null;  // which key the current list belongs to
    $current_item = null;

    // indent tracking for the current context
    $top_indent = -1;
    $sec_indent = -1;
    $list_indent = -1;

    foreach ($lines as $line) {
        $line = rtrim($line);
        if ($line === '') continue;
        if (ltrim($line)[0] === '#') continue;

        $indent = 0;
        while ($indent < strlen($line) && $line[$indent] === ' ') $indent++;
        $trimmed = ltrim($line);

        // Top-level keys (indent 0)
        if ($indent === 0) {
            if (preg_match('/^(\w+):\s*(.*)/', $trimmed, $m)) {
                $key = $m[1];
                $val = trim($m[2]);
                $val = trim($val, '"');
                if (in_array($key, ['title', 'slug', 'description', 'tone'])) {
                    $brief[$key] = $val;
                }
                if ($key === 'sections') {
                    $state = 'section';
                    $sec_indent = $indent;
                }
            }
            continue;
        }

        // New section list item
        // Two cases: first section (state=section) or subsequent (state=section_list, same indent)
        if (($state === 'section' || ($state === 'section_list' && $indent === $sec_indent))
            && preg_match('/^-\s+(.+)/', $trimmed, $m)) {
            // Flush previous section and item
            if ($current_item && $current_list_key && $current_sec) {
                $current_sec['slots'][$current_list_key][] = $current_item;
                $current_item = null;
            }
            if ($current_sec) {
                $brief['sections'][] = $current_sec;
            }

            $item_text = trim($m[1]);
            $sec_indent = $indent;
            $state = 'section_list';

            if (preg_match('/^(\w+):\s*(.*)/', $item_text, $im)) {
                $current_sec = [
                    'section_type' => trim($im[2]),
                    'slots' => [],
                ];
            }
            $current_list_key = null;
            continue;
        }

        // Properties within a list item (must come before section properties)
        if ($current_item && $indent > $list_indent && preg_match('/^(\w+):\s*(.*)/', $trimmed, $m)) {
            $current_item[$m[1]] = trim(trim($m[2]), '"');
            continue;
        }

        // List items within a slot list (stats, features, items, testimonials)
        if ($current_list_key && $indent >= $list_indent && preg_match('/^-\s+(.+)/', $trimmed, $m)) {
            // Flush previous item
            if ($current_item && $current_sec) {
                $current_sec['slots'][$current_list_key][] = $current_item;
            }
            $item_text = trim($m[1]);
            if (preg_match('/^(\w+):\s*(.*)/', $item_text, $im)) {
                $current_item = [$im[1] => trim(trim($im[2]), '"')];
            } else {
                $current_item = ['_value' => $item_text];
            }
            continue;
        }

        // Properties within a section
        if (in_array($state, ['section', 'section_list']) && $indent > $sec_indent) {
            if (preg_match('/^(\w+):\s*(.*)/', $trimmed, $m)) {
                $key = $m[1];
                $val = trim($m[2]);
                $val = trim($val, '"');

                if ($val === '') {
                    // Start a list
                    $current_list_key = $key;
                    $list_indent = $indent;
                    $current_item = null;
                } else {
                    // Direct slot value
                    if ($current_sec) {
                        $current_sec['slots'][$key] = $val;
                    }
                    $current_list_key = null;
                }
                continue;
            }
        }

        // Transition: if indent drops back to section level, end list
        if ($current_list_key && $indent <= $list_indent && $indent > $sec_indent) {
            if ($current_item && $current_sec) {
                $current_sec['slots'][$current_list_key][] = $current_item;
                $current_item = null;
            }
            $current_list_key = null;

            // Re-process this line as a section property
            if (preg_match('/^(\w+):\s*(.*)/', $trimmed, $m)) {
                $key = $m[1];
                $val = trim($m[2]);
                $val = trim($val, '"');
                if ($val === '') {
                    $current_list_key = $key;
                    $list_indent = $indent;
                } else {
                    if ($current_sec) {
                        $current_sec['slots'][$key] = $val;
                    }
                }
            }
            continue;
        }
    }

    // Flush last section and last item
    if ($current_item && $current_list_key && $current_sec) {
        $current_sec['slots'][$current_list_key][] = $current_item;
    }
    if ($current_sec) {
        $brief['sections'][] = $current_sec;
    }

    return $brief;
}

// ─── Build composition from brief ────────────────────
function build_composition(array $brief, array $patterns): array {
    global $SECTION_TEMPLATES;
    $sections = [];
    $tone = $brief['tone'] ?? 'editorial';
    $slug = $brief['slug'] ?? 'page';

    // Premium Citas Literarias indexadas por slug para dar diversidad al Hero
    $LITERARY_QUOTES = [
        'home' => [
            'icon' => '&#x1F4D6;',
            'text' => '"El universo (que otros llaman la Biblioteca) se compone de un número indefinido, y tal vez infinito, de galerías hexagonales..."',
            'attribution' => '— Jorge Luis Borges'
        ],
        'contacto' => [
            'icon' => '&#x1F5E8;',
            'text' => '"El diálogo es el camino para llegar a la verdad, revelando lo que yace en el silencio del pensamiento."',
            'attribution' => '— Umberto Eco'
        ],
        'about' => [
            'icon' => '&#x1F570;',
            'text' => '"No hay nada más noble en la mente que el deseo de comprender, recopilar y resguardar el conocimiento de los siglos."',
            'attribution' => '— Erasmo de Rotterdam'
        ],
        'default' => [
            'icon' => '&#x2728;',
            'text' => '"La lectura abre reinos inexplorados, convirtiendo el silencio de las páginas en elocuentes revelaciones del espíritu."',
            'attribution' => '— Bibliotheca'
        ]
    ];

    $section_counts = [];

    foreach ($brief['sections'] as $i => $sec_def) {
        $type = $sec_def['section_type'] ?? 'generic';
        
        // Track section counts of the same type for alternation (zigzag)
        $section_counts[$type] = ($section_counts[$type] ?? 0) + 1;
        $occurrence = $section_counts[$type];

        // Determine section template
        $template_name = $SECTION_TEMPLATES[$type] ?? null;
        if (!$template_name) {
            fwrite(STDERR, "[ORCH] WARNING: No template for section type '{$type}', skipping\n");
            continue;
        }

        // Get pattern recommendation for this section type
        $rec = recommend_section_structure($type, $patterns);
        if (!empty($rec)) {
            fwrite(STDERR, "[ORCH]  pattern: {$type} → {$rec['avg_modules']}avg modules, gradient:{$rec['gradient_frequency']}\n");
        }

        // 🥇 Priority: local base templates with variants (premium, curated)
        $template = null;
        if ($template_name) {
            $variant_name = suggest_variant($tone, $template_name);
            
            // Alternate layout template to avoid identical structures on the same page
            if ($occurrence > 1 && $type === 'content') {
                // If we have multiple content sections, switch to centered or staggered variants
                $alt_template = 'content-split-icon-list';
                $base_path_alt = SECTIONS_DIR . DIRECTORY_SEPARATOR . $alt_template . DIRECTORY_SEPARATOR . '_base.section.json';
                if (file_exists($base_path_alt)) {
                    $template = suggest_variant($tone, $alt_template);
                    fwrite(STDERR, "[ORCH]  Alternating Template: {$type} occurrence {$occurrence} → {$template}\n");
                }
            }

            if (!$template) {
                $base_path = SECTIONS_DIR . DIRECTORY_SEPARATOR . $template_name . DIRECTORY_SEPARATOR . '_base.section.json';
                if (file_exists($base_path)) {
                    $template = $variant_name;
                    fwrite(STDERR, "[ORCH]  Local Template: {$type} → {$template}\n");
                } else {
                    fwrite(STDERR, "[ORCH]  Base template NOT FOUND: {$base_path}\n");
                }
            }
        }

        // 🥈 Fallback: semantic catalog search (only if no local template exists)
        if (!$template) {
            $title_query = $slots['title'] ?? $sec_def['title'] ?? '';
            $query_str = trim("{$tone} {$type} {$title_query}");
            $search_cmd = sprintf('python "%s" --category %s --query %s --limit 1 2>&1', 
                DAW_ROOT . '/workspace/automation/search_catalog.py', 
                escapeshellarg($type),
                escapeshellarg($query_str)
            );
            
            $search_output = shell_exec($search_cmd);
            $search_results = json_decode($search_output, true);
            
            if (!empty($search_results) && isset($search_results[0]['name'])) {
                $matched_name = $search_results[0]['name'];
                $score = $search_results[0]['score'] ?? 0;
                
                $threshold = 0.60;
                $blacklist = ['kindergarten', 'day-care', 'kinder', 'child', 'baby', 'toy', 'play', 'day_care', 'pets', 'pet', 'dog', 'cat', 'spa', 'beauty', 'salon', 'hair', 'yoga', 'makeup', 'plumber', 'roofing', 'repair', 'mechanic', 'dentist', 'dental', 'massage'];
                
                $is_blacklisted = false;
                $matched_name_lower = strtolower($matched_name);
                foreach ($blacklist as $bad_word) {
                    if (str_contains($matched_name_lower, $bad_word)) {
                        $is_blacklisted = true;
                        break;
                    }
                }
                
                if ($score >= $threshold && !$is_blacklisted) {
                    $target_template_path = SECTIONS_DIR . DIRECTORY_SEPARATOR . 'catalog' . DIRECTORY_SEPARATOR . $matched_name . '.section.json';
                    if (file_exists($target_template_path)) {
                        $template = "catalog/{$matched_name}";
                        fwrite(STDERR, "[ORCH]  Catalog Fallback: '{$query_str}' -> '{$template}' (score: {$score})\n");
                    }
                } else {
                    if ($is_blacklisted) {
                        fwrite(STDERR, "[ORCH]  Catalog Match Rejected (Blacklisted niche): '{$matched_name}'\n");
                    } else {
                        fwrite(STDERR, "[ORCH]  Catalog Match Rejected (Score {$score} < {$threshold}): '{$matched_name}'\n");
                    }
                }
            }
        }
        
        if (!$template) {
            fwrite(STDERR, "[ORCH]  WARNING: No template resolved for section '{$type}', skipping\n");
            continue;
        }

        // Build slots from brief content (any non-reserved key is a slot)
        $reserved = ['section_type', 'type', 'slots', 'template'];
        $slots = $sec_def['slots'] ?? [];
        foreach ($sec_def as $k => $v) {
            if (!in_array($k, $reserved)) {
                $slots[$k] = $v;
            }
        }

        // Normalize slot keys for all section types
        // Maps common brief key aliases to the template-expected slot names
        $slots['btn_primary_text'] ??= $slots['btn_text'] ?? $slots['button_text'] ?? '';
        $slots['btn_primary_url'] ??= $slots['btn_url'] ?? $slots['button_url'] ?? '';
        $slots['btn_secondary_text'] ??= $slots['btn_secondary_text'] ?? '';
        $slots['btn_secondary_url'] ??= $slots['btn_secondary_url'] ?? '';
        $slots['eyebrow'] ??= $slots['eyebrow'] ?? $slots['kicker'] ?? '';
        $slots['title'] ??= $slots['title'] ?? 'Título';
        $slots['text'] ??= $slots['text'] ?? '';
        
        // Hero: ensure decorative slots exist with diverse literary defaults (non-identical)
        $quote = $LITERARY_QUOTES[$slug] ?? $LITERARY_QUOTES['default'];
        $slots['decorative_icon'] ??= $quote['icon'];
        $slots['decorative_text'] ??= $quote['text'];
        $slots['decorative_attribution'] ??= $quote['attribution'];

        // Features: inject default unicode icons for items that lack them
        if (isset($slots['features']) && is_array($slots['features'])) {
            $default_icons = ['&#xe03a;', '&#xe065;', '&#xe0bf;', '&#xe049;', '&#xe0e4;', '&#xe025;'];
            foreach ($slots['features'] as $fi => &$item) {
                if (is_array($item) && empty($item['icon'])) {
                    $item['icon'] = $default_icons[$fi % count($default_icons)];
                }
            }
            unset($item);
        }

        $sections[] = [
            'template' => $template,
            'slots' => $slots,
        ];
    }

    return [
        'title' => $brief['title'] ?? 'Page',
        'slug' => $brief['slug'] ?? 'page',
        'description' => $brief['description'] ?? '',
        'sections' => $sections,
    ];
}

// ─── Main (only when executed directly) ───────────────
$is_main = (php_sapi_name() === 'cli' && isset($argv[0]) && realpath($argv[0]) === realpath(__FILE__));
if (!$is_main) { return; }
$opts = getopt('', ['brief::', 'deploy', 'help']);
$brief_name = $opts['brief'] ?? null;

if (isset($opts['help']) || !$brief_name) {
    echo "Usage: php orchestrate_page.php --brief=<name> [--deploy]\n\n";
    echo "  --brief=<name>  Brief name (e.g. 'home' → site/<site>/briefs/home.yml)\n";
    echo "  --deploy        Build + deploy to WordPress\n";
    echo "  --help          This message\n\n";
    echo "Pipeline: brief.yml → patterns + variant → compose → [build_page.php --deploy]\n";
    echo "Skills: ui-ux-pro-max (style), frontend-design (variants), design-patterns (composition)\n";
    exit(isset($opts['help']) ? 0 : 1);
}

// Find brief file
$brief_path = BRIEFS_DIR . DIRECTORY_SEPARATOR . $brief_name . '.yml';
if (!file_exists($brief_path)) {
    fwrite(STDERR, "[ERROR] Brief not found: {$brief_path}\n");
    fwrite(STDERR, "[HINT] Create briefs in: " . BRIEFS_DIR . "\n");
    exit(1);
}

echo "[ORCH] Reading brief: {$brief_path}\n";
$brief = parse_brief($brief_path);
echo "[ORCH] Tone: {$brief['tone']}\n";
echo "[ORCH] Sections: " . count($brief['sections']) . "\n";

// Load design patterns
$patterns = load_patterns();

// Build composition
$composition = build_composition($brief, $patterns);
$slug = $composition['slug'];

// Write composition to compositions/
if (!is_dir(COMPOSITIONS_DIR)) {
    mkdir(COMPOSITIONS_DIR, 0777, true);
}
$comp_path = COMPOSITIONS_DIR . DIRECTORY_SEPARATOR . "{$slug}.page.json";
file_put_contents($comp_path, json_encode($composition, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES));
echo "[ORCH] Composition written: {$comp_path}\n";

    // Run compose_page.php (same directory as this script)
    $compose_script = dirname(__FILE__) . DIRECTORY_SEPARATOR . 'compose_page.php';
$compose_cmd = sprintf('"%s" "%s" --page=%s 2>&1', PHP_BINARY, $compose_script, "{$slug}.page.json");
echo "[ORCH] Running compose...\n";
passthru($compose_cmd, $compose_exit);

if ($compose_exit !== 0) {
    fwrite(STDERR, "[ERROR] compose_page.php failed (exit {$compose_exit})\n");
    exit(1);
}

// Run post_compose.php (premium decoration injection, demo image cleanup)
$post_script = dirname(__FILE__) . DIRECTORY_SEPARATOR . 'post_compose.php';
$post_cmd = sprintf('"%s" "%s" --def=%s.json 2>&1', PHP_BINARY, $post_script, $slug);
echo "[ORCH] Running post-compose...\n";
passthru($post_cmd, $post_exit);
if ($post_exit !== 0) {
    fwrite(STDERR, "[WARN] post_compose.php had issues (exit {$post_exit})\n");
}

// Deploy if requested
if (isset($opts['deploy'])) {
    $build_script = dirname(__FILE__) . DIRECTORY_SEPARATOR . 'build_page.php';
    $build_cmd = sprintf('"%s" "%s" --def=%s.json --deploy 2>&1', PHP_BINARY, $build_script, $slug);
    echo "[ORCH] Running build + deploy...\n";
    passthru($build_cmd, $build_exit);
    if ($build_exit !== 0) {
        fwrite(STDERR, "[ERROR] build_page.php failed (exit {$build_exit})\n");
        exit(1);
    }
    echo "[ORCH] Deployed: {$slug}\n";
}

echo "[ORCH] Done.\n";
