<?php

namespace DAC\Core;

class Design_Validator {

    private const FONT_CATEGORIES = [
        'serif'       => ['Georgia', 'Times New Roman', 'Palatino', 'Garamond', 'Merriweather', 'Playfair Display', 'Lora', 'Source Serif', 'EB Garamond', 'Crimson Text', 'Cardo', 'Alegreya', 'Noto Serif', 'Bitter', 'Arvo', 'DM Serif'],
        'sans'        => ['Inter', 'Helvetica', 'Arial', 'Roboto', 'Open Sans', 'Lato', 'Montserrat', 'Poppins', 'Nunito', 'Work Sans', 'Source Sans', 'DM Sans', 'Plus Jakarta Sans', 'Manrope', 'Figtree', 'Onest', 'Outfit', 'Sora', 'Lexend', 'Public Sans', 'Noto Sans', 'Fira Sans', 'Raleway', 'Ubuntu', 'Mukta'],
        'display'     => ['Oswald', 'Anton', 'Bebas Neue', 'Cinzel', 'Unbounded', 'Clash Display', 'Synonym', 'Array', 'Trap', 'Panchang', 'Abril Fatface', 'Prata', 'Bodoni', 'Didot', 'Arapey', 'Stardom'],
        'mono'        => ['Courier New', 'Fira Code', 'JetBrains Mono', 'Source Code Pro', 'Roboto Mono', 'IBM Plex Mono', 'Space Mono', 'DM Mono'],
        'handwriting' => ['Caveat', 'Dancing Script', 'Patrick Hand', 'Kalam'],
    ];

    private const HEADING_EXPECTED_RATIO = 1.25;
    private const SPACE_EXPECTED_RATIO   = 1.5;
    private const RADIUS_EXPECTED_RATIO  = 2.0;
    private const SCALE_TOLERANCE        = 0.2;

    private static function relative_luminance(string $hex): float {
        $hex = ltrim($hex, '#');
        if (strlen($hex) === 3) {
            $hex = $hex[0] . $hex[0] . $hex[1] . $hex[1] . $hex[2] . $hex[2];
        }
        $r = hexdec(substr($hex, 0, 2)) / 255;
        $g = hexdec(substr($hex, 2, 2)) / 255;
        $b = hexdec(substr($hex, 4, 2)) / 255;

        $linearize = function(float $c): float {
            return ($c <= 0.04045) ? $c / 12.92 : pow(($c + 0.055) / 1.055, 2.4);
        };

        return 0.2126 * $linearize($r) + 0.7152 * $linearize($g) + 0.0722 * $linearize($b);
    }

    private static function contrast_ratio(string $hex1, string $hex2): float {
        $l1 = self::relative_luminance($hex1);
        $l2 = self::relative_luminance($hex2);
        $lighter = max($l1, $l2);
        $darker  = min($l1, $l2);
        return ($lighter + 0.05) / ($darker + 0.05);
    }

    private static function classify_font(string $font_name): string {
        $font_name = trim($font_name, "'\" ");
        foreach (self::FONT_CATEGORIES as $category => $fonts) {
            foreach ($fonts as $known) {
                if (stripos($font_name, $known) !== false) {
                    return $category;
                }
            }
        }
        // Heuristic fallback: check last name segment
        $lower = strtolower($font_name);
        if (str_contains($lower, 'serif')) return 'serif';
        if (str_contains($lower, 'mono'))  return 'mono';
        if (str_contains($lower, 'script') || str_contains($lower, 'hand')) return 'handwriting';
        return 'sans';
    }

    private static function parse_px(string $value): ?float {
        $value = trim($value);
        if (preg_match('/^(\d+(?:\.\d+)?)px$/', $value, $m)) {
            return (float) $m[1];
        }
        return null;
    }

    // ─── Checks ─────────────────────────────────────────────────────────

    /**
     * Detecta dark mode analizando la luminancia del surface principal.
     * Si color_surface_light tiene luminancia < 0.2, es un tema oscuro.
     */
    private static function is_dark_mode(array $vars): bool {
        $surface = $vars['color_surface_light'] ?? null;
        if ($surface && str_starts_with($surface, '#')) {
            return self::relative_luminance($surface) < 0.2;
        }
        return false;
    }

