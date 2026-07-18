<?php
/**
 * generate-header-blocks.php — Generate raw Divi 5 blocks for the header
 * and update the specified Theme Builder layout.
 *
 * Usage:
 *   php generate-header-blocks.php --layout-id=127661
 */

$layout_id = 0;
foreach ($argv as $arg) {
    if (str_starts_with($arg, '--layout-id=')) {
        $layout_id = intval(substr($arg, 12));
    }
}
if (!$layout_id) {
    fwrite(STDERR, "Usage: php generate-header-blocks.php --layout-id=<id>\n");
    exit(1);
}

$project_root = dirname(__DIR__, 3);
require_once $project_root . '/app/public/wp-load.php';

$props = fn($arr) => json_encode($arr, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE);

$version = defined('DIVI_BUILDER_VERSION')
    ? DIVI_BUILDER_VERSION
    : (function_exists('wp_get_theme') && ($t = wp_get_theme('Divi'))->exists() ? $t->get('Version') : '5.7.4');

// Image block
$img_logo = $props([
    'builderVersion' => $version,
    'module' => [
        'meta' => ['adminLabel' => ['desktop' => ['value' => 'Desktop Logo']]],
        'advanced' => [
            'align' => ['desktop' => ['value' => 'center']],
            'sizing' => ['desktop' => ['value' => ['maxWidth' => '200px', 'width' => '200px']]],
        ],
        'decoration' => [
            'layout' => ['desktop' => ['value' => ['display' => 'block']]],
            'disabledOn' => [
                'phone' => ['value' => 'on'],
                'tabletOnly' => ['value' => 'on'],
                'desktopAbove' => ['value' => 'off'],
            ],
        ],
    ],
    'image' => [
        'innerContent' => [
            'desktop' => ['value' => [
                'src' => 'https://sanpablo.com.mx/wp-content/uploads/2023/07/Logo-ssp-color-ok.png',
                'alt' => 'San Pablo México',
                'titleText' => 'San Pablo México',
            ]],
        ],
    ],
]);

// Search block
$search_block = $props([
    'builderVersion' => $version,
    'module' => [
        'meta' => ['adminLabel' => ['desktop' => ['value' => 'Search']]],
        'advanced' => ['showButton' => ['desktop' => ['value' => 'off']]],
        'decoration' => [
            'border' => ['desktop' => ['value' => [
                'radius' => ['topLeft' => '9999px', 'topRight' => '9999px', 'bottomLeft' => '9999px', 'bottomRight' => '9999px'],
                'styles' => ['color' => '#DDD6CC', 'width' => '2px', 'style' => 'solid'],
            ]]],
            'sizing' => ['desktop' => ['value' => ['width' => '100%']]],
        ],
    ],
    'searchPlaceholder' => [
        'innerContent' => ['desktop' => ['value' => 'Buscar biblias, libros, autores, artículos religiosos...']],
    ],
]);

// Blurb (Mi cuenta)
$blurb_account = $props([
    'builderVersion' => $version,
    'module' => [
        'meta' => ['adminLabel' => ['desktop' => ['value' => 'My Account']]],
        'advanced' => [
            'link' => ['desktop' => ['value' => ['url' => '/mi-cuenta/']]],
        ],
        'decoration' => [
            'spacing' => ['desktop' => ['value' => ['margin' => ['top' => '', 'right' => '10px', 'bottom' => '0px', 'left' => '', 'syncVertical' => 'off', 'syncHorizontal' => 'off']]]],
            'layout' => ['desktop' => ['value' => ['display' => 'block']]],
        ],
    ],
    'imageIcon' => [
        'innerContent' => ['desktop' => ['value' => ['useIcon' => 'on', 'icon' => ['unicode' => '&#xf007;', 'type' => 'fa', 'weight' => '400']]]],
        'advanced' => [
            'color' => ['desktop' => ['value' => '#4A4138']],
            'placement' => ['desktop' => ['value' => 'left']],
        ],
        'decoration' => [
            'sizing' => ['desktop' => ['value' => ['width' => '20px', 'iconFontSize' => '20px']]],
        ],
    ],
    'title' => [
        'innerContent' => ['desktop' => ['value' => 'Mi cuenta']],
        'decoration' => ['font' => ['font' => ['desktop' => ['value' => ['family' => 'DM Sans', 'color' => '#4A4138', 'size' => '14px', 'weight' => '600']]]]],
    ],
]);

