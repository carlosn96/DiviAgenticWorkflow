<?php
/**
 * post_compose.php — Premium Design Post-Composition
 *
 * Enhances a page-def after compose_page.php:
 *   1. Injects brand presets into sections/modules lacking decoration
 *   2. Replaces demo/catalog image URLs with brand-safe placeholders
 *   3. Applies sensible decoration defaults per section type
 *
 * Usage:
 *   php post_compose.php --def=slug.json
 *   php post_compose.php --def=path/to/page-def.json --out=output.json
 */

require_once __DIR__ . '/env_loader.php';
$DIR_SEP = DIRECTORY_SEPARATOR;
define('DAW_ROOT', str_replace('/', $DIR_SEP, dirname(__DIR__, 2)));
define('DAW_SITE', getenv('DAW_SITE') ?: 'bibliotheca');
define('DEFS_DIR', DAW_ROOT . $DIR_SEP . 'site' . $DIR_SEP . DAW_SITE . $DIR_SEP . 'page-defs');
define('DS_PATH', DAW_ROOT . $DIR_SEP . 'site' . $DIR_SEP . DAW_SITE . $DIR_SEP . 'design-system' . $DIR_SEP . 'divitheme.json');

// ─── Default presets per section type ──────────────────────
$SECTION_DEFAULTS = [
    'hero'              => ['section:hero-dark'],
    'hero-centered'     => ['section:hero-dark'],
    'features'          => ['section:light'],
    'stats'             => ['section:trust-bar'],
    'testimonials'      => ['section:light'],
    'cta'               => ['section:cta-epic'],
    'content'           => ['section:light'],
    'content-list'      => ['section:dark'],
    'logos'             => ['section:light'],
    'about'             => ['section:light'],
    'contact'           => ['section:white'],
    'team'              => ['section:light'],
    'gallery'           => ['section:white'],
    'blog'              => ['section:light'],
    'faq'               => ['section:white'],
    'timeline'          => ['section:light'],
];

$MODULE_DEFAULTS = [
    'divi/blurb'        => ['module:feature-card'],
    'divi/number-counter' => ['module:stat-item'],
    'divi/button'       => ['module:btn-primary'],
    'divi/image'        => ['module:image-shadow'],
];

$DEMO_URL_PATTERNS = [
    '/\/\/divi\.space\//i',
    '/\/\/placehold\.co\//i',
    '/\/\/picsum\.photos\//i',
    '/\/\/source\.unsplash\.com\//i',
    '/\/\/via\.placeholder\.com\//i',
    '/\/\/unsplash\.com\/photos\//i',
    '/\/\/images\.unsplash\.com\//i',
    '/\/\/diviplus\.io\//i',
    '/\/\/divilayoutsextended\.com\//i',
    '/\/\/elegantthemes\.com\//i',
    '/\/\/elegantblocks\.com\//i',
    '/\/\/divilayouts\.com\//i',
];

function load_json(string $path): ?array {
    if (!file_exists($path)) return null;
    $data = json_decode(file_get_contents($path), true);
    return $data ?: null;
}

function deep_merge(array $base, array $override): array {
    $result = $base;
    foreach ($override as $key => $val) {
        if (isset($result[$key]) && is_array($result[$key]) && is_array($val)) {
            $result[$key] = deep_merge($result[$key], $val);
        } else {
            $result[$key] = $val;
        }
    }
    return $result;
}

function detect_section_type(array $section): string {
    if (isset($section['_section_type'])) return $section['_section_type'];
    $rows = $section['rows'] ?? [];
    if (empty($rows)) return 'content';
    $modules = [];
    foreach ($rows as $row) {
        $columns = $row['columns'] ?? [];
        foreach ($columns as $col) {
            foreach ($col['modules'] ?? [] as $mod) {
                $modules[] = $mod['type'] ?? '';
            }
        }
    }
    $types = array_count_values($modules);
    $top = $types ? array_search(max($types), $types) : '';
    if (str_contains($top, 'number-counter')) return 'stats';
    if (str_contains($top, 'blurb') && ($types['divi/blurb'] ?? 0) >= 3) return 'features';
    if (str_contains($top, 'testimonial')) return 'testimonials';
    return 'content';
}

function has_decoration(array $node): bool {
    if (isset($node['decoration']) && !empty($node['decoration'])) return true;
    if (isset($node['presets']) && !empty($node['presets'])) return true;
    return false;
}

