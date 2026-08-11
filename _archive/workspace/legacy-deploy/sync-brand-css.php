<?php
/**
 * Sync brand to WordPress — single source, single execution.
 * Reads _design_vars.json, generates everything, updates WordPress.
 * Usage: wp eval-file DAW_bundle/workspace/sync-brand-css.php
 */

$root = dirname(__DIR__, 2);
$site = getenv('DAW_SITE') ?: 'lopezvelarde';
$vars_path = $root . '/DAW_bundle/site/' . $site . '/brand/_design_vars.json';

if (!file_exists($vars_path)) {
    echo "ERROR: _design_vars.json not found at $vars_path\n";
    exit(1);
}

$vars = json_decode(file_get_contents($vars_path), true);
if (!$vars) {
    echo "ERROR: invalid JSON in _design_vars.json\n";
    exit(1);
}

echo "Reading: $vars_path\n";

// ── Extract values ──
$heading_font_raw = $vars['font_display'] ?? "'Inter', sans-serif";
$body_font_raw    = $vars['font_body'] ?? "'Inter', sans-serif";
preg_match("/'([^']+)'/", $heading_font_raw, $m);
$heading_font = $m[1] ?? 'Inter';
preg_match("/'([^']+)'/", $body_font_raw, $m);
$body_font = $m[1] ?? 'Inter';

$heading_font_weight = $vars['font_display_weight'] ?? '700';
$body_font_weight    = $vars['font_body_weight'] ?? '500';

$colors = [
    'accent'         => $vars['color_accent'] ?? '#e50914',
    'surface-deep'   => $vars['color_surface_deep'] ?? '#000000',
    'surface-mid'    => $vars['color_surface_mid'] ?? '#0f0f0f',
    'surface-light'  => $vars['color_surface_light'] ?? '#232323',
    'text-primary'   => $vars['color_text_primary'] ?? '#ffffff',
    'text-secondary' => $vars['color_text_secondary'] ?? '#b3b3b3',
    'text-on-dark'   => $vars['color_text_on_dark'] ?? '#ffffff',
];

$btn_radius = $vars['radius_md'] ?? '8px';

echo "Fonts: heading=$heading_font, body=$body_font\n";

// ── Update Divi Theme Options (via direct DB) ──
global $wpdb;
$raw = $wpdb->get_var("SELECT option_value FROM {$wpdb->options} WHERE option_name = 'et_divi'");
$opts = is_string($raw) ? maybe_unserialize($raw) : [];
if (!is_array($opts)) $opts = [];

$changed = 0;

// Map _design_vars.json color keys to Divi option keys
$accent = $colors['accent'];
$text_primary = $colors['text-primary'];
$surface_deep = $colors['surface-deep'];
$surface_mid = $colors['surface-mid'];

$divi_map = [
    'heading_font'                 => $heading_font,
    'heading_font_weight'          => $heading_font_weight,
    'body_font'                    => $body_font,
    'body_font_weight'             => $body_font_weight,
    'divi_google_fonts_inline'     => 'on',
    'accent_color'                 => $accent,
    'secondary_accent_color'       => $accent,
    'font_color'                   => $text_primary,
    'header_color'                 => $text_primary,
    'link_color'                   => $accent,
    'all_buttons_font'              => 'none',
    'all_buttons_bg_color'          => $accent,
    'all_buttons_bg_color_hover'    => '#b20710',
    'all_buttons_text_color'        => '#ffffff',
    'all_buttons_text_color_hover'  => '#ffffff',
    'all_buttons_border_radius'     => str_replace('px', '', $btn_radius),
    'all_buttons_border_radius_hover' => str_replace('px', '', $btn_radius),
    'all_buttons_border_width'      => '0',
    'all_buttons_spacing'           => '2',
    'all_buttons_font_size'         => '20',
    'all_buttons_font_style'        => 'bold',
    'all_buttons_icon'              => 'yes',
    'all_buttons_icon_color'        => '#ffffff',
    'all_buttons_selected_icon'     => '5',
    'all_buttons_icon_placement'    => 'right',
    'all_buttons_icon_hover'        => 'yes',
    'primary_nav_bg'               => $surface_deep,
    'menu_link'                    => $text_primary,
    'menu_link_active'             => $accent,
    'primary_nav_text_color'       => $text_primary,
    'secondary_nav_bg'             => $surface_mid,
    'secondary_nav_text_color'     => $text_primary,
    'footer_bg'                    => $surface_deep,
    'footer_widget_text_color'     => $colors['text-secondary'],
    'footer_widget_link_color'     => $accent,
    'footer_widget_header_color'   => $text_primary,
];

// Apply map values
foreach ($divi_map as $key => $value) {
    if (($opts[$key] ?? '') !== $value) {
        $opts[$key] = $value;
        $changed++;
    }
}

