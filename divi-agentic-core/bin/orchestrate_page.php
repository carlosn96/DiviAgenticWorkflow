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
define('CATALOG_SECTIONS_DIR', SECTIONS_DIR . $DIR_SEP . 'catalog');
define('DIE_SCRIPT', DAW_ROOT . $DIR_SEP . 'ml-dataset' . $DIR_SEP . 'artifacts' . $DIR_SEP . 'design_intelligence.py');
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
        fwrite(STDOUT, "[ORCH] WARNING: design-patterns.json not found. Run extract_patterns.py first.\n");
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

function call_die(array $brief): ?array {
    $tmp_path = sys_get_temp_dir() . DIRECTORY_SEPARATOR . 'die_brief_' . uniqid() . '.json';
    $sections = [];
    foreach ($brief['sections'] as $sec) {
        $slots = $sec['slots'] ?? $sec;
        $sections[] = [
            'title' => $slots['title'] ?? $sec['title'] ?? '',
            'text' => $slots['text'] ?? $sec['text'] ?? '',
            'section_type' => $sec['section_type'] ?? 'generic',
        ];
    }
    $die_input = ['tone' => $brief['tone'] ?? 'editorial', 'sections' => $sections];
    file_put_contents($tmp_path, json_encode($die_input, JSON_UNESCAPED_UNICODE));

    // Resolve python CLI command to use venv python with PyTorch/SentenceTransformers
    $python_cmd = getenv('PYTHON_CLI_COMMAND') ?: 'python';
    $venv_python = DAW_ROOT . DIRECTORY_SEPARATOR . 'worskpace' . DIRECTORY_SEPARATOR . 'scraper' . DIRECTORY_SEPARATOR . 'venv' . DIRECTORY_SEPARATOR . 'Scripts' . DIRECTORY_SEPARATOR . 'python.exe';
    if ($python_cmd === 'python' && file_exists($venv_python)) {
        $python_cmd = '"' . $venv_python . '"';
    }

    $cmd = sprintf('%s "%s" --brief-file "%s" 2>nul', $python_cmd, DIE_SCRIPT, $tmp_path);
    $output = shell_exec($cmd);
    unlink($tmp_path);
    if (!$output) { fwrite(STDOUT, "[ORCH] DIE: no output\n"); return null; }

    // Extract JSON array or object from output (ignores debug logs/warnings)
    if (preg_match('/(\[\s*\{.*\}\s*\]|\{\s*".*"\s*\})/s', $output, $matches)) {
        $plans = json_decode($matches[1], true);
    } else {
        $plans = json_decode($output, true);
    }

    if (!is_array($plans)) {
        fwrite(STDOUT, "[ORCH] DIE: invalid JSON. Raw output was:\n" . $output . "\n");
        return null;
    }
    return $plans;
}