// Button (Contáctanos)
$btn_contact = $props([
    'builderVersion' => $version,
    'module' => [
        'meta' => ['adminLabel' => ['desktop' => ['value' => 'Button']]],
        'advanced' => [
            'button' => ['innerContent' => ['desktop' => ['value' => ['text' => 'Contáctanos']]]],
            'link' => ['desktop' => ['value' => ['url' => '#']]],
        ],
        'decoration' => [
            'background' => ['desktop' => ['value' => ['color' => '#0D1B2A']]],
            'border' => ['desktop' => ['value' => ['radius' => ['topLeft' => '10px', 'topRight' => '10px', 'bottomLeft' => '10px', 'bottomRight' => '10px']]]],
            'font' => ['font' => ['desktop' => ['value' => ['family' => 'DM Sans', 'color' => '#FFFFFF', 'size' => '14px', 'weight' => '600']]]],
        ],
    ],
]);

// Button (Categorías) — native Divi button with red bg + menu icon
$btn_categories = $props([
    'builderVersion' => $version,
    'module' => [
        'meta' => ['adminLabel' => ['desktop' => ['value' => 'Categories Toggle']]],
        'advanced' => [
            'button' => ['innerContent' => ['desktop' => ['value' => ['text' => 'Categorías']]]],
            'buttonIcon' => ['innerContent' => ['desktop' => ['value' => ['useIcon' => 'on', 'icon' => ['unicode' => '&#xf0c9;', 'type' => 'fa', 'weight' => '400']]]]],
            'link' => ['desktop' => ['value' => ['url' => '#']]],
        ],
        'decoration' => [
            'background' => ['desktop' => ['value' => ['color' => '#ED1B2F']]],
            'border' => ['desktop' => ['value' => ['radius' => ['topLeft' => '10px', 'topRight' => '10px', 'bottomLeft' => '0', 'bottomRight' => '0']]]],
            'font' => ['font' => ['desktop' => ['value' => ['family' => 'DM Sans', 'color' => '#FFFFFF', 'size' => '14px', 'weight' => '700']]]],
            'spacing' => ['desktop' => ['value' => ['padding' => ['top' => '14px', 'bottom' => '14px', 'left' => '20px', 'right' => '20px']]]],
        ],
    ],
]);

// Menu block (navigation) — with menu_id pointing to "Menú Encabezado Header"
$menu_block = $props([
    'builderVersion' => $version,
    'module' => [
        'meta' => ['adminLabel' => ['desktop' => ['value' => 'Menu']]],
        'advanced' => ['style' => ['desktop' => ['value' => 'left_aligned']]],
        'decoration' => [
            'font' => ['font' => ['desktop' => ['value' => ['family' => 'DM Sans', 'size' => '14px', 'weight' => '500', 'color' => '#4A4138']]]],
            'spacing' => ['desktop' => ['value' => ['margin' => ['top' => '0px', 'bottom' => '0px']]]],
        ],
    ],
    'menu' => ['desktop' => ['value' => 3768]],
    'menuDropdown' => [
        'advanced' => ['animation' => ['desktop' => ['value' => 'fade']]],
        'decoration' => [
            'background' => ['desktop' => ['value' => ['color' => '#FFFFFF']]],
            'border' => ['desktop' => ['value' => ['radius' => ['topLeft' => '0px', 'topRight' => '0px', 'bottomLeft' => '10px', 'bottomRight' => '10px']]]],
        ],
    ],
]);