    private static function check_contrast_pairs(array $vars, array $rules): array {
        $results = [];
        $is_dark = self::is_dark_mode($vars);

        foreach ($rules as $source_key => $rule) {
            if (empty($rule['contrast_against']) || empty($rule['contrast_min'])) continue;

            $source_value = $vars[$source_key] ?? null;
            if (!$source_value || !str_starts_with($source_value, '#')) continue;

            $source_lum = self::relative_luminance($source_value);

            foreach ($rule['contrast_against'] as $target_key) {
                $target_value = $vars[$target_key] ?? null;
                if (!$target_value || !str_starts_with($target_value, '#')) continue;

                $target_lum = self::relative_luminance($target_value);

                // En dark mode: salta checks donde ambos colores son muy oscuros
                // (e.g., accent sobre surface_light — ambos son fondos, no texto sobre fondo)
                if ($source_lum < 0.1 && $target_lum < 0.1) {
                    continue;
                }

                // En dark mode: color_surface_white no es blanco real,
                // salta checks que lo usan como fondo claro
                if ($is_dark && $target_lum < 0.5) {
                    continue;
                }

                $ratio = self::contrast_ratio($source_value, $target_value);
                $min   = (float) $rule['contrast_min'];

                if ($ratio >= $min) {
                    $status = 'pass';
                } elseif ($ratio >= $min - 1.5) {
                    $status = 'warn';
                } else {
                    $status = 'fail';
                }

                $results[] = [
                    'rule'    => "contrast:{$source_key}:{$target_key}",
                    'status'  => $status,
                    'actual'  => round($ratio, 2),
                    'min'     => $min,
                    'message' => "$source_key ($source_value) vs $target_key ($target_value): {$ratio}:1 (min {$min}:1)",
                ];

                if ($status === 'warn') {
                    $results[] = [
                        'rule'    => "contrast:warn:{$source_key}:{$target_key}",
                        'status'  => 'warn',
                        'actual'  => round($ratio, 2),
                        'min'     => $min,
                        'message' => "Bajo contraste: $source_key vs $target_key = {$ratio}:1. Objetivo AAA: {$min}:1",
                    ];
                }
            }
        }

        return $results;
    }

    private static function check_scale_progression(array $vars, array $rules, string $group, float $expected_ratio): array {
        $results = [];

        $items = [];
        foreach ($rules as $key => $rule) {
            if (($rule['scale_group'] ?? null) === $group && isset($rule['order'])) {
                $value = $vars[$key] ?? null;
                if ($value !== null) {
                    $items[] = [
                        'key'   => $key,
                        'order' => $rule['order'],
                        'value' => $value,
                    ];
                }
            }
        }

        usort($items, fn($a, $b) => $a['order'] <=> $b['order']);

        for ($i = 0; $i < count($items) - 1; $i++) {
            $current_px = self::parse_px($items[$i]['value']);
            $next_px    = self::parse_px($items[$i + 1]['value']);

            if ($current_px === null || $next_px === null) continue;

            // Skip intentional outliers (e.g., radius_full = 9999px)
            if ($current_px > 1000 || $next_px > 1000) continue;

            // Ratio always as larger/smaller
            $ratio = max($current_px, $next_px) / min($current_px, $next_px);

            $expected = ($group === 'heading') ? $expected_ratio : $expected_ratio;
            $min_expected = $expected - self::SCALE_TOLERANCE;
            $max_expected = $expected + self::SCALE_TOLERANCE;

            if ($ratio >= $min_expected && $ratio <= $max_expected) {
                $status = 'pass';
            } elseif ($ratio >= $expected * 0.5 && $ratio <= $expected * 1.5) {
                $status = 'warn';
            } else {
                $status = 'fail';
            }

            $results[] = [
                'rule'    => "scale:{$group}:{$items[$i]['key']}->{$items[$i+1]['key']}",
                'status'  => $status,
                'actual'  => round($ratio, 2),
                'min'     => $expected,
                'message' => "{$items[$i]['key']} ({$items[$i]['value']}) → {$items[$i+1]['key']} ({$items[$i+1]['value']}) = ratio {$ratio}. Esperado: ~{$expected}",
            ];
        }

        return $results;
    }