function parse_brief(string $path): array {
    $content = file_get_contents($path);
    if (!$content) {
        fwrite(STDOUT, "[ERROR] Cannot read: {$path}\n"); exit(1);
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
            // Collect indented lines for YAML literal block scalar (body: | ...)
            // MUST be checked BEFORE key:value patterns to handle lines with colons
            if (isset($key) && isset($block_indent) && $indent >= $block_indent) {
                $block_lines[] = $trimmed;
                continue;
            }
            // End of block scalar — flush collected lines
            if (isset($key) && isset($block_lines) && $block_lines) {
                if ($current_sec) {
                    $current_sec['slots'][$key] = implode("\n", $block_lines);
                }
                $current_list_key = null;
                unset($key, $block_indent, $block_lines);
                // Re-process this line as a new section property
                if (preg_match('/^(\w+):\s*(.*)/', $trimmed, $m)) {
                    $nk = $m[1];
                    $nv = trim(trim($m[2]), '"');
                    if ($nv === '') {
                        $current_list_key = $nk;
                        $list_indent = $indent;
                    } elseif ($current_sec) {
                        $current_sec['slots'][$nk] = $nv;
                    }
                }
                continue;
            }
            if (preg_match('/^(\w+):\s*(.*)/', $trimmed, $m)) {
                $key = $m[1];
                $val = trim($m[2]);
                $val = trim($val, '"');

                if ($val === '') {
                    // Start a list
                    $current_list_key = $key;
                    $list_indent = $indent;
                    $current_item = null;
                } elseif ($val === '|') {
                    // YAML literal block scalar: read following indented lines
                    $block_lines = [];
                    $block_indent = $indent + 2;
                    continue;
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

            // Flush any pending literal block scalar
            if (isset($key) && isset($block_lines) && $block_lines) {
                if ($current_sec) {
                    $current_sec['slots'][$key] = implode("\n", $block_lines);
                }
                unset($key, $block_indent, $block_lines);
            }

            // Re-process this line as a section property
            if (preg_match('/^(\w+):\s*(.*)/', $trimmed, $m)) {
                $key2 = $m[1];
                $val2 = trim(trim($m[2]), '"');
                if ($val2 === '') {
                    $current_list_key = $key2;
                    $list_indent = $indent;
                } else {
                    if ($current_sec) {
                        $current_sec['slots'][$key2] = $val2;
                    }
                }
            }
            continue;
        }
    }

    // Flush last section and last item
    if (isset($key) && isset($block_lines) && $block_lines) {
        if ($current_sec) {
            $current_sec['slots'][$key] = implode("\n", $block_lines);
        }
    }
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

    // 🧠 Try DIE first for structural recommendations only (no template injection)
    $die_plans = null;
    if (file_exists(DIE_SCRIPT)) {
        $die_plans = call_die($brief);
    } else {
        fwrite(STDOUT, "[ORCH] DIE script not found: " . DIE_SCRIPT . ", skipping\n");
    }

    foreach ($brief['sections'] as $i => $sec_def) {
        $type = $sec_def['section_type'] ?? 'generic';
        
        // Track section counts of the same type for alternation (zigzag)
        $section_counts[$type] = ($section_counts[$type] ?? 0) + 1;
        $occurrence = $section_counts[$type];

        // Determine section template
        $template = null;
        $slots = $sec_def['slots'] ?? [];
        foreach ($sec_def as $k => $v) {
            if (!in_array($k, ['section_type', 'type', 'slots', 'template'])) {
                $slots[$k] = $v;
            }
        }

        // 🥇 Priority 1: DIE structural recommendations only (no catalog template injection)
        $die_plan = $die_plans[$i] ?? null;
        if ($die_plan && !empty($die_plan['recommended_structure'])) {
            fwrite(STDOUT, "[ORCH]  DIE Recommendation: {$type} → {$die_plan['recommended_structure']}\n");
        }

        // 🥈 Priority 2: local base templates (premium, curated, clean slots)
        if (!$template && isset($SECTION_TEMPLATES[$type])) {
            $template_name = $SECTION_TEMPLATES[$type];
            $base_path = SECTIONS_DIR . DIRECTORY_SEPARATOR . $template_name . DIRECTORY_SEPARATOR . '_base.section.json';
            if (file_exists($base_path)) {
                $variant_name = suggest_variant($tone, $template_name);
                if ($occurrence > 1 && $type === 'content') {
                    $alt_template = 'content-split-icon-list';
                    $base_path_alt = SECTIONS_DIR . DIRECTORY_SEPARATOR . $alt_template . DIRECTORY_SEPARATOR . '_base.section.json';
                    if (file_exists($base_path_alt)) {
                        $template = suggest_variant($tone, $alt_template);
                        fwrite(STDOUT, "[ORCH]  Alternating: {$type} #{$occurrence} → {$template}\n");
                    }
                }
                if (!$template) {
                    $template = $variant_name;
                    fwrite(STDOUT, "[ORCH]  Local: {$type} → {$template}\n");
                }
            } else {
                fwrite(STDOUT, "[ORCH]  Base NOT FOUND: {$base_path}\n");
            }
        }

        // 🥉 Fallback: skeleton section (no catalog template injection — catalog is reference only)
        if (!$template) {
            $template = '_skeleton';
            fwrite(STDOUT, "[ORCH]  Skeleton: {$type} → no template, using empty skeleton\n");
        }

        // Get pattern recommendation for this section type
        $rec = recommend_section_structure($type, $patterns);
        if (!empty($rec)) {
            fwrite(STDOUT, "[ORCH]  pattern: {$type} → {$rec['avg_modules']}avg, gradient:{$rec['gradient_frequency']}\n");
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
        $slots['body'] ??= $slots['body_text'] ?? '';
        
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
            'section_type' => $type,
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
    fwrite(STDOUT, "[ERROR] Brief not found: {$brief_path}\n");
    fwrite(STDOUT, "[HINT] Create briefs in: " . BRIEFS_DIR . "\n");
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
    fwrite(STDOUT, "[ERROR] compose_page.php failed (exit {$compose_exit})\n");
    exit(1);
}

// Run post_compose.php (premium decoration injection, demo image cleanup)
$post_script = dirname(__FILE__) . DIRECTORY_SEPARATOR . 'post_compose.php';
$post_cmd = sprintf('"%s" "%s" --def=%s.json 2>&1', PHP_BINARY, $post_script, $slug);
echo "[ORCH] Running post-compose...\n";
passthru($post_cmd, $post_exit);
if ($post_exit !== 0) {
    fwrite(STDOUT, "[WARN] post_compose.php had issues (exit {$post_exit})\n");
}

// Deploy if requested
if (isset($opts['deploy'])) {
    $build_script = dirname(__FILE__) . DIRECTORY_SEPARATOR . 'build_page.php';
    $build_cmd = sprintf('"%s" "%s" --def=%s.json --deploy 2>&1', PHP_BINARY, $build_script, $slug);
    echo "[ORCH] Running build + deploy...\n";
    passthru($build_cmd, $build_exit);
    if ($build_exit !== 0) {
        fwrite(STDOUT, "[ERROR] build_page.php failed (exit {$build_exit})\n");
        exit(1);
    }
    echo "[ORCH] Deployed: {$slug}\n";
}

echo "[ORCH] Done.\n";