function inject_section_presets(array $section, string $section_type, int $content_section_count, string $page_tone, array $design_system): array {
    // Dynamic presets based on tone and section order
    $presets = [];
    if ($section_type === 'hero' || $section_type === 'hero-centered') {
        $presets = ($page_tone === 'minimal' || $page_tone === 'white') ? ['section:white'] : ['section:hero-dark'];
    } elseif ($section_type === 'cta') {
        $presets = ($page_tone === 'minimal') ? ['section:white'] : ['section:cta-epic'];
    } elseif (in_array($section_type, ['features', 'content', 'content-list', 'testimonials', 'logos', 'about', 'team', 'gallery', 'faq', 'timeline'])) {
        // Alternation logic for normal sections
        if ($page_tone === 'modern' || $page_tone === 'dramatic') {
            // Alternates between dark and light sections
            $presets = ($content_section_count % 2 === 0) ? ['section:dark'] : ['section:light'];
        } elseif ($page_tone === 'minimal') {
            // Minimal uses light and white
            $presets = ($content_section_count % 2 === 0) ? ['section:light'] : ['section:white'];
        } else {
            // Editorial/Premium uses white and parchment (light)
            $presets = ($content_section_count % 2 === 0) ? ['section:white'] : ['section:light'];
        }
    } else {
        // Default mapping per section type
        global $SECTION_DEFAULTS;
        $presets = $SECTION_DEFAULTS[$section_type] ?? $SECTION_DEFAULTS['content'];
    }

    $existing_presets = $section['presets'] ?? [];
    
    // Only inject if section has no brand presets already
    $has_brand_preset = false;
    foreach ($existing_presets as $p) {
        if (str_starts_with($p, 'section:')) {
            $has_brand_preset = true;
            break;
        }
    }
    
    if (!$has_brand_preset) {
        $section['presets'] = array_unique(array_merge($presets, $existing_presets));
        fwrite(STDERR, "[POSTC]  injected alternating section presets: " . implode(', ', $presets) . " ({$section_type}, tone: {$page_tone})\n");
    }
    
    // Strip external background images from catalog templates
    if (isset($section['decoration']['background']['desktop']['value']['image']['url'])) {
        $url = $section['decoration']['background']['desktop']['value']['image']['url'];
        if (preg_match('/\/\/(?:diviplus|divilayoutsextended|elegantthemes|elegantblocks|divilayouts|divi\.space|unsplash|picsum|placehold)\./i', $url)) {
            unset($section['decoration']['background']['desktop']['value']['image']);
            fwrite(STDERR, "[POSTC]  stripped catalog background image\n");
        }
    }
    
    // Remove hardcoded gradients from catalog (section preset provides brand gradient)
    if (isset($section['decoration']['background']['desktop']['value']['gradient'])) {
        unset($section['decoration']['background']['desktop']['value']['gradient']);
    }
    
    return $section;
}

function inject_module_presets(array $module): array {
    global $MODULE_DEFAULTS;
    $type = $module['type'] ?? '';
    if (!has_decoration($module) && isset($MODULE_DEFAULTS[$type])) {
        $module['presets'] = $module['presets'] ?? $MODULE_DEFAULTS[$type];
        fwrite(STDERR, "[POSTC]  injected module presets: " . implode(', ', $MODULE_DEFAULTS[$type]) . " ({$type})\n");
    }
    return $module;
}

function strip_demo_images($value) {
    global $DEMO_URL_PATTERNS;
    if (is_string($value)) {
        $cleaned = $value;
        foreach ($DEMO_URL_PATTERNS as $pattern) {
            $cleaned = preg_replace($pattern, '//brand.placeholder/', $cleaned);
        }
        if ($cleaned !== $value) {
            fwrite(STDERR, "[POSTC]  replaced demo image URL\n");
        }
        return $cleaned;
    }
    if (is_array($value)) {
        $result = [];
        foreach ($value as $k => $v) {
            $result[$k] = strip_demo_images($v);
        }
        return $result;
    }
    return $value;
}

// ─── Process sections recursively ──────────────────────────
function strip_placeholder_modules(array &$modules): void {
    $modules = array_values(array_filter($modules, function($mod) {
        $type = $mod['type'] ?? '';
        if ($type === 'divi/placeholder') {
            fwrite(STDERR, "[POSTC]  stripped divi/placeholder module\n");
            return false;
        }
        return true;
    }));
}

function is_section_dark(array $section): bool {
    $presets = $section['presets'] ?? [];
    foreach ($presets as $p) {
        if ($p === 'section:hero-dark' || $p === 'section:dark' || $p === 'section:cta-epic') {
            return true;
        }
    }
    if (isset($section['_section_type']) && in_array($section['_section_type'], ['hero', 'cta'])) {
        return true;
    }
    return false;
}

