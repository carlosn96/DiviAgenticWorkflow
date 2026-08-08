<?php

namespace DAC\Core\Skills;

use DAC\Core\Token_Registry;

class Impeccable_Skill implements Skill_Interface {

    private const CREAM_CHROMA_MAX  = 0.06;
    private const CREAM_HUE_MIN     = 40;
    private const CREAM_HUE_MAX     = 100;
    private const CREAM_L_MIN       = 0.84;
    private const CREAM_L_MAX       = 0.97;

    public static function get_name(): string {
        return 'impeccable';
    }

    public static function get_description(): string {
        return 'UX de calidad: contraste tipográfico, color estratégico, escalas armónicas';
    }

    public static function validate(array $vars): array {
        $results = [];
        $fails   = 0;
        $warns   = 0;
        $passes  = 0;

        // ── 1. Heading hero máximo 96px ──
        $h1 = $vars['font_heading_size_h1'] ?? null;
        if ($h1 && preg_match('/^(\d+(?:\.\d+)?)px$/', $h1, $m)) {
            $px = (float) $m[1];
            if ($px > 96) {
                $results[] = [
                    'rule'    => 'impeccable:heading-max',
                    'status'  => 'fail',
                    'message' => "H1 es {$px}px, excede el máximo de 96px de impeccable.",
                ];
                $fails++;
            } elseif ($px > 80) {
                $results[] = [
                    'rule'    => 'impeccable:heading-max',
                    'status'  => 'warn',
                    'message' => "H1 es {$px}px, cerca del límite. Impeccable recomienda ≤ 96px.",
                ];
                $warns++;
            } else {
                $results[] = [
                    'rule'    => 'impeccable:heading-max',
                    'status'  => 'pass',
                    'message' => "H1 = {$px}px, dentro del límite.",
                ];
                $passes++;
            }
        }

        // ── 2. Color surface light no debe ser cream/sand/beige default ──
        $surface_light = $vars['color_surface_light'] ?? null;
        if ($surface_light && str_starts_with($surface_light, '#')) {
            $is_warm = self::is_warm_neutral($surface_light);
            if ($is_warm) {
                $results[] = [
                    'rule'    => 'impeccable:no-cream-bg',
                    'status'  => 'warn',
                    'message' => "{$surface_light} está en el rango cream/sand AI default. Impeccable recomienda evitar este tono como body bg.",
                ];
                $warns++;
            } else {
                $results[] = [
                    'rule'    => 'impeccable:no-cream-bg',
                    'status'  => 'pass',
                    'message' => "{$surface_light} no es un warm neutral default.",
                ];
                $passes++;
            }
        }

        // ── 3. No gradientes en botones (sin sentido en vars, pero checkeable por el valor) ──
        // No aplica a _design_vars.json directamente, se salta.

        // ── 4. body_size ≥ 16px en mobile (check valor numérico) ──
        $body_size = $vars['font_body_size'] ?? null;
        if ($body_size && preg_match('/^(\d+(?:\.\d+)?)px$/', $body_size, $m)) {
            $px = (float) $m[1];
            if ($px < 16) {
                $results[] = [
                    'rule'    => 'impeccable:body-size-min',
                    'status'  => 'fail',
                    'message' => "Body font size es {$px}px. Impeccable exige ≥ 16px en mobile.",
                ];
                $fails++;
            } else {
                $results[] = [
                    'rule'    => 'impeccable:body-size-min',
                    'status'  => 'pass',
                    'message' => "Body font size = {$px}px, ok.",
                ];
                $passes++;
            }
        }

        // ── 5. heading display letter-spacing no menor a -0.04em ──
        // No hay un token directo para letter-spacing en los vars, así que se omite.

        // ── 6. body line length 65-75ch ──
        // No aplica a _design_vars.json (es page-level)

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
            'color_accent'           => '#2563EB',
            'color_accent_hover'     => '#1D4ED8',
            'color_ink'              => '#FFFFFF',
            'color_ink_soft'         => '#94A3B8',
            'color_surface_deep'     => '#0F172A',
            'color_surface_mid'      => '#1E293B',
            'color_surface_light'    => '#F8FAFC',
            'color_surface_white'    => '#FFFFFF',
            'color_text_primary'     => '#0F172A',
            'color_text_secondary'   => '#475569',
            'color_text_on_dark'     => '#F1F5F9',
            'color_success'          => '#10B981',
            'color_error'            => '#EF4444',
            'font_display'           => 'Unbounded',
            'font_body'              => 'Source Serif',
            'font_ui'                => 'DM Sans',
            'font_body_size'         => '16px',
            'font_body_height'       => '1.7',
            'font_body_weight'       => '400',
            'font_heading_weight'    => '700',
            'font_heading_size_h1'   => '56px',
            'font_heading_size_h2'   => '40px',
            'font_heading_size_h3'   => '32px',
            'font_heading_size_h4'   => '24px',
            'font_heading_size_h5'   => '20px',
            'font_heading_size_h6'   => '16px',
            'radius_sm'              => '2px',
            'radius_md'              => '4px',
            'radius_lg'              => '8px',
            'radius_xl'              => '12px',
            'radius_full'            => '9999px',
            'space_xs'               => '4px',
            'space_sm'               => '8px',
            'space_md'               => '16px',
            'space_lg'               => '24px',
            'space_xl'               => '40px',
            'space_2xl'              => '64px',
            'space_3xl'              => '96px',
            'button_border_radius'   => '6px',
            'button_border_width'    => '0',
            'button_font_size'       => '16px',
            'button_text_color'      => '#FFFFFF',
            'button_text_color_hover' => '#E2E8F0',
            'customizer_primary'     => 'accent',
            'customizer_secondary'   => 'accent',
            'customizer_heading'     => 'text_primary',
            'customizer_body'        => 'text_primary',
            'customizer_link'        => 'accent',
        ]);
    }

    /**
     * Detecta si un hex está en el rango warm-neutral AI-default
     * usando una aproximación simple de CIELCH.
     */
    private static function is_warm_neutral(string $hex): bool {
        $hex = ltrim($hex, '#');
        if (strlen($hex) === 3) {
            $hex = $hex[0] . $hex[0] . $hex[1] . $hex[1] . $hex[2] . $hex[2];
        }
        $r = hexdec(substr($hex, 0, 2)) / 255;
        $g = hexdec(substr($hex, 2, 2)) / 255;
        $b = hexdec(substr($hex, 4, 2)) / 255;

        // sRGB to linear
        $linearize = function(float $c): float {
            return ($c <= 0.04045) ? $c / 12.92 : pow(($c + 0.055) / 1.055, 2.4);
        };
        $r_lin = $linearize($r);
        $g_lin = $linearize($g);
        $b_lin = $linearize($b);

        // Relative luminance
        $Y = 0.2126 * $r_lin + 0.7152 * $g_lin + 0.0722 * $b_lin;
        if ($Y < 0.18 || $Y > 0.9) return false; // fuera del rango de luminosidad cream

        // XYZ values (D65)
        $x = 0.4124564 * $r_lin + 0.3575761 * $g_lin + 0.1804375 * $b_lin;
        $y = 0.2126729 * $r_lin + 0.7151522 * $g_lin + 0.0721750 * $b_lin;
        $z = 0.0193339 * $r_lin + 0.1191920 * $g_lin + 0.9503041 * $b_lin;

        // XYZ to Lab (D65 reference: 0.95047, 1.0, 1.08883)
        $fx = ($x / 0.95047) > 0.008856 ? pow($x / 0.95047, 1/3) : (7.787 * $x / 0.95047 + 16/116);
        $fy = ($y / 1.0) > 0.008856 ? pow($y / 1.0, 1/3) : (7.787 * $y / 1.0 + 16/116);
        $fz = ($z / 1.08883) > 0.008856 ? pow($z / 1.08883, 1/3) : (7.787 * $z / 1.08883 + 16/116);

        $L = 116 * $fy - 16;
        $a = 500 * ($fx - $fy);
        $b = 200 * ($fy - $fz);
        $C = sqrt($a * $a + $b * $b);
        $h = atan2($b, $a) * 180 / M_PI;
        if ($h < 0) $h += 360;

        return (
            $L >= self::CREAM_L_MIN && $L <= self::CREAM_L_MAX &&
            $C < self::CREAM_CHROMA_MAX &&
            $h >= self::CREAM_HUE_MIN && $h <= self::CREAM_HUE_MAX
        );
    }
}