// Clean stale keys — hover border keys should NOT be set (no border on hover since border_width=0)
$stale_keys = [
    'all_buttons_border_color_hover',
    'all_buttons_border_color',
];
foreach ($stale_keys as $sk) {
    if (isset($opts[$sk])) {
        unset($opts[$sk]);
        $changed++;
        echo "Removed stale key: $sk\n";
    }
}

if (!empty($opts['divi_custom_css'])) { unset($opts['divi_custom_css']); echo "Cleaned legacy divi_custom_css\n"; }

if ($changed > 0) {
    $wpdb->update($wpdb->options, ['option_value' => maybe_serialize($opts)], ['option_name' => 'et_divi']);
    wp_cache_delete('et_divi', 'options');
    echo "Divi options updated ($changed changes)\n";
} else {
    echo "Divi options up-to-date\n";
}

// ── Generate brand.css from _design_vars.json components ──
$components = $vars['components'] ?? [];
$font_map = ['display' => $heading_font_raw, 'body' => $body_font_raw];

$css = "/* Auto-generated Brand CSS — DAW Pipeline */\n";
$css .= ":root {\n";
foreach ($colors as $k => $v) {
    $css .= "  --daw-color-{$k}: {$v};\n";
}

$css .= "  --daw-radius: {$btn_radius};\n";
$css .= "}\n\n";

foreach ($components as $class => $def) {
    $scope = $def['scope'] ?? '';
    $prefix = $scope ? "{$scope} " : '';
    $sel = "{$prefix}.{$class}";
    $hover = $def['hover'] ?? null;

    switch ($def['type']) {
        case 'typography':
            $props = [];
            if (isset($def['font'])) {
                $var = $def['font'] === 'display' ? 'et_global_heading_font' : 'et_global_body_font';
                $fallback = $font_map[$def['font']] ?? 'sans-serif';
                $props[] = "font-family: var(--{$var}, {$fallback})";
            }
            if (isset($def['size'])) $props[] = "font-size: {$def['size']}";
            if (isset($def['weight'])) $props[] = "font-weight: {$def['weight']}";
            if (isset($def['lineHeight'])) $props[] = "line-height: {$def['lineHeight']}";
            if (isset($def['letterSpacing'])) $props[] = "letter-spacing: {$def['letterSpacing']}";
            if (isset($def['transform'])) $props[] = "text-transform: {$def['transform']}";
            if (isset($def['maxWidth'])) $props[] = "max-width: {$def['maxWidth']}";
            if (isset($def['color'])) {
                $cv = $def['color'];
                $props[] = "color: " . (strpos($cv, '#') === 0 ? $cv : "var(--daw-color-{$cv})");
            }
            $css .= "{$sel} { " . implode('; ', $props) . "; }\n";
            break;

        case 'section':
            $props = [];
            if (isset($def['color'])) $props[] = "color: var(--daw-color-{$def['color']})";
            if (isset($def['background'])) $props[] = "background: var(--daw-color-{$def['background']})";
            if ($props) $css .= "{$sel} { " . implode('; ', $props) . "; }\n";
            break;

        case 'button':
            $props = [];
            $bg = $def['background'] ?? '';
            $props[] = "background: " . (strpos($bg, '#') === 0 ? $bg : "var(--daw-color-{$bg})") . " !important";
            $c = $def['color'] ?? '#ffffff';
            $props[] = "color: {$c} !important";
            if (isset($def['border'])) $props[] = "border: 1px solid {$def['border']} !important";
            else $props[] = "border: none !important";
            $r_key = $def['radius'] ?? 'md';
            $r_val = $vars["radius_{$r_key}"] ?? '8px';
            $props[] = "border-radius: {$r_val} !important";
            if (isset($def['padding'])) $props[] = "padding: {$def['padding']} !important";
            if (isset($def['weight'])) $props[] = "font-weight: {$def['weight']} !important";
            if (isset($def['size'])) $props[] = "font-size: {$def['size']} !important";
            $props[] = "transition: all 0.2s ease !important";
            $css .= "{$sel} { " . implode('; ', $props) . "; }\n";

            if ($hover) {
                $hp = [];
                if (isset($hover['background'])) $hp[] = "background: var(--daw-color-{$hover['background']}) !important";
                if (isset($hover['borderColor'])) $hp[] = "border-color: {$hover['borderColor']} !important";
                if (isset($hover['color'])) $hp[] = "color: {$hover['color']} !important";
                if (isset($hover['background']) && strpos($hover['background'], '#') === 0) $hp[] = "background: {$hover['background']} !important";
                if ($hp) $css .= "{$sel}:hover { " . implode('; ', $hp) . "; }\n";
            }
            break;

        case 'card':
            $bg = $def['background'] ?? 'surface-light';
            $r_key = $def['radius'] ?? 'md';
            $r_val = $vars["radius_{$r_key}"] ?? '8px';
            $css .= "{$sel} { background: var(--daw-color-{$bg}); border-radius: {$r_val}; transition: transform 0.35s ease, box-shadow 0.35s ease; }\n";
            if (isset($def['hover'])) {
                $css .= "{$sel}:hover { transform: {$def['hover']}; box-shadow: 0 16px 40px rgba(0,0,0,0.3); }\n";
            }
            break;

        case 'animation':
            $anim = $def['animation'] ?? 'dawFadeUp';
            $dur = $def['duration'] ?? '0.6s';
            $delay = $def['delay'] ?? '0s';
            $css .= "{$sel} { animation: {$anim} {$dur} cubic-bezier(0,0,0.2,1) {$delay} both; }\n";
            break;

        case 'utility':
            if (isset($def['css'])) {
                $css .= "{$sel} { {$def['css']} }\n";
            }
            break;

        case 'custom':
            if (isset($def['css'])) {
                $css .= str_replace('{selector}', $sel, $def['css']) . "\n";
            }
            break;
    }
}