function correct_module_contrast(array &$mod, bool $is_dark, string $text_role = 'text', string $section_type = 'content', string $button_role = 'primary'): void {
    $type = $mod['type'] ?? '';
    
    // Enforce heading styling
    if ($type === 'divi/heading') {
        $existing_presets = $mod['presets'] ?? [];
        $new_presets = [];
        
        foreach ($existing_presets as $p) {
            if (!str_starts_with($p, 'text:')) {
                $new_presets[] = $p;
            }
        }
        
        $level = $mod['level'] ?? 'h2';
        
        if ($is_dark) {
            if ($level === 'h1') {
                $new_presets[] = 'text:display-xl-light';
            } elseif ($level === 'h2') {
                $new_presets[] = 'text:display-md-light';
            } else {
                $new_presets[] = 'text:headline-light';
            }
        } else {
            if ($level === 'h1') {
                $new_presets[] = 'text:display-xl';
            } elseif ($level === 'h2') {
                $new_presets[] = 'text:display-md';
            } else {
                $new_presets[] = 'text:headline';
            }
        }
        $mod['presets'] = array_unique($new_presets);
        
        // Overwrite headingFont color in correct structure
        $heading_color = $is_dark ? '{{design:color:parchment-50}}' : '{{design:color:ink}}';
        $mod['headingFont'] = [
            $level => [
                'font' => [
                    'desktop' => [
                        'value' => [
                            'color' => $heading_color
                        ]
                    ]
                ]
            ]
        ];
        
        // Strip any hardcoded local colors/spacing to let presets control it
        if (isset($mod['decoration']['headingFont'])) {
            unset($mod['decoration']['headingFont']);
        }
    }
    
    // Enforce text styling
    if ($type === 'divi/text') {
        $existing_presets = $mod['presets'] ?? [];
        $new_presets = [];
        
        foreach ($existing_presets as $p) {
            if (!str_starts_with($p, 'text:')) {
                $new_presets[] = $p;
            }
        }
        
        // Native color mode helper (light/dark text contrast class)
        $mod['advanced']['text']['text']['desktop']['value']['color'] = $is_dark ? 'light' : 'dark';
        
        if ($text_role === 'title') {
            $is_hero = ($section_type === 'hero' || $section_type === 'hero-centered');
            $level = $is_hero ? 'h1' : 'h2';
            $heading_color = $is_dark ? '{{design:color:parchment-50}}' : '{{design:color:ink}}';
            
            if ($is_hero) {
                if ($is_dark) {
                    $new_presets[] = 'text:hero-title';
                } else {
                    $new_presets[] = 'text:display-xl';
                }
                $content = $mod['content'] ?? '';
                if ($content && !preg_match('/<h[1-6]\b/i', $content)) {
                    $mod['content'] = "<h1>" . strip_tags($content) . "</h1>";
                }
            } else {
                if ($is_dark) {
                    $new_presets[] = 'text:display-md-light';
                } else {
                    $new_presets[] = 'text:display-md';
                }
                $content = $mod['content'] ?? '';
                if ($content && !preg_match('/<h[1-6]\b/i', $content)) {
                    $mod['content'] = "<h2>" . strip_tags($content) . "</h2>";
                }
            }
            
            // Set headingFont override
            $mod['headingFont'] = [
                $level => [
                    'font' => [
                        'desktop' => [
                            'value' => [
                                'color' => $heading_color
                            ]
                        ]
                    ]
                ]
            ];
            // Clear bodyFont so it doesn't conflict
            if (isset($mod['bodyFont'])) {
                unset($mod['bodyFont']);
            }
        } elseif ($text_role === 'eyebrow') {
            if ($is_dark) {
                $new_presets[] = 'text:eyebrow-dark';
                $eyebrow_color = '{{design:color:sepia-300}}';
            } else {
                $new_presets[] = 'text:eyebrow';
                $eyebrow_color = '{{design:color:sepia-700}}';
            }
            
            // Set bodyFont override in correct nested structure
            $mod['bodyFont'] = [
                'body' => [
                    'font' => [
                        'desktop' => [
                            'value' => [
                                'color' => $eyebrow_color
                            ]
                        ]
                    ]
                ]
            ];
        } else {
            // Default text/description
            if ($is_dark) {
                $new_presets[] = 'text:lead';
                $body_color = '{{design:color:text-on-dark}}';
            } else {
                $new_presets[] = 'text:lead-dark';
                $body_color = '{{design:color:text-secondary}}';
            }
            
            // Set bodyFont override in correct nested structure
            $mod['bodyFont'] = [
                'body' => [
                    'font' => [
                        'desktop' => [
                            'value' => [
                                'color' => $body_color
                            ]
                        ]
                    ]
                ]
            ];
        }
        $mod['presets'] = array_unique($new_presets);
        
        if (isset($mod['decoration']['bodyFont'])) {
            unset($mod['decoration']['bodyFont']);
        }
    }

    // Enforce button styling
    if ($type === 'divi/button') {
        $existing_presets = $mod['presets'] ?? [];
        $new_presets = [];
        
        foreach ($existing_presets as $p) {
            if (!str_starts_with($p, 'module:')) {
                $new_presets[] = $p;
            }
        }
        
        if ($button_role === 'primary') {
            $new_presets[] = 'module:btn-primary';
        } else {
            if ($is_dark) {
                $new_presets[] = 'module:btn-outline-light';
            } else {
                $new_presets[] = 'module:btn-ghost';
            }
        }
        $mod['presets'] = array_unique($new_presets);
        
        // Strip any catalog decoration override
        if (isset($mod['decoration'])) {
            unset($mod['decoration']);
        }
    }
    
    // Enforce blurb/card styling
    if ($type === 'divi/blurb') {
        $existing_presets = $mod['presets'] ?? [];
        $new_presets = [];
        
        foreach ($existing_presets as $p) {
            if (!str_starts_with($p, 'module:') && !str_starts_with($p, 'transform:')) {
                $new_presets[] = $p;
            }
        }
        
        // Native color mode helper (light/dark text contrast class)
        $mod['advanced']['text']['text']['desktop']['value']['color'] = $is_dark ? 'light' : 'dark';
        
        if ($is_dark) {
            $new_presets[] = 'module:glass-card';
            $new_presets[] = 'transform:hover-lift';
            $heading_color = '{{design:color:parchment-50}}';
            $body_color = '{{design:color:text-on-dark}}';
        } else {
            $new_presets[] = 'module:feature-card';
            $new_presets[] = 'transform:hover-lift';
            $heading_color = '{{design:color:ink}}';
            $body_color = '{{design:color:text-secondary}}';
        }
        $mod['presets'] = array_unique($new_presets);
        
        $mod['headingFont'] = [
            'h4' => [
                'font' => [
                    'desktop' => [
                        'value' => [
                            'color' => $heading_color
                        ]
                    ]
                ]
            ]
        ];
        
        $mod['bodyFont'] = [
            'body' => [
                'font' => [
                    'desktop' => [
                        'value' => [
                            'color' => $body_color
                        ]
                    ]
                ]
            ]
        ];
        
        $mod['imageIcon']['advanced']['color']['desktop']['value'] = '{{design:color:accent}}';
    }
    
    // Recurse into columns/modules if nested structure exists (e.g. groups or rows)
    if (isset($mod['columns']) && is_array($mod['columns'])) {
        foreach ($mod['columns'] as &$col) {
            if (isset($col['modules']) && is_array($col['modules'])) {
                strip_placeholder_modules($col['modules']);
                foreach ($col['modules'] as &$m) {
                    correct_module_contrast($m, $is_dark, 'text', $section_type, 'primary');
                }
            }
        }
    }
    if (isset($mod['modules']) && is_array($mod['modules'])) {
        strip_placeholder_modules($mod['modules']);
        foreach ($mod['modules'] as &$m) {
            correct_module_contrast($m, $is_dark, 'text', $section_type, 'primary');
        }
    }
}