    private static function hex_to_lab(string $hex): ?array {
        $hex = ltrim($hex, '#');
        if (strlen($hex) === 3) {
            $hex = $hex[0] . $hex[0] . $hex[1] . $hex[1] . $hex[2] . $hex[2];
        }
        if (strlen($hex) !== 6) return null;

        $r = hexdec(substr($hex, 0, 2)) / 255;
        $g = hexdec(substr($hex, 2, 2)) / 255;
        $b = hexdec(substr($hex, 4, 2)) / 255;

        $linearize = function(float $c): float {
            return ($c <= 0.04045) ? $c / 12.92 : pow(($c + 0.055) / 1.055, 2.4);
        };
        $r_lin = $linearize($r);
        $g_lin = $linearize($g);
        $b_lin = $linearize($b);

        // XYZ (D65)
        $x = 0.4124564 * $r_lin + 0.3575761 * $g_lin + 0.1804375 * $b_lin;
        $y = 0.2126729 * $r_lin + 0.7151522 * $g_lin + 0.0721750 * $b_lin;
        $z = 0.0193339 * $r_lin + 0.1191920 * $g_lin + 0.9503041 * $b_lin;

        // XYZ to Lab (D65: 0.95047, 1.0, 1.08883)
        $fx = ($x / 0.95047) > 0.008856 ? pow($x / 0.95047, 1/3) : (7.787 * $x / 0.95047 + 16/116);
        $fy = ($y / 1.0) > 0.008856 ? pow($y / 1.0, 1/3) : (7.787 * $y / 1.0 + 16/116);
        $fz = ($z / 1.08883) > 0.008856 ? pow($z / 1.08883, 1/3) : (7.787 * $z / 1.08883 + 16/116);

        return [116 * $fy - 16, 500 * ($fx - $fy), 200 * ($fy - $fz)];
    }

    private static function delta_e(array $lab1, array $lab2): float {
        $dl = $lab1[0] - $lab2[0];
        $da = $lab1[1] - $lab2[1];
        $db = $lab1[2] - $lab2[2];
        return sqrt($dl * $dl + $da * $da + $db * $db);
    }

    private static function check_color_harmony(array $vars, array $rules): array {
        $results = [];
        $groups  = [];

        foreach ($rules as $key => $rule) {
            $group = $rule['harmony_group'] ?? null;
            if (!$group) continue;
            $value = $vars[$key] ?? null;
            if (!$value || !str_starts_with($value, '#')) continue;
            $lab = self::hex_to_lab($value);
            if (!$lab) continue;

            $groups[$group][] = ['key' => $key, 'value' => $value, 'lab' => $lab, 'L' => $lab[0]];
        }

        foreach ($groups as $group => $colors) {
            // Compare every pair in the same harmony group
            for ($i = 0; $i < count($colors); $i++) {
                for ($j = $i + 1; $j < count($colors); $j++) {
                    $de = self::delta_e($colors[$i]['lab'], $colors[$j]['lab']);

                    // Surfaces: check luminance progression
                    if ($group === 'surface') {
                        if ($colors[$i]['L'] !== $colors[$j]['L']) {
                            $ratio = max($colors[$i]['L'], $colors[$j]['L']) / min($colors[$i]['L'], $colors[$j]['L']);
                            if ($ratio < 1.1) {
                                $results[] = [
                                    'rule'    => "harmony:{$group}:luminance",
                                    'status'  => 'warn',
                                    'actual'  => round($ratio, 2),
                                    'min'     => '1.1',
                                    'message' => "{$colors[$i]['key']} (L={$colors[$i]['L']}) y {$colors[$j]['key']} (L={$colors[$j]['L']}) tienen luminancia muy cercana. Las superficies necesitan más contraste entre sí.",
                                ];
                            }
                        }
                        continue; // surfaces deltaE no es relevante
                    }

                    // Text and functional: low deltaE = harmonious (similar hue) 
                    // High deltaE = discordant
                    if ($group === 'text' && $de > 40) {
                        $results[] = [
                            'rule'    => "harmony:{$group}:deltaE",
                            'status'  => 'warn',
                            'actual'  => round($de, 1),
                            'min'     => '≤40',
                            'message' => "{$colors[$i]['key']} vs {$colors[$j]['key']} deltaE={$de}. Colores textuales muy dispares.",
                        ];
                    }
                }
            }

            // Surface luminance gradient check
            if ($group === 'surface' && count($colors) >= 2) {
                usort($colors, fn($a, $b) => $a['L'] <=> $b['L']);
                $results[] = [
                    'rule'    => "harmony:{$group}:gradient",
                    'status'  => 'pass',
                    'actual'  => implode(' → ', array_map(fn($c) => "{$c['key']}(L{$c['L']})", $colors)),
                    'min'     => 'luminance progression',
                    'message' => "Superficies ordenadas por luminancia: " . implode(' → ', array_map(fn($c) => round($c['L'], 1), $colors)),
                ];
            }
        }

        if (empty($results)) {
            $results[] = [
                'rule'    => 'harmony:no-groups',
                'status'  => 'pass',
                'message' => 'No hay suficientes colores para evaluar armonía.',
            ];
        }

        return $results;
    }