// Eyebrow modifiers for section labels
$css .= ".daw-eyebrow--light { color: {$accent}; }\n";
$css .= ".daw-eyebrow--dark { color: rgba(255,255,255,0.55); letter-spacing: 0.12em; }\n";

// Divi native overrides (not exposed as theme options)
$css .= "body:not(.et-fb) a { color: {$accent}; }\n";
$css .= "body:not(.et-fb) .et_pb_menu .et-menu-nav li.current-menu-item a { border-top-color: {$accent} !important; }\n";
$css .= "body:not(.et-fb) .et_pb_menu .et-menu-nav li.current-menu-ancestor a { border-top-color: {$accent} !important; }\n";
$css .= "body:not(.et-fb) .et_pb_menu .et-menu-nav li a:hover { border-top-color: {$accent} !important; }\n";
$css .= "body:not(.et-fb) #top-menu li a:hover { color: {$accent} !important; }\n";
$css .= "body:not(.et-fb) .nav li ul { border-top-color: {$accent} !important; border-color: {$accent} !important; }\n";
$css .= "body:not(.et-fb) .et_mobile_menu { border-color: {$accent} !important; }\n";
$css .= "body:not(.et-fb) .nav li ul a:hover { color: {$accent} !important; }\n";

// Primary CTA (external WhatsApp links): additive-only — no classes, no !important, no property overrides
$css .= "body:not(.et-fb) .et_pb_button[href^=\"https://wa.me\"] { will-change: transform; }\n";
$css .= "body:not(.et-fb) .et_pb_button[href^=\"https://wa.me\"]:hover { transform: translateY(-3px); box-shadow: 0 14px 40px rgba(229, 9, 20, 0.35); }\n";
$css .= "body:not(.et-fb) .et_pb_button[href^=\"https://wa.me\"]:active { transform: translateY(-1px); box-shadow: 0 6px 20px rgba(229, 9, 20, 0.25); }\n";
$css .= "body:not(.et-fb) .et_pb_button[href^=\"https://wa.me\"]:focus-visible { outline: 3px solid #e50914; outline-offset: 3px; }\n";

// Keyframes
$css .= "@keyframes dawFadeUp { from { opacity: 0; transform: translateY(24px); } to { opacity: 1; transform: translateY(0); } }\n";
$css .= "@keyframes dawShine { 0% { background-position: 0% center; } 50% { background-position: 100% center; } 100% { background-position: 0% center; } }\n";

// ── Write to disk (plugin enqueues from site/<site>/brand/assets/css/brand.css) ──
$brand_css_path = $root . '/DAW_bundle/site/' . $site . '/brand/assets/css/brand.css';
$dir = dirname($brand_css_path);
if (!is_dir($dir)) {
    mkdir($dir, 0775, true);
}
file_put_contents($brand_css_path, $css);
echo "brand.css written to disk (" . strlen($css) . " chars, path: {$brand_css_path})\n";

// ── Generate divitheme.json for deploy token resolution ──
$ds_path = $root . '/DAW_bundle/site/' . $site . '/design-system/divitheme.json';
$ds = [];
if (file_exists($ds_path)) {
    $ds = json_decode(file_get_contents($ds_path), true) ?: [];
}
$ds['tokens']['color'] = $colors;
$ds['tokens']['font'] = [
    'display' => $heading_font_raw,
    'body'    => $body_font_raw,
    'ui'      => $body_font_raw,
];
$ds['tokens']['radius'] = [
    'sm' => $vars['radius_sm'] ?? '2px',
    'md' => $btn_radius,
    'lg' => $vars['radius_lg'] ?? '16px',
];
$ds['tokens']['space'] = [
    'xs' => '4px', 'sm' => '8px', 'md' => '16px', 'lg' => '24px',
    'xl' => '32px', '2xl' => '48px', '3xl' => '64px',
];
file_put_contents($ds_path, json_encode($ds, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE));
echo "divitheme.json generated (" . filesize($ds_path) . " chars)\n";

echo "Done.\n";