// ──── BUILD THE FULL HEADER ────

$blocks = '';

// === SECTION 1: ANNOUNCE BAR ===
$blocks .= '<!-- wp:divi/section ' . $props([
    'builderVersion' => $version,
    'module' => [
        'advanced' => ['type' => ['desktop' => ['value' => 'regular']]],
        'decoration' => [
            'background' => ['desktop' => ['value' => ['color' => '#0D1B2A']]],
            'spacing' => ['desktop' => ['value' => ['padding' => ['top' => '0px', 'bottom' => '0px', 'right' => '0px', 'left' => '0px'], 'margin' => ['top' => '0px', 'bottom' => '0px']]]],
            'sizing' => ['desktop' => ['value' => ['width' => '100%', 'innerWidth' => '100%']]],
        ],
    ],
]) . ' -->';

$blocks .= '<!-- wp:divi/row ' . $props([
    'builderVersion' => $version,
    'module' => [
        'advanced' => ['columnStructure' => ['desktop' => ['value' => '4_4']]],
        'decoration' => ['layout' => ['desktop' => ['value' => ['flexWrap' => 'nowrap', 'display' => 'flex']]]],
    ],
]) . ' -->';

$blocks .= '<!-- wp:divi/column ' . $props([
    'builderVersion' => $version,
    'module' => [
        'advanced' => ['type' => ['desktop' => ['value' => '4_4']]],
        'decoration' => ['sizing' => ['desktop' => ['value' => ['flexType' => '24_24']]]],
    ],
]) . ' -->';

$blocks .= '<!-- wp:divi/code ' . $props([
    'builderVersion' => $version,
    'module' => [
        'meta' => ['adminLabel' => ['desktop' => ['value' => 'Announce Bar']]],
        'advanced' => ['htmlAttributes' => ['desktop' => ['value' => ['class' => 'daw-announce-bar']]]],
        'decoration' => [
            'spacing' => ['desktop' => ['value' => ['padding' => ['top' => '10px', 'bottom' => '10px', 'left' => '20px', 'right' => '20px']]]],
            'sizing' => ['desktop' => ['value' => ['width' => '100%']]],
        ],
    ],
]) . ' -->'
. '<div class="daw-announce-inner">'
. '<span class="daw-announce-dot"></span>'
. '<span class="daw-announce-text">Envío GRATIS en toda la república en compras mayores a <strong>$500 MXN</strong></span>'
. '<span class="daw-announce-sep">·</span>'
. '<span class="daw-announce-whatsapp"><i class="ti ti-brand-whatsapp"></i>Compra por WhatsApp al <strong>33 3250 5322</strong></span>'
. '<a class="daw-announce-link" href="#">Ver catálogo 2026 PDF</a>'
. '</div>'
. '<!-- /wp:divi/code -->';

$blocks .= '<!-- /wp:divi/column -->';
$blocks .= '<!-- /wp:divi/row -->';
$blocks .= '<!-- /wp:divi/section -->';

// === SECTION 2: MAIN HEADER (sticky) ===
$blocks .= '<!-- wp:divi/section ' . $props([
    'builderVersion' => $version,
    'module' => [
        'advanced' => ['type' => ['desktop' => ['value' => 'regular']]],
        'decoration' => [
            'background' => ['desktop' => ['value' => ['color' => '#FFFFFF']]],
            'spacing' => ['desktop' => ['value' => ['padding' => ['top' => '0px', 'bottom' => '0px', 'right' => '0px', 'left' => '0px'], 'margin' => ['top' => '0px', 'bottom' => '0px']]]],
            'position' => ['desktop' => ['value' => ['position' => 'sticky', 'zIndex' => '900', 'top' => '0px']]],
            'sizing' => ['desktop' => ['value' => ['width' => '100%', 'innerWidth' => '100%']]],
        ],
    ],
]) . ' -->';