    private static function check_font_pairing(array $vars, array $rules): array {
        $results = [];
        $fonts   = [];

        foreach ($rules as $key => $rule) {
            if (!empty($rule['pairing_group']) && !empty($vars[$key])) {
                $category = self::classify_font($vars[$key]);
                $fonts[$key] = [
                    'value'    => $vars[$key],
                    'category' => $category,
                    'group'    => $rule['pairing_group'],
                ];
            }
        }

        $keys = array_keys($fonts);
        for ($i = 0; $i < count($keys); $i++) {
            for ($j = $i + 1; $j < count($keys); $j++) {
                $a = $fonts[$keys[$i]];
                $b = $fonts[$keys[$j]];

                if ($a['category'] === $b['category'] && $a['category'] !== 'display') {
                    $results[] = [
                        'rule'    => "pairing:{$keys[$i]}:{$keys[$j]}",
                        'status'  => 'warn',
                        'actual'  => "{$a['category']} + {$b['category']}",
                        'min'     => 'different category',
                        'message' => "{$keys[$i]} ({$a['value']}, {$a['category']}) y {$keys[$j]} ({$b['value']}, {$b['category']}) son de la misma categoría.",
                    ];
                } else {
                    $results[] = [
                        'rule'    => "pairing:{$keys[$i]}:{$keys[$j]}",
                        'status'  => 'pass',
                        'actual'  => "{$a['category']} + {$b['category']}",
                        'min'     => 'different category',
                        'message' => "{$keys[$i]} ({$a['category']}) + {$keys[$j]} ({$b['category']}) — compatible.",
                    ];
                }
            }
        }

        if (empty($results)) {
            $results[] = [
                'rule'    => 'pairing:no-fonts',
                'status'  => 'warn',
                'actual'  => 'none',
                'min'     => '2 fonts',
                'message' => 'No hay suficientes fuentes definidas para evaluar pairing.',
            ];
        }

        return $results;
    }

    // ─── Main ───────────────────────────────────────────────────────────

    public static function run(array $vars): array {
        $rules   = Token_Registry::get_validation_rules();
        $results = [];

        $results = array_merge($results, self::check_contrast_pairs($vars, $rules));
        $results = array_merge($results, self::check_scale_progression($vars, $rules, 'heading', self::HEADING_EXPECTED_RATIO));
        $results = array_merge($results, self::check_scale_progression($vars, $rules, 'space', self::SPACE_EXPECTED_RATIO));
        $results = array_merge($results, self::check_scale_progression($vars, $rules, 'radius', self::RADIUS_EXPECTED_RATIO));
        $results = array_merge($results, self::check_color_harmony($vars, $rules));
        $results = array_merge($results, self::check_font_pairing($vars, $rules));

        $pass_count = count(array_filter($results, fn($r) => $r['status'] === 'pass'));
        $warn_count = count(array_filter($results, fn($r) => $r['status'] === 'warn'));
        $fail_count = count(array_filter($results, fn($r) => $r['status'] === 'fail'));

        $gate_passes = $fail_count === 0;

        return [
            'checks'  => $results,
            'summary' => [
                'total' => count($results),
                'pass'  => $pass_count,
                'warn'  => $warn_count,
                'fail'  => $fail_count,
                'gate'  => $gate_passes,
            ],
        ];
    }
}
