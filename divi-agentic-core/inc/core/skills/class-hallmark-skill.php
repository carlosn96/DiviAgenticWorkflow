<?php

namespace DAC\Core\Skills;

use DAC\Core\Token_Registry;

class Hallmark_Skill implements Skill_Interface {

    public static function get_name(): string {
        return 'hallmark';
    }

    public static function get_description(): string {
        return 'Anti-AI-slop: variedad estructural, fuentes con intención, tipografía pura';
    }

    public static function validate(array $vars): array {
        $results = [];
        $fails   = 0;
        $warns   = 0;
        $passes  = 0;

        // ── 1. Al menos 2 fuentes definidas ──
        $display = $vars['font_display'] ?? null;
        $body    = $vars['font_body'] ?? null;
        $ui      = $vars['font_ui'] ?? null;

        $defined_fonts = array_filter([$display, $body, $ui]);
        $font_count    = count($defined_fonts);

        if ($font_count < 2) {
            $results[] = [
                'rule'    => 'hallmark:font-count',
                'status'  => 'fail',
                'message' => "Hallmark requiere ≥ 2 fuentes (display + body). Definidas: {$font_count}.",
            ];
            $fails++;
        } else {
            $results[] = [
                'rule'    => 'hallmark:font-count',
                'status'  => 'pass',
                'message' => "{$font_count} fuentes definidas. Ok.",
            ];
            $passes++;

            // ── 2. Display ≠ Body (no misma fuente) ──
            if ($display && $body) {
                $d_clean = trim($display, "'\" ");
                $b_clean = trim($body, "'\" ");
                if (strcasecmp($d_clean, $b_clean) === 0) {
                    $results[] = [
                        'rule'    => 'hallmark:font-distinct',
                        'status'  => 'fail',
                        'message' => "Display y body son la misma fuente: {$d_clean}. Hallmark exige distintas.",
                    ];
                    $fails++;
                } else {
                    $results[] = [
                        'rule'    => 'hallmark:font-distinct',
                        'status'  => 'pass',
                        'message' => "Display ({$d_clean}) ≠ Body ({$b_clean}). Ok.",
                    ];
                    $passes++;
                }
            }
        }

        // ── 3. Locked tokens: no hex null o vacío en required ──
        $required_colors = ['color_accent', 'color_surface_deep', 'color_text_primary', 'color_text_on_dark'];
        $missing_colors  = [];
        foreach ($required_colors as $key) {
            $val = $vars[$key] ?? null;
            if (!$val || !str_starts_with($val, '#')) {
                $missing_colors[] = $key;
            }
        }
        if (!empty($missing_colors)) {
            $results[] = [
                'rule'    => 'hallmark:locked-tokens',
                'status'  => 'fail',
                'message' => 'Tokens requeridos sin valor: ' . implode(', ', $missing_colors),
            ];
            $fails++;
        } else {
            $results[] = [
                'rule'    => 'hallmark:locked-tokens',
                'status'  => 'pass',
                'message' => 'Todos los tokens requeridos tienen valor.',
            ];
            $passes++;
        }

        // ── 4. Sin valores default placeholder ──
        $defaults_used = [];
        if (isset($vars['color_ink_soft']) && $vars['color_ink_soft'] === '#666666') {
            $defaults_used[] = 'color_ink_soft (#666666)';
        }
        if (isset($vars['color_surface_white']) && $vars['color_surface_white'] === '#ffffff') {
            $defaults_used[] = 'color_surface_white (#ffffff)';
        }
        if (!empty($defaults_used)) {
            $results[] = [
                'rule'    => 'hallmark:no-defaults',
                'status'  => 'warn',
                'message' => 'Valores default detectados: ' . implode(', ', $defaults_used) . '. Hallmark recomienda valores intencionales.',
            ];
            $warns++;
        } else {
            $results[] = [
                'rule'    => 'hallmark:no-defaults',
                'status'  => 'pass',
                'message' => 'No hay valores default placeholder.',
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
            'color_accent'           => '#DC2626',
            'color_accent_hover'     => '#B91C1C',
            'color_ink'              => '#FFFFFF',
            'color_ink_soft'         => '#A1A1AA',
            'color_surface_deep'     => '#18181B',
            'color_surface_mid'      => '#27272A',
            'color_surface_light'    => '#F4F4F5',
            'color_surface_white'    => '#FAFAFA',
            'color_text_primary'     => '#18181B',
            'color_text_secondary'   => '#52525B',
            'color_text_on_dark'     => '#F4F4F5',
            'color_success'          => '#22C55E',
            'color_error'            => '#EF4444',
            'font_display'           => 'DM Serif Display',
            'font_body'              => 'DM Sans',
            'font_body_size'         => '18px',
            'font_body_height'       => '1.6',
            'font_body_weight'       => '400',
            'font_heading_weight'    => '700',
            'font_heading_size_h1'   => '72px',
            'font_heading_size_h2'   => '48px',
            'font_heading_size_h3'   => '36px',
            'font_heading_size_h4'   => '28px',
            'font_heading_size_h5'   => '20px',
            'font_heading_size_h6'   => '16px',
            'radius_sm'              => '4px',
            'radius_md'              => '8px',
            'radius_lg'              => '12px',
            'radius_xl'              => '20px',
            'radius_full'            => '9999px',
            'space_xs'               => '4px',
            'space_sm'               => '8px',
            'space_md'               => '16px',
            'space_lg'               => '32px',
            'space_xl'               => '48px',
            'space_2xl'              => '80px',
            'space_3xl'              => '128px',
            'button_border_radius'   => '8px',
            'button_border_width'    => '1px',
            'button_font_size'       => '16px',
            'button_text_color'      => '#FAFAFA',
            'button_text_color_hover' => '#FAFAFA',
            'customizer_primary'     => 'accent',
            'customizer_secondary'   => 'accent',
            'customizer_heading'     => 'text_primary',
            'customizer_body'        => 'text_primary',
            'customizer_link'        => 'accent',
        ]);
    }
}