// ── DESKTOP ROW 1: Logo | Search | Account + CTA ──
$blocks .= '<!-- wp:divi/row ' . $props([
    'builderVersion' => $version,
    'module' => [
        'advanced' => ['columnStructure' => ['desktop' => ['value' => '1_4,1_2,1_4']]],
        'decoration' => [
            'layout' => [
                'desktop' => ['value' => ['flexWrap' => 'nowrap', 'display' => 'flex', 'alignItems' => 'center']],
                'tablet' => ['value' => ['display' => 'none']],
                'phone' => ['value' => ['display' => 'none']],
            ],
            'spacing' => ['desktop' => ['value' => ['padding' => ['top' => '0px', 'bottom' => '0px', 'left' => '24px', 'right' => '24px']]]],
            'sizing' => ['desktop' => ['value' => ['maxWidth' => '1440px', 'width' => '100%']]],
        ],
    ],
]) . ' -->';

// Column 1: Logo
$blocks .= '<!-- wp:divi/column ' . $props([
    'builderVersion' => $version,
    'module' => [
        'advanced' => ['type' => ['desktop' => ['value' => '1_4']]],
        'decoration' => ['sizing' => ['desktop' => ['value' => ['flexType' => '6_24']]]],
    ],
]) . ' -->';
$blocks .= '<!-- wp:divi/image ' . $img_logo . ' /-->';
$blocks .= '<!-- /wp:divi/column -->';

// Column 2: Search
$blocks .= '<!-- wp:divi/column ' . $props([
    'builderVersion' => $version,
    'module' => [
        'advanced' => ['type' => ['desktop' => ['value' => '1_2']]],
        'decoration' => ['sizing' => ['desktop' => ['value' => ['flexType' => '12_24']]]],
    ],
]) . ' -->';
$blocks .= '<!-- wp:divi/search ' . $search_block . ' /-->';
$blocks .= '<!-- /wp:divi/column -->';

// Column 3: Account + CTA
$blocks .= '<!-- wp:divi/column ' . $props([
    'builderVersion' => $version,
    'module' => [
        'advanced' => ['type' => ['desktop' => ['value' => '1_4']]],
        'decoration' => ['sizing' => ['desktop' => ['value' => ['flexType' => '6_24']]]],
    ],
]) . ' -->';

// Nested row: 1_2,1_2 (account | cta)
$blocks .= '<!-- wp:divi/row ' . $props([
    'builderVersion' => $version,
    'module' => [
        'meta' => ['adminLabel' => ['desktop' => ['value' => 'Header Actions']]],
        'advanced' => ['columnStructure' => ['desktop' => ['value' => '1_2,1_2']]],
        'decoration' => [
            'layout' => ['desktop' => ['value' => ['flexWrap' => 'nowrap', 'display' => 'flex', 'alignItems' => 'center']]],
            'spacing' => ['desktop' => ['value' => ['padding' => ['top' => '0px', 'bottom' => '0px'], 'margin' => ['top' => '0px', 'bottom' => '0px']]]],
        ],
    ],
]) . ' -->';

$blocks .= '<!-- wp:divi/column ' . $props([
    'builderVersion' => $version,
    'module' => [
        'advanced' => ['type' => ['desktop' => ['value' => '1_2']]],
        'decoration' => ['sizing' => ['desktop' => ['value' => ['flexType' => '12_24']]]],
    ],
]) . ' -->';
$blocks .= '<!-- wp:divi/blurb ' . $blurb_account . ' /-->';
$blocks .= '<!-- /wp:divi/column -->';

$blocks .= '<!-- wp:divi/column ' . $props([
    'builderVersion' => $version,
    'module' => [
        'advanced' => ['type' => ['desktop' => ['value' => '1_2']]],
        'decoration' => ['sizing' => ['desktop' => ['value' => ['flexType' => '12_24']]]],
    ],
]) . ' -->';
$blocks .= '<!-- wp:divi/button ' . $btn_contact . ' /-->';
$blocks .= '<!-- /wp:divi/column -->';

