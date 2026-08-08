<?php

namespace DAC\Core\Skills;

use DAC\Core\Token_Registry;

class High_End_Skill implements Skill_Interface {

    private const BANNED_FONTS = [
        'inter', 'roboto', 'arial', 'helvetica', 'open sans', 'times new roman',
    ];

    public static function get_name(): string {
        return 'high-end-visual-design';
    }

    public static function get_description(): string {
        return 'Diseño premium agencia: fuentes exclusivas, macro-whitespace, radios generosos';
    }

    public static function validate(array $vars): array {
        $results = [];
        $fails   = 0;
        $warns   = 0;
        $passes  = 0;

        // ── 1. Banned fonts ──
        $font_keys = ['font_display', 'font_body', 'font_ui'];
        $banned_found = [];

        foreach ($font_keys as $key) {
            $font = $vars[$key] ?? null;
            if (!$font) continue;
            $clean = strtolower(trim($font, "'\" "));

            foreach (self::BANNED_FONTS as $banned) {
                if (str_contains($clean, $banned)) {
                    $banned_found[] = "{$key}: {$font}";
                    break;
                }
            }
        }

        if (!empty($banned_found)) {
            $results[] = [
                'rule'    => 'high-end:banned-fonts',
                'status'  => 'fail',
                'message' => 'Fuentes prohibidas: ' . implode(', ', $banned_found) . '. High-end no permite Inter, Roboto, Arial, Helvetica, Open Sans.',
            ];
            $fails++;
        } else {
            $results[] = [
                'rule'    => 'high-end:banned-fonts',
                'status'  => 'pass',
                'message' => 'No hay fuentes prohibidas.',
            ];
            $passes++;
        }

        // ── 2. Macro-whitespace: space_2xl debe ser ≥ 64px ──
        $space_2xl = $vars['space_2xl'] ?? null;
        if ($space_2xl && preg_match('/^(\d+(?:\.\d+)?)px$/', $space_2xl, $m)) {
            $px = (float) $m[1];
            if ($px < 64) {
                $results[] = [
                    'rule'    => 'high-end:macro-whitespace',
                    'status'  => 'warn',
                    'message' => "space_2xl = {$px}px. High-end recomienda ≥ 64px para espaciado premium.",
                ];
                $warns++;
            } else {
                $results[] = [
                    'rule'    => 'high-end:macro-whitespace',
                    'status'  => 'pass',
                    'message' => "space_2xl = {$px}px, dentro del estándar premium.",
                ];
                $passes++;
            }
        }

        // ── 3. space_3xl debe ser ≥ 100px ──
        $space_3xl = $vars['space_3xl'] ?? null;
        if ($space_3xl && preg_match('/^(\d+(?:\.\d+)?)px$/', $space_3xl, $m)) {
            $px = (float) $m[1];
            if ($px < 100) {
                $results[] = [
                    'rule'    => 'high-end:max-whitespace',
                    'status'  => 'warn',
                    'message' => "space_3xl = {$px}px. High-end recomienda ≥ 100px para separaciones máximas.",
                ];
                $warns++;
            } else {
                $results[] = [
                    'rule'    => 'high-end:max-whitespace',
                    'status'  => 'pass',
                    'message' => "space_3xl = {$px}px, ok.",
                ];
                $passes++;
            }
        }

        // ── 4. Radios premium: radius_lg ≥ 16px ──
        $radius_lg = $vars['radius_lg'] ?? null;
        if ($radius_lg && preg_match('/^(\d+(?:\.\d+)?)px$/', $radius_lg, $m)) {
            $px = (float) $m[1];
            if ($px < 16) {
                $results[] = [
                    'rule'    => 'high-end:premium-radius',
                    'status'  => 'warn',
                    'message' => "radius_lg = {$px}px. High-end recomienda ≥ 16px para radio premium.",
                ];
                $warns++;
            } else {
                $results[] = [
                    'rule'    => 'high-end:premium-radius',
                    'status'  => 'pass',
                    'message' => "radius_lg = {$px}px, dentro del estándar premium.",
                ];
                $passes++;
            }
        }

        // ── 5. Font display debe ser premium (no generic) ──
        $display = $vars['font_display'] ?? '';
        $clean_display = strtolower(trim($display, "'\" "));
        $generic_terms = ['sans-serif', 'serif', 'system-ui', 'ui-sans-serif', 'ui-serif'];
        $is_generic = false;
        foreach ($generic_terms as $term) {
            if (str_contains($clean_display, $term)) {
                $is_generic = true;
                break;
            }
        }
        if ($is_generic) {
            $results[] = [
                'rule'    => 'high-end:display-font',
                'status'  => 'warn',
                'message' => "Font display ({$display}) es un fallback genérico. Una marca premium necesita una fuente con nombre.",
            ];
            $warns++;
        } elseif (!empty($display)) {
            $results[] = [
                'rule'    => 'high-end:display-font',
                'status'  => 'pass',
                'message' => "{$display} es una fuente con nombre, ok.",
            ];
            $passes++;
        }

        return [
            'checks'  => $results,
            'summary' => [
                'total' => count($results),
                'pass'  => $passes,
                'warn'  => $warns,
                'fail'  => $fails,
                'gate'  => $fails === 0,
            ],
        ];
    }

    public static function get_scaffold(): array {
        $base = Token_Registry::generate_scaffold();
        return array_merge($base, [
            'color_accent'           => '#7C3AED',
            'color_accent_hover'     => '#6D28D9',
            'color_ink'              => '#FFFFFF',
            'color_ink_soft'         => '#A1A1AA',
            'color_surface_deep'     => '#050505',
            'color_surface_mid'      => '#18181B',
            'color_surface_light'    => '#FAFAFA',
            'color_surface_white'    => '#FFFFFF',
            'color_text_primary'     => '#09090B',
            'color_text_secondary'   => '#71717A',
            'color_text_on_dark'     => '#F4F4F5',
            'color_success'          => '#22C55E',
            'color_error'            => '#EF4444',
            'font_display'           => 'Clash Display',
            'font_body'              => 'Plus Jakarta Sans',
            'font_body_size'         => '18px',
            'font_body_height'       => '1.7',
            'font_body_weight'       => '400',
            'font_heading_weight'    => '600',
            'font_heading_size_h1'   => '80px',
            'font_heading_size_h2'   => '56px',
            'font_heading_size_h3'   => '40px',
            'font_heading_size_h4'   => '32px',
            'font_heading_size_h5'   => '24px',
            'font_heading_size_h6'   => '18px',
            'radius_sm'              => '8px',
            'radius_md'              => '12px',
            'radius_lg'              => '20px',
            'radius_xl'              => '32px',
            'radius_full'            => '9999px',
            'space_xs'               => '8px',
            'space_sm'               => '16px',
            'space_md'               => '24px',
            'space_lg'               => '40px',
            'space_xl'               => '64px',
            'space_2xl'              => '96px',
            'space_3xl'              => '160px',
            'button_border_radius'   => '9999px',
            'button_border_width'    => '0',
            'button_font_size'       => '16px',
            'button_text_color'      => '#FFFFFF',
            'button_text_color_hover' => '#FFFFFF',
            'customizer_primary'     => 'accent',
            'customizer_secondary'   => 'accent',
            'customizer_heading'     => 'text_primary',
            'customizer_body'        => 'text_primary',
            'customizer_link'        => 'accent',
        ]);
    }
}