function process_sections(array &$sections, array $design_system, string $page_tone = 'editorial'): void {
    $content_section_count = 0;
    foreach ($sections as &$section) {
        $section_type = detect_section_type($section);
        if (in_array($section_type, ['features', 'content', 'content-list', 'testimonials', 'logos', 'about', 'team', 'gallery', 'faq', 'timeline'])) {
            $content_section_count++;
        }
        $section = inject_section_presets($section, $section_type, $content_section_count, $page_tone, $design_system);
        
        $is_dark = is_section_dark($section);
        
        // Strip catalog-specific layout background/spacing overrides
        $is_catalog = (isset($section['_template']) && str_starts_with($section['_template'], 'catalog/'));
        if ($is_catalog) {
            if (isset($section['decoration']['background'])) {
                unset($section['decoration']['background']);
                fwrite(STDERR, "[POSTC]  stripped catalog local background decoration\n");
            }
            if (isset($section['decoration']['spacing'])) {
                unset($section['decoration']['spacing']);
                fwrite(STDERR, "[POSTC]  stripped catalog local spacing decoration\n");
            }
        }
        
        if (isset($section['rows']) && is_array($section['rows'])) {
            foreach ($section['rows'] as &$row) {
                if (isset($row['columns']) && is_array($row['columns'])) {
                    foreach ($row['columns'] as &$col) {
                        if (isset($col['modules']) && is_array($col['modules'])) {
                            strip_placeholder_modules($col['modules']);
                            
                            $text_mods = [];
                            $button_mods = [];
                            $has_heading = false;
                            foreach ($col['modules'] as $idx => $m) {
                                $m_type = $m['type'] ?? '';
                                if ($m_type === 'divi/text') {
                                    $text_mods[] = $idx;
                                } elseif ($m_type === 'divi/button') {
                                    $button_mods[] = $idx;
                                } elseif ($m_type === 'divi/heading') {
                                    $has_heading = true;
                                }
                            }
                            
                            $num_text_mods = count($text_mods);
                            $num_button_mods = count($button_mods);
                            
                            foreach ($col['modules'] as $idx => &$mod) {
                                $text_role = 'text';
                                if (($mod['type'] ?? '') === 'divi/text') {
                                    $text_pos = array_search($idx, $text_mods);
                                    if ($has_heading) {
                                        if ($num_text_mods === 1) {
                                            $text_role = 'text';
                                        } else {
                                            $text_role = ($text_pos === 0) ? 'eyebrow' : 'text';
                                        }
                                    } else {
                                        if ($num_text_mods === 1) {
                                            $text_role = 'text';
                                        } elseif ($num_text_mods === 2) {
                                            $text_role = ($text_pos === 0) ? 'title' : 'text';
                                        } elseif ($num_text_mods >= 3) {
                                            if ($text_pos === 0) {
                                                $text_role = 'eyebrow';
                                            } elseif ($text_pos === 1) {
                                                $text_role = 'title';
                                            } else {
                                                $text_role = 'text';
                                            }
                                        }
                                    }
                                }
                                
                                $button_role = 'primary';
                                if (($mod['type'] ?? '') === 'divi/button') {
                                    $btn_pos = array_search($idx, $button_mods);
                                    $button_role = ($btn_pos === 0) ? 'primary' : 'secondary';
                                }
                                
                                correct_module_contrast($mod, $is_dark, $text_role, $section_type, $button_role);
                            }
                            unset($mod);
                        }
                    }
                }
            }
        }
    }
    unset($section, $row, $col, $mod);
}