$blocks .= '<!-- /wp:divi/row -->';
$blocks .= '<!-- /wp:divi/column -->';
$blocks .= '<!-- /wp:divi/row -->';

// ── DESKTOP ROW 2: Categories Button + Menu | Spacer | Actions ──
$blocks .= '<!-- wp:divi/row ' . $props([
    'builderVersion' => $version,
    'module' => [
        'advanced' => ['columnStructure' => ['desktop' => ['value' => '1_4,1_2,1_4']]],
        'decoration' => [
            'layout' => [
                'desktop' => ['value' => ['flexWrap' => 'nowrap', 'display' => 'flex', 'alignItems' => 'center']],
                'tablet' => ['value' => ['display' => 'none']],
                'phone' => ['value' => ['display' => 'none']],
            ],
            'border' => ['desktop' => ['value' => ['styles' => ['color' => '#EDE8E0', 'width' => '1px', 'style' => 'solid'], 'side' => 'top']]],
            'spacing' => ['desktop' => ['value' => ['padding' => ['top' => '0px', 'bottom' => '0px', 'left' => '24px', 'right' => '24px']]]],
            'sizing' => ['desktop' => ['value' => ['maxWidth' => '1440px', 'width' => '100%']]],
        ],
    ],
]) . ' -->';

// Column 1: Categories button + Menu
$blocks .= '<!-- wp:divi/column ' . $props([
    'builderVersion' => $version,
    'module' => [
        'advanced' => ['type' => ['desktop' => ['value' => '1_4']]],
        'decoration' => ['sizing' => ['desktop' => ['value' => ['flexType' => '6_24']]]],
    ],
]) . ' -->';

// Categories toggle as native divi/button with icon
$blocks .= '<!-- wp:divi/button ' . $btn_categories . ' /-->';

// Navigation menu with menu_id
$blocks .= '<!-- wp:divi/menu ' . $menu_block . ' /-->';
$blocks .= '<!-- /wp:divi/column -->';

// Column 2: Empty spacer
$blocks .= '<!-- wp:divi/column ' . $props([
    'builderVersion' => $version,
    'module' => [
        'advanced' => ['type' => ['desktop' => ['value' => '1_2']]],
        'decoration' => ['sizing' => ['desktop' => ['value' => ['flexType' => '12_24']]]],
    ],
]) . ' -->';
$blocks .= '<!-- /wp:divi/column -->';

// Column 3: Actions (wishlist, cart, dark mode) as divi/code with CSS classes
$blocks .= '<!-- wp:divi/column ' . $props([
    'builderVersion' => $version,
    'module' => [
        'advanced' => ['type' => ['desktop' => ['value' => '1_4']]],
        'decoration' => ['sizing' => ['desktop' => ['value' => ['flexType' => '6_24']]]],
    ],
]) . ' -->';

$blocks .= '<!-- wp:divi/code ' . $props([
    'builderVersion' => $version,
    'module' => [
        'meta' => ['adminLabel' => ['desktop' => ['value' => 'Actions Row 2']]],
        'decoration' => ['spacing' => ['desktop' => ['value' => ['padding' => ['top' => '0px', 'bottom' => '0px'], 'margin' => ['top' => '0px', 'bottom' => '0px']]]]],
    ],
]) . ' -->'
. '<div class="daw-header-actions">'
. '<div class="daw-action-pill"><i class="ti ti-heart"></i><span class="daw-action-badge">8</span></div>'
. '<div class="daw-action-pill"><i class="ti ti-shopping-cart"></i><span>Carrito</span><span class="daw-action-badge">3</span></div>'
. '<button class="daw-theme-toggle"><i class="ti ti-moon"></i></button>'
. '</div>'
. '<!-- /wp:divi/code -->';
$blocks .= '<!-- /wp:divi/column -->';
$blocks .= '<!-- /wp:divi/row -->';

// ── MOBILE ROW (tablet + phone) ──
$blocks .= '<!-- wp:divi/row ' . $props([
    'builderVersion' => $version,
    'module' => [
        'advanced' => ['columnStructure' => ['desktop' => ['value' => '4_4']]],
        'decoration' => [
            'layout' => [
                'desktop' => ['value' => ['flexWrap' => 'wrap', 'display' => 'none']],
                'tablet' => ['value' => ['display' => 'flex', 'flexWrap' => 'wrap']],
                'phone' => ['value' => ['display' => 'flex', 'flexWrap' => 'wrap']],
            ],
            'disabledOn' => [
                'desktopAbove' => ['value' => 'on'],
                'tabletOnly' => ['value' => 'off'],
                'phone' => ['value' => 'off'],
            ],
        ],
    ],
]) . ' -->';

$blocks .= '<!-- wp:divi/column ' . $props([
    'builderVersion' => $version,
    'module' => [
        'advanced' => ['type' => ['desktop' => ['value' => '4_4']]],
        'decoration' => ['sizing' => ['desktop' => ['value' => ['flexType' => '24_24']]]],
    ],
]) . ' -->';

$mobile_html = '<div class="daw-mobile-header">'
    . '<div class="daw-mobile-row">'
    . '<button class="daw-hamburger"><span></span><span></span><span></span></button>'
    . '<a class="daw-mobile-logo" href="/">'
    . '<span class="daw-mobile-logo-icon">SP</span>'
    . '<span class="daw-mobile-logo-text">SAN <span>PABLO</span></span>'
    . '</a>'
    . '<div class="daw-mobile-actions">'
    . '<button class="daw-mobile-action-btn"><i class="ti ti-phone"></i></button>'
    . '<button class="daw-mobile-action-btn"><i class="ti ti-shopping-cart"></i><span class="daw-action-badge">3</span></button>'
    . '</div>'
    . '</div>'
    . '<div class="daw-mobile-search">'
    . '<div class="daw-mobile-search-inner">'
    . '<i class="ti ti-search"></i>'
    . '<input type="text" placeholder="Buscar biblias, libros, autores...">'
    . '</div>'
    . '</div>'
    . '</div>';

$blocks .= '<!-- wp:divi/code ' . $props([
    'builderVersion' => $version,
    'module' => [
        'meta' => ['adminLabel' => ['desktop' => ['value' => 'Mobile Header']]],
        'decoration' => [
            'background' => ['desktop' => ['value' => ['color' => '#FFFFFF']]],
            'border' => ['desktop' => ['value' => ['styles' => ['color' => '#EDE8E0', 'width' => '1px', 'style' => 'solid'], 'side' => 'bottom']]],
            'spacing' => ['desktop' => ['value' => ['padding' => ['top' => '0px', 'bottom' => '0px', 'left' => '0px', 'right' => '0px']]]],
        ],
    ],
    'content' => ['innerContent' => ['desktop' => ['value' => $mobile_html]]],
]) . ' /-->';

$blocks .= '<!-- /wp:divi/column -->';
$blocks .= '<!-- /wp:divi/row -->';
$blocks .= '<!-- /wp:divi/section -->';

// Update the post — NO wp_slash() to prevent double-escaping
$post_data = [
    'ID'           => $layout_id,
    'post_content' => $blocks,
    'post_status'  => 'publish',
];

$result = wp_update_post($post_data, true);
if (is_wp_error($result)) {
    fwrite(STDERR, "[ERROR] Update failed: " . $result->get_error_message() . "\n");
    exit(1);
}

echo "[OK] Header layout ID {$layout_id} updated successfully.\n";

update_post_meta($layout_id, '_et_pb_built_with_d5', '1');
update_post_meta($layout_id, '_et_builder_version', $version);

if (function_exists('et_core_clear_wp_cache')) {
    et_core_clear_wp_cache();
    echo "[OK] Divi cache cleared.\n";
}

echo "[OK] Post ID {$layout_id} is now live.\n";