// ─── CLI ───────────────────────────────────────────────────
$is_main = (php_sapi_name() === 'cli' && isset($argv[0]) && realpath($argv[0]) === realpath(__FILE__));
if ($is_main) {
    $opts = getopt('', ['def::', 'out::', 'help']);
    $def_file = $opts['def'] ?? null;

    if (isset($opts['help']) || !$def_file) {
        echo "Usage: php post_compose.php --def=slug.json [--out=output.json]\n\n";
        echo "  --def=<file>  Page-def file (in page-defs/ or full path)\n";
        echo "  --out=<file>  Output path (default: overwrites input)\n";
        exit(isset($opts['help']) ? 0 : 1);
    }

    if (!file_exists($def_file)) {
        $alt = DEFS_DIR . $DIR_SEP . $def_file;
        if (!file_exists($alt)) {
            $alt = DEFS_DIR . $DIR_SEP . $def_file . '.json';
        }
        if (file_exists($alt)) { $def_file = $alt; }
    }

    if (!file_exists($def_file)) {
        fwrite(STDERR, "[ERROR] Page-def not found: {$def_file}\n");
        exit(1);
    }

    $page_def = json_decode(file_get_contents($def_file), true);
    if (!$page_def) {
        fwrite(STDERR, "[ERROR] Invalid JSON in: {$def_file}\n");
        exit(1);
    }

    $design_system = load_json(DS_PATH);
    if (!$design_system) {
        fwrite(STDERR, "[WARN] Design system not found at: " . DS_PATH . "\n");
        $design_system = ['presets' => []];
    }

    echo "[POSTC] Post-composing: {$page_def['title']}\n";

    // Process
    $page_def = strip_demo_images($page_def);
    $sections = $page_def['sections'] ?? [];
    $page_tone = $page_def['tone'] ?? 'editorial';
    process_sections($sections, $design_system, $page_tone);
    $page_def['sections'] = $sections;

    // Write
    $out_file = $opts['out'] ?? $def_file;
    file_put_contents(
        $out_file,
        json_encode($page_def, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES)
    );
    echo "[POSTC] Written to: {$out_file}\n";
}
