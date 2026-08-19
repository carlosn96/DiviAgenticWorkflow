<?php
namespace DAC\CLI;

/**
 * Agentic Command v3.1 — Deploys pages and global layouts with Divi 5.10.1.
 *
 * Validates schema blocks, resolves design tokens via Design_Resolver,
 * then compiles to Divi 5 blocks via Layout_Engine.
 */
class Agentic_Command {

    private array $native_blocks = [
        'divi/section', 'divi/row', 'divi/column', 'divi/row-inner', 'divi/column-inner',
        'divi/text', 'divi/image', 'divi/button', 'divi/code', 'divi/video',
        'divi/audio', 'divi/heading', 'divi/icon', 'divi/link', 'divi/divider',
        'divi/gallery', 'divi/breadcrumbs',
        'divi/menu', 'divi/toggle', 'divi/accordion', 'divi/accordion-item',
        'divi/tabs', 'divi/tab', 'divi/dropdown',
        'divi/contact-form', 'divi/contact-field', 'divi/contact-form-7',
        'divi/signup', 'divi/signup-custom-field',
        'divi/social-media-follow', 'divi/social-media-follow-network',
        'divi/blog', 'divi/post-title', 'divi/post-content', 'divi/post-nav',
        'divi/post-slider', 'divi/comments', 'divi/search',
        'divi/blurb', 'divi/cta', 'divi/pricing-table', 'divi/pricing-tables',
        'divi/team-member', 'divi/testimonial', 'divi/icon-list', 'divi/icon-list-item',
        'divi/lottie', 'divi/before-after-image', 'divi/canvas-portal', 'divi/svg',
        'divi/number-counter', 'divi/counter', 'divi/counters',
        'divi/circle-counter',
        'divi/slider', 'divi/slide', 'divi/video-slider', 'divi/video-slider-item',
        'divi/fullwidth-code', 'divi/fullwidth-header', 'divi/fullwidth-image',
        'divi/fullwidth-map', 'divi/fullwidth-menu', 'divi/fullwidth-portfolio',
        'divi/fullwidth-post-content', 'divi/fullwidth-post-slider',
        'divi/fullwidth-post-title', 'divi/fullwidth-slider',
        'divi/group', 'divi/group-carousel', 'divi/global-layout',
        'divi/portfolio', 'divi/filterable-portfolio', 'divi/sidebar',
        'divi/login', 'divi/countdown-timer', 'divi/map', 'divi/map-pin',
        'divi/shortcode-module', 'divi/placeholder', 'divi/layout',
        'divi/shop',
        'divi/woocommerce-breadcrumb', 'divi/woocommerce-cart-notice',
        'divi/woocommerce-cart-products', 'divi/woocommerce-cart-totals',
        'divi/woocommerce-checkout-additional-info', 'divi/woocommerce-checkout-billing',
        'divi/woocommerce-checkout-order-details', 'divi/woocommerce-checkout-payment-info',
        'divi/woocommerce-checkout-shipping', 'divi/woocommerce-cross-sells',
        'divi/woocommerce-product-additional-info', 'divi/woocommerce-product-add-to-cart',
        'divi/woocommerce-product-description', 'divi/woocommerce-product-gallery',
        'divi/woocommerce-product-images', 'divi/woocommerce-product-meta',
        'divi/woocommerce-product-price', 'divi/woocommerce-product-rating',
        'divi/woocommerce-product-reviews', 'divi/woocommerce-product-stock',
        'divi/woocommerce-product-tabs', 'divi/woocommerce-product-title',
        'divi/woocommerce-product-upsell', 'divi/woocommerce-related-products',
    ];

    private array $allowed_blocks = [];

    public static function register() {
        \WP_CLI::add_command( 'agentic', self::class );
    }

    /**
     * Syncs design-system color tokens to Divi 5 Global Colors (gcid-*).
     *
     * ## OPTIONS
     *
     * <subcommand>
     * : Subcommand: sync, status, list
     *
     * [--design-system=<path>]
     * : Path to the design-system JSON file.
     *
     * [--force]
     * : Force re-sync even if hash matches.
     *
     * @when after_wp_load
     */
    public function global_colors( $args, $assoc_args ) {
        $subcommand = $args[0] ?? 'status';
        $ds_path    = $assoc_args['design-system'] ?? '';
        $colors_ds  = [];
        $ds_hash    = '';
        $key_map    = [];

        if ( ! empty( $ds_path ) ) {
            if ( ! file_exists( $ds_path ) ) {
                \WP_CLI::error( "Design system not found: {$ds_path}" );
            }
            $raw = file_get_contents( $ds_path );
            $raw = ltrim( $raw, "\xEF\xBB\xBF" );
            $ds  = json_decode( $raw, true );
            if ( json_last_error() !== JSON_ERROR_NONE ) {
                \WP_CLI::error( 'Design system JSON error: ' . json_last_error_msg() );
            }

            $color_tokens       = $ds['tokens']['color'] ?? [];
            $token_count        = count( $color_tokens );
            foreach ( $color_tokens as $key => $hex ) {
                $gcid                 = 'gcid-' . sanitize_title( $key );
                $key_map[ $gcid ]     = $key;
                $colors_ds[ $gcid ]   = [
                    'color'  => $hex,
                    'active' => 'yes',
                ];
            }

            // Auto-map design system tokens to Divi 5 Customizer colors.
            // Reads the "customizer" section from design system JSON:
            //   "customizer": { "primary": "accent", "secondary": "premium", ... }
            // Maps short slot names → Divi gcid IDs, then reads the referenced
            // token hex. No hardcoded mapping needed — change the JSON, not PHP.
            $customizer_slots = \DAC\Core\Token_Registry::get_customizer_slots();
            $customizer_map = $ds['customizer'] ?? [];
            foreach ( $customizer_map as $slot => $token_key ) {
                $gcid = $customizer_slots[ $slot ] ?? '';
                if ( ! empty( $gcid ) && isset( $color_tokens[ $token_key ] ) ) {
                    $key_map[ $gcid ]   = $token_key . ' (customizer)';
                    $colors_ds[ $gcid ] = [
                        'color'  => $color_tokens[ $token_key ],
                        'active' => 'yes',
                    ];
                }
            }

            $ds_hash = md5( json_encode( $colors_ds ) );
        }

        $stored_hash = get_option( '_dac_gcid_hash', '' );

        switch ( $subcommand ) {
            case 'sync':
                if ( empty( $colors_ds ) ) {
                    \WP_CLI::error( 'No color tokens found in design system.' );
                }
                if ( $ds_hash === $stored_hash && ! isset( $assoc_args['force'] ) ) {
                    \WP_CLI::success( 'Global colors already in sync. Use --force to re-sync.' );
                    return;
                }
                if ( ! class_exists( '\ET\Builder\Packages\GlobalData\GlobalData' ) ) {
                    \WP_CLI::error( 'Divi 5 GlobalData class not found. Is Divi 5 active?' );
                }

                // Clear existing global_colors first to prevent accumulation.
                // Divi 5 set_global_colors(…, true) merges by default (array_merge),
                // so every sync would add duplicates without this cleanup.
                $existing_global_data = maybe_unserialize( et_get_option( 'et_global_data' ) );
                if ( is_array( $existing_global_data ) && isset( $existing_global_data['global_colors'] ) ) {
                    $existing_global_data['global_colors'] = [];
                    et_update_option( 'et_global_data', $existing_global_data );
                }

                \ET\Builder\Packages\GlobalData\GlobalData::set_global_colors( $colors_ds, true );
                update_option( '_dac_gcid_hash', $ds_hash );
                \WP_CLI::success( $token_count . ' global colors synced + 5 Customizer defaults overridden with design system values.' );
                $this->_print_gcid_table( $colors_ds, $key_map );
                break;

            case 'status':
                if ( empty( $ds_path ) ) {
                    $this->_show_gcids();
                    break;
                }
                if ( ! empty( $stored_hash ) && $ds_hash === $stored_hash ) {
                    \WP_CLI::success( 'Global colors SYNCED with design system.' );
                    $this->_print_gcid_table( $colors_ds, $key_map );
                } elseif ( ! empty( $stored_hash ) ) {
                    \WP_CLI::warning( 'Global colors OUT OF SYNC.' );
                    \WP_CLI::log( 'Run: wp agentic global_colors sync --design-system="' . $ds_path . '"' );
                    $this->_print_gcid_table( $colors_ds, $key_map );
                } else {
                    \WP_CLI::warning( 'No global colors synced yet.' );
                    \WP_CLI::log( 'Run: wp agentic global_colors sync --design-system="path/to/divitheme.json"' );
                }
                break;

            case 'list':
                $this->_show_gcids();
                break;

            default:
                \WP_CLI::error( "Unknown subcommand: {$subcommand}. Use: sync, status, list" );
        }
    }

    private function _print_gcid_table( array $colors, array $key_map ): void {
        $items = [];
        foreach ( $colors as $gcid => $data ) {
            $label = $key_map[ $gcid ] ?? $gcid;
            $items[] = [
                'gcid'  => $gcid,
                'token' => "{{design:color:{$label}}}",
                'hex'   => $data['color'],
                'css'   => "var(--{$gcid})",
            ];
        }
        \WP_CLI\Utils\format_items( 'table', $items, [ 'gcid', 'token', 'hex', 'css' ] );
    }

    private function _show_gcids(): void {
        if ( ! class_exists( '\ET\Builder\Packages\GlobalData\GlobalData' ) ) {
            \WP_CLI::error( 'Divi 5 GlobalData class not found.' );
        }
        $colors = \ET\Builder\Packages\GlobalData\GlobalData::get_global_colors();
        if ( empty( $colors ) ) {
            \WP_CLI::log( 'No global colors registered in Divi 5.' );
            return;
        }
        $items = [];
        foreach ( $colors as $gcid => $data ) {
            $items[] = [
                'gcid'  => $gcid,
                'color' => $data['color'] ?? '—',
                'status' => $data['status'] ?? '—',
            ];
        }
        \WP_CLI::log( 'Divi 5 Global Colors:' );
        \WP_CLI\Utils\format_items( 'table', $items, [ 'gcid', 'color', 'status' ] );
    }

    /**
     * Deploys a page from a JSON schema.
     *
     * ## OPTIONS
     *
     * --title=<title>
     * : The title of the page.
     *
     * --slug=<slug>
     * : The slug of the page.
     *
     * --schema=<path>
     * : Path to the JSON schema file.
     *
     * [--design-system=<path>]
     * : Path to the design-system JSON file for token/preset resolution.
     *
     * [--status=<status>]
     * : Post status: publish (default) or draft.
     *
     * [--front]
     * : Set as front page.
     *
     * @when after_wp_load
     */
    public function deploy_page( $args, $assoc_args ) {
        $title = $assoc_args['title'];
        $slug  = $assoc_args['slug'];
        $path  = $assoc_args['schema'];
        $status = $assoc_args['status'] ?? 'publish';

        if ( ! file_exists( $path ) ) {
            \WP_CLI::error( "Schema not found: {$path}" );
        }

        // Load schema
        $raw = file_get_contents( $path );
        $raw = ltrim( $raw, "\xEF\xBB\xBF" );
        $raw = trim( $raw );

        // ------------- DESIGN TOKEN RESOLUTION -------------
        if ( isset( $assoc_args['design-system'] ) ) {
            $gcid_hash = get_option( '_dac_gcid_hash', '' );
            if ( ! empty( $gcid_hash ) ) {
                \WP_CLI::log( 'Global colors active — tokens resolve to var(--gcid-*)' );
            }

            $brand_vars_path = preg_replace( '#(design-system[\\\\/])?divitheme\.json$#', 'brand/_design_vars.json', $assoc_args['design-system'] );
            if ( ! file_exists( $brand_vars_path ) ) {
                $brand_vars_path = null;
            }

            $resolver = new \DAC\Core\Design_Resolver( $assoc_args['design-system'], $brand_vars_path );
            $raw = $resolver->resolve_schema_string( $raw );
            \WP_CLI::log( "Design tokens resolved from: {$assoc_args['design-system']}" );

            if ( empty( $gcid_hash ) ) {
                $ds_colors = $resolver->get_design()['tokens']['color'] ?? [];
                if ( ! empty( $ds_colors ) ) {
                    \WP_CLI::warning( 'Color tokens will resolve to hex — no global colors synced.' );
                    \WP_CLI::log( '  Run: wp agentic global_colors sync --design-system="' . $assoc_args['design-system'] . '"' );
                }
            }
        }
        // ----------------------------------------------------

        // ------------- VALIDATION PHASE (blocks only) -------------
        $validation_errors = $this->validate_schema_string( $raw );
        if ( ! empty( $validation_errors ) ) {
            foreach ( $validation_errors as $error ) {
                \WP_CLI::error( "Schema validation error: {$error}" );
            }
        }
        // ----------------------------------------------------------

        $engine = new \DAC\Core\Layout_Engine();
        $blocks = $engine->compile( $raw );

        $page = get_page_by_path( $slug, OBJECT, 'page' );

        $blocks_slashed = wp_slash( $blocks );

        $post_data = [
            'post_title'   => sanitize_text_field( $title ),
            'post_name'    => sanitize_title( $slug ),
            'post_content' => $blocks_slashed,
            'post_status'  => $status,
            'post_type'    => 'page',
            'post_author'  => 1,
        ];

        if ( $page ) {
            $post_data['ID'] = $page->ID;
            $post_id = wp_update_post( $post_data );
            \WP_CLI::log( "Updated page ID: {$post_id}" );
        } else {
            $post_id = wp_insert_post( $post_data );
            \WP_CLI::log( "Created page ID: {$post_id}" );
        }

        $this->apply_divi_meta( $post_id );

        if ( isset( $assoc_args['front'] ) ) {
            update_option( 'show_on_front', 'page' );
            update_option( 'page_on_front', $post_id );
            \WP_CLI::success( "Set as front page." );
        }

        \WP_CLI::success( "Page '{$title}' deployed." );
    }

    /**
     * Creates a template. Fails if --use-on already exists.
     *
     * ## OPTIONS
     *
     * --use-on=<scope>
     * : Template scope (_et_use_on). See the main command help for valid patterns.
     *
     * --title=<title>
     * : Title for the template.
     *
     * ## EXAMPLES
     *
     *     wp agentic template_create --use-on="singular:post_type:page:all" --title="Pages"
     *
     * @when after_wp_load
     */
    public function template_create( $args, $assoc_args ) {
        $use_on = $assoc_args['use-on'] ?? '';
        $title  = $assoc_args['title'] ?? '';
        if ( empty( $use_on ) || empty( $title ) ) {
            \WP_CLI::error( "--use-on and --title are required." );
        }
        $this->validate_use_on( $use_on );

        $existing = $this->find_templates_by_use_on( $use_on );
        if ( ! empty( $existing ) ) {
            $tid = $existing[0]->ID;
            \WP_CLI::error( "Template for '{$use_on}' already exists (ID {$tid}). Check with: template_show {$tid}. To update: template_update {$tid} --title=\"{$title}\" or deploy_global_ecosystem --mode=update --template-id={$tid} ..." );
        }

        $id = $this->create_template( $use_on, $title );
        \WP_CLI::success( "Template created: ID {$id}." );
    }

    /**
     * Finds a template by --use-on. Returns 0 if not found.
     *
     * ## OPTIONS
     *
     * --use-on=<scope>
     * : Template scope (_et_use_on).
     *
     * @when after_wp_load
     */
    public function template_find( $args, $assoc_args ) {
        $use_on = $assoc_args['use-on'] ?? '';
        if ( empty( $use_on ) ) {
            \WP_CLI::error( "--use-on is required." );
        }

        $existing = $this->find_templates_by_use_on( $use_on );
        if ( count( $existing ) > 1 ) {
            $ids = array_map( fn( $p ) => $p->ID, $existing );
            \WP_CLI::error( "Multiple templates for '{$use_on}': IDs " . implode( ', ', $ids ) );
        }
        if ( empty( $existing ) ) {
            \WP_CLI::log( '0 (not found)' );
            return;
        }
        \WP_CLI::log( (string) $existing[0]->ID );
    }

    /**
     * Ensures a template exists for --use-on with the given title.
     * Creates if missing, updates title if exists (idempotent).
     *
     * ## OPTIONS
     *
     * --use-on=<scope>
     * : Template scope (_et_use_on).
     *
     * --title=<title>
     * : Title for the template.
     *
     * @when after_wp_load
     */
    public function template_ensure( $args, $assoc_args ) {
        $use_on = $assoc_args['use-on'] ?? '';
        $title  = $assoc_args['title'] ?? '';
        if ( empty( $use_on ) || empty( $title ) ) {
            \WP_CLI::error( "--use-on and --title are required." );
        }
        $this->validate_use_on( $use_on );

        $existing = $this->find_templates_by_use_on( $use_on );
        if ( count( $existing ) > 1 ) {
            $ids = array_map( fn( $p ) => $p->ID, $existing );
            \WP_CLI::error( "Multiple templates for '{$use_on}': IDs " . implode( ', ', $ids ) . '. Use template_update <id> --title=...' );
        }

        if ( ! empty( $existing ) ) {
            $id = $existing[0]->ID;
            wp_update_post([ 'ID' => $id, 'post_title' => sanitize_text_field( $title ) ]);
            $this->register_template_with_theme_builder( $id );
            \WP_CLI::log( (string) $id );
            return;
        }

        $id = $this->create_template( $use_on, $title );
        \WP_CLI::log( (string) $id );
    }

    /**
     * Updates a template's title and/or use-on by ID.
     *
     * ## OPTIONS
     *
     * <id>
     * : Template ID.
     *
     * [--title=<title>]
     * : New title.
     *
     * [--use-on=<scope>]
     * : New _et_use_on scope.
     *
     * @when after_wp_load
     */
    public function template_update( $args, $assoc_args ) {
        $template_id = (int) ( $args[0] ?? 0 );
        if ( $template_id < 1 ) {
            \WP_CLI::error( "Usage: wp agentic template_update <id> [--title=...] [--use-on=...]" );
        }
        $post = get_post( $template_id );
        if ( ! $post || $post->post_type !== 'et_template' ) {
            \WP_CLI::error( "Template ID {$template_id} not found." );
        }

        $updated = false;
        if ( isset( $assoc_args['title'] ) ) {
            wp_update_post([ 'ID' => $template_id, 'post_title' => sanitize_text_field( $assoc_args['title'] ) ]);
            \WP_CLI::log( "  Title updated." );
            $updated = true;
        }
        if ( isset( $assoc_args['use-on'] ) ) {
            $this->validate_use_on( $assoc_args['use-on'] );
            delete_post_meta( $template_id, '_et_use_on' );
            add_post_meta( $template_id, '_et_use_on', $assoc_args['use-on'] );
            \WP_CLI::log( "  Use-on updated to: {$assoc_args['use-on']}" );
            $updated = true;
        }

        if ( ! $updated ) {
            \WP_CLI::error( "Nothing to update. Pass --title, --use-on, or both." );
        }

        \WP_CLI::success( "Template {$template_id} updated." );
    }

    /**
     * Shows template details.
     *
     * ## OPTIONS
     *
     * <id>
     * : Template ID.
     *
     * @when after_wp_load
     */
    public function template_show( $args, $assoc_args ) {
        $template_id = (int) ( $args[0] ?? 0 );
        if ( $template_id < 1 ) {
            \WP_CLI::error( "Usage: wp agentic template_show <id>" );
        }
        $post = get_post( $template_id );
        if ( ! $post || $post->post_type !== 'et_template' ) {
            \WP_CLI::error( "Template ID {$template_id} not found." );
        }

        $use_on   = get_post_meta( $template_id, '_et_use_on', true );
        $enabled  = get_post_meta( $template_id, '_et_enabled', true );
        $default  = get_post_meta( $template_id, '_et_default', true );
        $header   = (int) get_post_meta( $template_id, '_et_header_layout_id', true );
        $footer   = (int) get_post_meta( $template_id, '_et_footer_layout_id', true );
        $body     = (int) get_post_meta( $template_id, '_et_body_layout_id', true );

        \WP_CLI\Utils\format_items( 'table', [ [
            'ID'      => $template_id,
            'title'   => $post->post_title,
            'use_on'  => $use_on ?: '(none)',
            'default' => $default ?: '0',
            'enabled' => $enabled ?: '0',
            'header'  => $header ?: '—',
            'footer'  => $footer ?: '—',
            'body'    => $body ?: '—',
        ] ], [ 'ID', 'title', 'use_on', 'default', 'enabled', 'header', 'footer', 'body' ] );
    }

    /**
     * Wires layouts to a template.
     *
     * ## OPTIONS
     *
     * <id>
     * : Template ID.
     *
     * [--header-id=<id>]
     * : Header layout ID to assign.
     *
     * [--footer-id=<id>]
     * : Footer layout ID to assign.
     *
     * [--body-id=<id>]
     * : Body layout ID to assign.
     *
     * [--header-enabled=<0|1>]
     * : Enable header region. Default: 1.
     *
     * [--footer-enabled=<0|1>]
     * : Enable footer region. Default: 1.
     *
     * [--body-enabled=<0|1>]
     * : Enable body region. Default: 1.
     *
     * [--header-global=<0|1>]
     * : Whether header layout is shared across templates. Default: 1.
     *
     * [--footer-global=<0|1>]
     * : Whether footer layout is shared across templates. Default: 1.
     *
     * [--body-global=<0|1>]
     * : Whether body layout is shared across templates. Default: 1.
     *
     * @when after_wp_load
     */
    public function template_wire( $args, $assoc_args ) {
        $template_id = (int) ( $args[0] ?? 0 );
        if ( $template_id < 1 ) {
            \WP_CLI::error( "Usage: wp agentic template_wire <id> [--header-id=...] [--footer-id=...] [--body-id=...]" );
        }
        $post = get_post( $template_id );
        if ( ! $post || $post->post_type !== 'et_template' ) {
            \WP_CLI::error( "Template ID {$template_id} not found." );
        }

        $components = [ 'header', 'footer', 'body' ];
        foreach ( $components as $key ) {
            $id_key = "{$key}-id";
            $enabled_key = "{$key}-enabled";
            $global_key = "{$key}-global";

            if ( isset( $assoc_args[ $id_key ] ) ) {
                $layout_id = (int) $assoc_args[ $id_key ];
                $post_type = "et_{$key}_layout";
                $layout = get_post( $layout_id );
                if ( ! $layout || $layout->post_type !== $post_type ) {
                    \WP_CLI::error( "{$post_type} ID {$layout_id} not found." );
                }
                update_post_meta( $template_id, "_et_{$key}_layout_id", $layout_id );
                \WP_CLI::log( "  Wired {$key} layout ID {$layout_id} to template {$template_id}." );
            } else {
                update_post_meta( $template_id, "_et_{$key}_layout_id", 0 );
            }

            $enabled = isset( $assoc_args[ $enabled_key ] ) ? $assoc_args[ $enabled_key ] : '1';
            update_post_meta( $template_id, "_et_{$key}_layout_enabled", $enabled );

            $global = isset( $assoc_args[ $global_key ] ) ? $assoc_args[ $global_key ] : '1';
            update_post_meta( $template_id, "_et_{$key}_layout_global", $global );
        }

        // Ensure template is active — Divi marks unused templates with this meta on UI saves
        delete_post_meta( $template_id, '_et_theme_builder_marked_as_unused' );

        // Re-register with Theme Builder in case it was detached by a UI save
        $this->register_template_with_theme_builder( $template_id );

        \WP_CLI::success( "Template {$template_id} wired." );
    }

    /**
     * Returns the default template ID (creates one if none exists).
     *
     * ## OPTIONS
     *
     * [--title=<title>]
     * : Title to set on the default template.
     *
     * ## EXAMPLES
     *
     *     wp agentic template_default
     *     wp agentic template_default --title="Footer Global"
     *
     * @when after_wp_load
     */
    public function template_default( $args, $assoc_args ) {
        $id = $this->get_or_create_default_template();
        if ( isset( $assoc_args['title'] ) ) {
            wp_update_post([ 'ID' => $id, 'post_title' => sanitize_text_field( $assoc_args['title'] ) ]);
        }
        \WP_CLI::log( (string) $id );
    }

    /**
     * Trashes a template and detaches it from the Theme Builder.
     *
     * Follows Divi's own deletion pattern:
     * - Trashes the et_template post (soft delete)
     * - Removes the template ID from the Theme Builder post's _et_template meta
     * - Does NOT trash associated layouts — Divi marks them unused and
     *   cleans up after 7 days via et_theme_builder_trash_draft_and_unused_posts()
     *
     * ## OPTIONS
     *
     * <id>
     * : Template ID to trash.
     *
     * @when after_wp_load
     */
    public function template_delete( $args, $assoc_args ) {
        $template_id = (int) ( $args[0] ?? 0 );
        if ( $template_id < 1 ) {
            \WP_CLI::error( "Usage: wp agentic template_delete <id>" );
        }

        $post = get_post( $template_id );
        if ( ! $post || $post->post_type !== 'et_template' ) {
            \WP_CLI::error( "Template ID {$template_id} not found or not an et_template." );
        }

        // Detach from Theme Builder post's _et_template meta (match D5 REST pattern)
        $this->detach_template_from_theme_builder( $template_id );

        // Trash the template (soft delete — Divi pattern)
        wp_trash_post( $template_id );

        \WP_CLI::success( "Template {$template_id} trashed." );
    }

    private function detach_template_from_theme_builder( int $template_id ): void {
        if ( ! defined( 'ET_THEME_BUILDER_THEME_BUILDER_POST_TYPE' ) ) {
            return;
        }

        $live_id = et_theme_builder_get_theme_builder_post_id( true, false );
        if ( ! $live_id ) {
            return;
        }

        $existing = get_post_meta( $live_id, '_et_template', false );
        if ( empty( $existing ) || ! in_array( (string) $template_id, $existing, true ) ) {
            return;
        }

        delete_post_meta( $live_id, '_et_template' );
        foreach ( $existing as $tid ) {
            if ( (string) $template_id !== $tid ) {
                add_post_meta( $live_id, '_et_template', $tid );
            }
        }
        \WP_CLI::log( "  Detached template {$template_id} from Theme Builder post {$live_id}." );
    }

    /**
     * Deploys a layout from a combined JSON. Always creates a new layout post.
     *
     * ## OPTIONS
     *
     * <type>
     * : Layout type: header, footer, or body.
     *
     * --schema=<path>
     * : Path to the combined JSON file.
     *
     * [--design-system=<path>]
     * : Path to the design-system JSON file for token/preset resolution.
     *
     * @when after_wp_load
     */
    public function layout_deploy( $args, $assoc_args ) {
        $type   = $args[0] ?? '';
        $post_type = $this->layout_type_to_post_type( $type );
        if ( ! $post_type ) {
            \WP_CLI::error( "Invalid type: {$type}. Use: header, footer, or body." );
        }
        $path = $assoc_args['schema'] ?? '';
        if ( empty( $path ) ) {
            \WP_CLI::error( "--schema is required." );
        }

        $layout_id = $this->compile_and_insert_layout( 0, $path, $post_type, $assoc_args['design-system'] ?? null );
        \WP_CLI::success( "{$type} layout created: ID {$layout_id}." );
        \WP_CLI::log( (string) $layout_id );
    }

    /**
     * Updates an existing layout by ID. Fails if ID not found.
     *
     * ## OPTIONS
     *
     * <type>
     * : Layout type: header, footer, or body.
     *
     * --schema=<path>
     * : Path to the combined JSON file.
     *
     * --by-id=<id>
     * : Layout ID to update.
     *
     * [--design-system=<path>]
     * : Path to the design-system JSON file.
     *
     * @when after_wp_load
     */
    public function layout_ensure( $args, $assoc_args ) {
        $type   = $args[0] ?? '';
        $post_type = $this->layout_type_to_post_type( $type );
        if ( ! $post_type ) {
            \WP_CLI::error( "Invalid type: {$type}. Use: header, footer, or body." );
        }
        $path      = $assoc_args['schema'] ?? '';
        $layout_id = (int) ( $assoc_args['by-id'] ?? 0 );
        if ( empty( $path ) || $layout_id < 1 ) {
            \WP_CLI::error( "--schema and --by-id are required." );
        }

        $post = get_post( $layout_id );
        if ( ! $post || $post->post_type !== $post_type ) {
            \WP_CLI::error( "{$post_type} ID {$layout_id} not found." );
        }

        $result_id = $this->compile_and_insert_layout( $layout_id, $path, $post_type, $assoc_args['design-system'] ?? null );
        \WP_CLI::success( "{$type} layout updated: ID {$result_id}." );
        \WP_CLI::log( (string) $result_id );
    }

    /**
     * Lists layouts of a given type.
     *
     * ## OPTIONS
     *
     * <type>
     * : Layout type: header, footer, or body.
     *
     * @when after_wp_load
     */
    public function layout_list( $args, $assoc_args ) {
        $type   = $args[0] ?? '';
        $post_type = $this->layout_type_to_post_type( $type );
        if ( ! $post_type ) {
            \WP_CLI::error( "Invalid type: {$type}. Use: header, footer, or body." );
        }

        $layouts = get_posts([
            'post_type'      => $post_type,
            'posts_per_page' => -1,
            'post_status'    => 'publish',
            'orderby'        => 'ID',
            'order'          => 'ASC',
        ]);

        if ( empty( $layouts ) ) {
            \WP_CLI::log( "No {$type} layouts found." );
            return;
        }

        $items = array_map( fn( $p ) => [
            'ID'    => $p->ID,
            'title' => $p->post_title,
            'slug'  => $p->post_name,
        ], $layouts );
        \WP_CLI\Utils\format_items( 'table', $items, [ 'ID', 'title', 'slug' ] );
    }

    private function layout_type_to_post_type( string $type ): ?string {
        return match ( $type ) {
            'header' => 'et_header_layout',
            'footer' => 'et_footer_layout',
            'body'   => 'et_body_layout',
            default  => null,
        };
    }

    private function find_templates_by_use_on( string $use_on ): array {
        return get_posts([
            'post_type'      => 'et_template',
            'posts_per_page' => -1,
            'post_status'    => 'publish',
            'meta_key'       => '_et_use_on',
            'meta_value'     => $use_on,
        ]);
    }

    private function create_template( string $use_on, string $title ): int {
        if ( empty( $title ) ) {
            \WP_CLI::error( "--title is required when creating a new template." );
        }
        $template_id = wp_insert_post([
            'post_title'  => sanitize_text_field( $title ),
            'post_author' => 1,
            'post_type'   => 'et_template',
            'post_status' => 'publish',
        ]);
        update_post_meta( $template_id, '_et_autogenerated_title', '1' );
        update_post_meta( $template_id, '_et_default', '0' );
        update_post_meta( $template_id, '_et_enabled', '1' );
        delete_post_meta( $template_id, '_et_use_on' );
        add_post_meta( $template_id, '_et_use_on', $use_on );
        $this->register_template_with_theme_builder( $template_id );
        \WP_CLI::log( "  Created new Template ID {$template_id}." );
        return $template_id;
    }

    private function resolve_template_by_id( int $template_id ): void {
        $post = get_post( $template_id );
        if ( ! $post || $post->post_type !== 'et_template' ) {
            \WP_CLI::error( "Template ID {$template_id} not found or not an et_template." );
        }
        \WP_CLI::log( "  Template ID {$template_id} resolved." );
    }

    private function compile_and_insert_layout( int $layout_id, string $path, string $post_type, ?string $ds_path ): int {
        if ( ! file_exists( $path ) ) {
            \WP_CLI::error( "File not found: {$path}" );
        }

        $raw = file_get_contents( $path );
        $raw = ltrim( $raw, "\xEF\xBB\xBF" );
        $raw = trim( $raw );

        if ( $ds_path ) {
            $brand_vars_path = preg_replace( '#(design-system[\\\\/])?divitheme\.json$#', 'brand/_design_vars.json', $ds_path );
            if ( ! file_exists( $brand_vars_path ) ) {
                $brand_vars_path = null;
            }
            $resolver = new \DAC\Core\Design_Resolver( $ds_path, $brand_vars_path );
            $raw = $resolver->resolve_schema_string( $raw );
        }

        $validation_errors = $this->validate_schema_string( $raw );
        if ( ! empty( $validation_errors ) ) {
            foreach ( $validation_errors as $error ) {
                \WP_CLI::error( "Schema validation error: {$error}" );
            }
        }

        $engine = new \DAC\Core\Layout_Engine();
        $blocks = $engine->compile( $raw );

        $title = ( $layout_id > 0 ) ? get_the_title( $layout_id ) : "Global " . ucfirst( str_replace( 'et_', '', str_replace( '_layout', '', $post_type ) ) );

        $post_data = [
            'post_title'   => $title,
            'post_content' => wp_slash( $blocks ),
            'post_status'  => 'publish',
            'post_type'    => $post_type,
            'post_author'  => 1,
        ];

        if ( $layout_id > 0 ) {
            $post_data['ID'] = $layout_id;
            $post_id = wp_update_post( $post_data );
            \WP_CLI::log( "  Updated {$post_type} ID {$post_id}." );
        } else {
            $post_id = wp_insert_post( $post_data );
            \WP_CLI::log( "  Created {$post_type} ID {$post_id}." );
        }

        $this->apply_divi_meta( $post_id );
        return $post_id;
    }

    /**
     * Convenience wrapper: deploys header + footer + body in one command.
     *
     * For fine-grained control, use the atomic commands:
     *   template_create, template_ensure, template_find
     *   layout_deploy, layout_ensure
     *   template_wire
     *
     * Behaviour by --mode:
     *   create  Calls template_create + layout_deploy for each component.
     *           Fails if template (by --use-on) already exists.
     *   update  Calls layout_ensure for each component with provided IDs.
     *           Requires --header-id, --footer-id or --body-id.
     *   upsert  (default) Calls template_ensure + layout_ensure for each.
     *
     * ## OPTIONS
     *
     * [--header=<path>]
     * : Path to the Header combined JSON.
     *
     * [--footer=<path>]
     * : Path to the Footer combined JSON.
     *
     * [--body=<path>]
     * : Path to the Body combined JSON.
     *
     * [--design-system=<path>]
     * : Path to the design-system JSON file for token/preset resolution.
     *
     * [--mode=<mode>]
     * : Operation mode: create (default), update, or upsert. See description above.
     *
     * [--template-id=<id>]
     * : Target an existing et_template by ID.
     *
     * [--use-on=<scope>]
     * : Template scope (_et_use_on). Divi-recognised patterns:
     *   - 404                                  → 404 page
     *   - search                               → search results
     *   - homepage                             → front page
     *   - singular:post_type:<type>:all        → all posts of a type
     *   - singular:post_type:<type>:id:<id>    → specific post ID
     *   - singular:post_type:<type>:children:id:<id> → child posts
     *   - singular:taxonomy:<tax>:term:id:<id> → taxonomy term
     *   - archive:all                          → all archives
     *   - archive:post_type:<type>             → post type archive
     *   - archive:taxonomy:<tax>:all           → taxonomy archive
     *   - archive:taxonomy:<tax>:term:id:<id>  → term archive
     *   - archive:user:all                     → all authors
     *   - archive:user:id:<id>                 → specific author
     *   - archive:user:role:<role>             → author role
     *   - archive:date:all                     → date archives
     *
     * [--title=<title>]
     * : Title for the template. Required when creating (mode=create or mode=upsert).
     *
     * [--header-id=<id>]
     * : Target an existing et_header_layout by ID.
     *
     * [--footer-id=<id>]
     * : Target an existing et_footer_layout by ID.
     *
     * [--body-id=<id>]
     * : Target an existing et_body_layout by ID.
     *
     * [--header-enabled=<0|1>]
     * : Enable/disable header region on the template. Default: 1.
     *
     * [--footer-enabled=<0|1>]
     * : Enable/disable footer region on the template. Default: 1.
     *
     * [--body-enabled=<0|1>]
     * : Enable/disable body region on the template. Default: 1.
     *
     * [--header-global=<0|1>]
     * : Whether header layout is shared across templates. Default: 1.
     *
     * [--footer-global=<0|1>]
     * : Whether footer layout is shared across templates. Default: 1.
     *
     * [--body-global=<0|1>]
     * : Whether body layout is shared across templates. Default: 1.
     *
     * ## EXAMPLES
     *
     *     # Create new template for all pages (fails if use-on already exists)
     *     wp agentic deploy_global_ecosystem \
     *       --header="site/cristorey/page-defs/header/header-combined.json" \
     *       --footer="site/cristorey/page-defs/footer/footer-combined.json" \
     *       --body="site/cristorey/page-defs/body/body-combined.json" \
     *       --design-system="site/cristorey/design-system/divitheme.json" \
     *       --mode=create \
     *       --use-on="singular:post_type:page:all" \
     *       --title="Todas las páginas"
     *
     *     # Upsert: create or update by use-on match (safe default)
     *     wp agentic deploy_global_ecosystem \
     *       --header="site/cristorey/page-defs/header/header-combined.json" \
     *       --footer="site/cristorey/page-defs/footer/footer-combined.json" \
     *       --body="site/cristorey/page-defs/body/body-combined.json" \
     *       --use-on="singular:post_type:page:all" \
     *       --title="Todas las páginas"
     *
     *     # Update specific template by ID
     *     wp agentic deploy_global_ecosystem \
     *       --header="site/cristorey/page-defs/header/header-combined.json" \
     *       --footer="site/cristorey/page-defs/footer/footer-combined.json" \
     *       --body="site/cristorey/page-defs/body/body-combined.json" \
     *       --mode=update --template-id=123
     *
     *     # Update specific footer layout only
     *     wp agentic deploy_global_ecosystem \
     *       --header="site/cristorey/page-defs/header/header-combined.json" \
     *       --footer="site/cristorey/page-defs/footer/footer-combined.json" \
     *       --body="site/cristorey/page-defs/body/body-combined.json" \
     *       --mode=update --footer-id=456
     *
     *     # 404 template with body only (no header/footer)
     *     wp agentic deploy_global_ecosystem \
     *       --header="site/cristorey/page-defs/header/header-combined.json" \
     *       --footer="site/cristorey/page-defs/footer/footer-combined.json" \
     *       --body="site/cristorey/page-defs/body/body-combined.json" \
     *       --use-on="404" --title="Página 404" \
     *       --header-enabled=0 --footer-enabled=0
     *
     * @when after_wp_load
     */
    public function deploy_global_ecosystem( $args, $assoc_args ) {
        $mode = $assoc_args['mode'] ?? 'create';
        if ( ! in_array( $mode, [ 'create', 'update', 'upsert' ], true ) ) {
            \WP_CLI::error( "Invalid --mode: {$mode}. Use: create, update, or upsert." );
        }

        $ds_path     = $assoc_args['design-system'] ?? null;
        $use_on      = $assoc_args['use-on'] ?? '';
        $title       = $assoc_args['title'] ?? '';
        $template_id = isset( $assoc_args['template-id'] ) ? (int) $assoc_args['template-id'] : 0;

        // Resolve template
        if ( $template_id > 0 ) {
            $this->resolve_template_by_id( $template_id );
        } elseif ( $mode === 'create' ) {
            if ( empty( $use_on ) ) {
                \WP_CLI::error( "--use-on is required in create mode." );
            }
            $this->validate_use_on( $use_on );
            $existing = $this->find_templates_by_use_on( $use_on );
            if ( ! empty( $existing ) ) {
                \WP_CLI::error( "Template for '{$use_on}' already exists (ID {$existing[0]->ID})." );
            }
            if ( empty( $title ) ) {
                \WP_CLI::error( "--title is required in create mode." );
            }
            $template_id = $this->create_template( $use_on, $title );
        } elseif ( $mode === 'update' ) {
            if ( $template_id < 1 && empty( $use_on ) ) {
                \WP_CLI::error( "--mode=update requires --template-id or --use-on." );
            }
            if ( $template_id < 1 ) {
                $existing = $this->find_templates_by_use_on( $use_on );
                if ( count( $existing ) > 1 ) {
                    $ids = array_map( fn( $p ) => $p->ID, $existing );
                    \WP_CLI::error( "Multiple templates for '{$use_on}': IDs " . implode( ', ', $ids ) . '. Use --template-id.' );
                }
                if ( empty( $existing ) ) {
                    \WP_CLI::error( "No template found for '{$use_on}'. Use --mode=upsert or --mode=create." );
                }
                $template_id = $existing[0]->ID;
            }
            $this->resolve_template_by_id( $template_id );
        } else {
            // upsert
            if ( $template_id > 0 ) {
                $this->resolve_template_by_id( $template_id );
            } elseif ( ! empty( $use_on ) ) {
                $this->validate_use_on( $use_on );
                $existing = $this->find_templates_by_use_on( $use_on );
                if ( count( $existing ) > 1 ) {
                    $ids = array_map( fn( $p ) => $p->ID, $existing );
                    \WP_CLI::error( "Multiple templates for '{$use_on}': IDs " . implode( ', ', $ids ) . '. Use --template-id.' );
                }
                if ( ! empty( $existing ) ) {
                    $template_id = $existing[0]->ID;
                } else {
                    if ( empty( $title ) ) {
                        \WP_CLI::error( "--title is required when creating a new template." );
                    }
                    $template_id = $this->create_template( $use_on, $title );
                }
            } else {
                $template_id = $this->get_or_create_default_template();
            }
        }

        // Wire use-on to template if provided
        if ( ! empty( $use_on ) ) {
            delete_post_meta( $template_id, '_et_use_on' );
            add_post_meta( $template_id, '_et_use_on', $use_on );
        }

        // Deploy layouts
        $components = [
            'header' => [ 'post_type' => 'et_header_layout', 'id_key' => 'header-id' ],
            'footer' => [ 'post_type' => 'et_footer_layout', 'id_key' => 'footer-id' ],
            'body'   => [ 'post_type' => 'et_body_layout',   'id_key' => 'body-id' ],
        ];

        foreach ( $components as $key => $cfg ) {
            $specific_id = isset( $assoc_args[ $cfg['id_key'] ] ) ? (int) $assoc_args[ $cfg['id_key'] ] : 0;

            if ( $mode === 'create' ) {
                if ( $specific_id > 0 ) {
                    \WP_CLI::error( "--mode=create cannot target an existing layout. Omit --{$cfg['id_key']}." );
                }
                $layout_id = $this->compile_and_insert_layout( 0, $assoc_args[ $key ], $cfg['post_type'], $ds_path );
            } elseif ( $mode === 'update' ) {
                if ( $specific_id < 1 ) {
                    \WP_CLI::error( "--mode=update requires --{$cfg['id_key']} for the {$key} layout." );
                }
                $layout_id = $this->compile_and_insert_layout( $specific_id, $assoc_args[ $key ], $cfg['post_type'], $ds_path );
            } else {
                // upsert
                if ( $specific_id > 0 ) {
                    $layout_id = $this->compile_and_insert_layout( $specific_id, $assoc_args[ $key ], $cfg['post_type'], $ds_path );
                } else {
                    $referenced = $this->find_most_referenced_layout_id( $cfg['post_type'] );
                    if ( $referenced ) {
                        $layout_id = $this->compile_and_insert_layout( $referenced, $assoc_args[ $key ], $cfg['post_type'], $ds_path );
                    } else {
                        $lowest = $this->find_lowest_id_layout( $cfg['post_type'] );
                        if ( $lowest ) {
                            $layout_id = $this->compile_and_insert_layout( $lowest, $assoc_args[ $key ], $cfg['post_type'], $ds_path );
                        } else {
                            $layout_id = $this->compile_and_insert_layout( 0, $assoc_args[ $key ], $cfg['post_type'], $ds_path );
                        }
                    }
                }
            }

            update_post_meta( $template_id, "_et_{$key}_layout_id", $layout_id );
            update_post_meta( $template_id, "_et_{$key}_layout_enabled", $assoc_args[ "{$key}-enabled" ] ?? '1' );
        }

        if ( function_exists( 'et_core_clear_wp_cache' ) ) {
            et_core_clear_wp_cache();
        }

        \WP_CLI::success( "Ecosystem deployed: template ID {$template_id}." );
    }

    private function get_or_create_default_template() {
        $templates = get_posts([
            'post_type'  => 'et_template',
            'meta_key'   => '_et_default',
            'meta_value' => '1',
            'posts_per_page' => 1
        ]);

        if ( ! empty( $templates ) ) return $templates[0]->ID;

        $template_id = wp_insert_post([
            'post_title'  => 'Default Website Template',
            'post_author' => 1,
            'post_type'   => 'et_template',
            'post_status' => 'publish'
        ]);
        update_post_meta( $template_id, '_et_default', '1' );
        return $template_id;
    }

    private function register_template_with_theme_builder( int $template_id ): void {
        if ( ! defined( 'ET_THEME_BUILDER_THEME_BUILDER_POST_TYPE' ) ) {
            return;
        }
        $tb_query = new \WP_Query([
            'post_type'              => ET_THEME_BUILDER_THEME_BUILDER_POST_TYPE,
            'post_status'            => 'publish',
            'posts_per_page'         => 1,
            'orderby'                => 'date',
            'order'                  => 'desc',
            'fields'                 => 'ids',
            'no_found_rows'          => true,
            'update_post_meta_cache' => false,
            'update_post_term_cache' => false,
            'meta_key'               => '_et_library_theme_builder',
            'meta_compare'           => 'NOT EXISTS',
        ]);

        if ( empty( $tb_query->posts ) ) {
            return;
        }

        $tb_id = $tb_query->posts[0];
        $existing = get_post_meta( $tb_id, '_et_template', false );

        if ( ! in_array( (string) $template_id, $existing, true ) ) {
            add_post_meta( $tb_id, '_et_template', (string) $template_id );
            \WP_CLI::log( "Registered template {$template_id} with Theme Builder post {$tb_id}." );
        }
    }

    private function validate_use_on( string $value ): void {
        $patterns = [
            '/^(404|search|homepage)$/',
            '/^singular:post_type:[a-z_]+:(all|id:\d+|children:id:\d+)$/',
            '/^singular:taxonomy:[a-z_]+:term:id:\d+$/',
            '/^archive:(all|post_type:[a-z_]+|date:all|user:(all|id:\d+|role:\w+))$/',
            '/^archive:taxonomy:[a-z_]+:(all|term:id:\d+)$/',
        ];

        foreach ( $patterns as $pattern ) {
            if ( preg_match( $pattern, $value ) ) {
                return;
            }
        }

        \WP_CLI::error( "Invalid --use-on value: '{$value}'. Must be a valid Divi Theme Builder condition (e.g., '404', 'singular:post_type:page:all', 'archive:post_type:post')." );
    }

    private function apply_divi_meta( $post_id ) {
        update_post_meta( $post_id, '_et_pb_use_builder', 'on' );
        update_post_meta( $post_id, '_et_pb_use_divi_5', 'on' );
        update_post_meta( $post_id, '_et_pb_show_page_creation', 'off' );
        update_post_meta( $post_id, '_et_pb_built_for_post_type', 'page' );
        update_post_meta( $post_id, '_et_pb_gutter_width', '3' );
        update_post_meta( $post_id, '_et_pb_enable_shortcode_tracking', '' );
        update_post_meta( $post_id, '_et_pb_custom_css', '' );
        update_post_meta( $post_id, '_et_pb_first_image', '' );
        update_post_meta( $post_id, '_et_pb_truncate_post', '' );
        update_post_meta( $post_id, '_et_pb_truncate_post_date', '' );
        update_post_meta( $post_id, '_et_builder_version', DIVI_BUILDER_VERSION );
        delete_post_meta( $post_id, '_et_theme_builder_marked_as_unused' );
    }

    private function find_most_referenced_layout_id( string $type ): ?int {
        $meta_key = [
            'et_header_layout' => '_et_header_layout_id',
            'et_footer_layout' => '_et_footer_layout_id',
            'et_body_layout'   => '_et_body_layout_id',
        ][ $type ] ?? '';

        if ( empty( $meta_key ) ) {
            return null;
        }

        global $wpdb;
        $results = $wpdb->get_results( $wpdb->prepare(
            "SELECT meta_value, COUNT(*) as cnt FROM {$wpdb->postmeta}
             WHERE meta_key = %s AND meta_value != ''
             GROUP BY meta_value
             ORDER BY cnt DESC
             LIMIT 1",
            $meta_key
        ) );

        if ( ! empty( $results ) ) {
            $id = (int) $results[0]->meta_value;
            if ( get_post_type( $id ) === $type ) {
                return $id;
            }
        }

        return null;
    }

    /**
     * Syncs brand CSS + design tokens to WordPress Custom CSS (wp_update_custom_css_post).
     *
     * Reads brand.css from the active brand directory, generates CSS custom properties
     * from divitheme.json, concatenates both, and stores them in the WordPress database
     * via the Customizer API. This survives production deploys — no filesystem dependency.
     *
     * ## OPTIONS
     *
     * [--site=<site>]
     * : Brand site name (defaults to DAW_SITE env).
     *
     * @when after_wp_load
     */
    public function sync_css( $args, $assoc_args ) {
        $site = $assoc_args['site'] ?? ( function_exists( 'daw_get_active_site' ) ? \daw_get_active_site() : getenv( 'DAW_SITE' ) );
        if ( empty( $site ) ) {
            \WP_CLI::error( 'DAW_SITE not set. Pass --site=<name> or set DAW_SITE env.' );
        }

        $daw_root = dirname( DIVI_AGENTIC_CORE_DIR );

        // 1. Verify brand.css exists on disk (file-based enqueue is now the source of truth)
        $brand_css_paths = [
            $daw_root . '/divi-agentic-core/assets/css/brand.css',
            $daw_root . '/site/' . $site . '/brand/assets/css/brand.css',
        ];
        $found = false;
        foreach ( $brand_css_paths as $p ) {
            if ( file_exists( $p ) ) {
                $brand_css = file_get_contents( $p );
                \WP_CLI::log( "brand.css (" . strlen( $brand_css ) . " chars) found at: {$p}" );
                $found = true;
                break;
            }
        }
        if ( ! $found ) {
            \WP_CLI::warning( 'brand.css not found at any expected path — enqueue will be skipped at runtime.' );
        }

        // Verify design tokens source exists
        $ds_path = $daw_root . '/site/' . $site . '/design-system/divitheme.json';
        if ( file_exists( $ds_path ) ) {
            \WP_CLI::log( "Design system found: {$ds_path}" );
        } else {
            \WP_CLI::warning( "Design system not found: {$ds_path}" );
        }

        // 2. Clean up legacy DB storage — brand.css is now enqueued from disk
        // Remove Divi legacy et_custom_css (stale from previous brands)
        delete_option( 'et_custom_css' );
        \WP_CLI::log( 'Cleaned up et_custom_css legacy option.' );

        // Remove WP native Custom CSS post content to avoid duplication
        // with the file-enqueued brand.css
        if ( function_exists( 'wp_get_custom_css_post' ) ) {
            $post = wp_get_custom_css_post();
            if ( $post ) {
                // Clear the content — keep the post but remove redundant CSS
                // (enqueued brand.css is now the source of truth)
                wp_update_custom_css_post( '' );
                \WP_CLI::log( 'Cleared WordPress Custom CSS post content (brand.css is now enqueued from disk).' );
            }
        }

        \WP_CLI::success( 'CSS flow synchronized: file-based enqueue is active, legacy DB storage removed.' );
    }

    /**
     * Exports a WordPress page of Divi 5 blocks into a schema JSON.
     *
     * ## OPTIONS
     *
     * --slug=<slug>
     * : The slug of the page to export.
     *
     * [--brand=<brand>]
     * : The brand directory to save to (defaults to env DAW_SITE or 'bibliotheca').
     *
     * [--dest=<path>]
     * : Override destination file path.
     *
     * @when after_wp_load
     */
    public function export_page( $args, $assoc_args ) {
        $slug = $assoc_args['slug'] ?? '';
        if ( empty( $slug ) ) {
            \WP_CLI::error( "Please specify --slug=<slug>" );
        }

        // Determine brand from env DAW_SITE, --brand arg, or .env
        $brand = $assoc_args['brand'] ?? getenv( 'DAW_SITE' );
        if ( empty( $brand ) ) {
            $brand = 'bibliotheca';
            \WP_CLI::warning( "DAW_SITE not set in environment or .env — defaulting to 'bibliotheca'. Set DAW_SITE=<brand> in .env to target a different brand." );
        }

        // Paths
        $daw_root = dirname( DIVI_AGENTIC_CORE_DIR );
        $ds_path  = $daw_root . DIRECTORY_SEPARATOR . 'site' . DIRECTORY_SEPARATOR . $brand . DIRECTORY_SEPARATOR . 'design-system' . DIRECTORY_SEPARATOR . 'divitheme.json';
        
        $dest_path = $assoc_args['dest'] ?? '';
        if ( empty( $dest_path ) ) {
            $dest_path = $daw_root . DIRECTORY_SEPARATOR . 'site' . DIRECTORY_SEPARATOR . $brand . DIRECTORY_SEPARATOR . 'page-defs' . DIRECTORY_SEPARATOR . $slug . '.json';
        }

        // Normalize paths
        $dest_path = str_replace( '/', DIRECTORY_SEPARATOR, $dest_path );

        \WP_CLI::log( "Exporting page '{$slug}' for brand '{$brand}'..." );
        if ( file_exists( $ds_path ) ) {
            \WP_CLI::log( "Using design system tokens from: {$ds_path}" );
        } else {
            \WP_CLI::warning( "Design system not found at: {$ds_path}. Hex colors won't be reverse-resolved." );
            $ds_path = null;
        }

        // Find post by slug
        $page = get_page_by_path( $slug, OBJECT, 'page' );
        if ( ! $page ) {
            \WP_CLI::error( "Page not found in WordPress with slug: {$slug}" );
        }

        try {
            // Convert blocks to schema
            require_once dirname( __DIR__ ) . '/core/class-blocks-to-schema.php';
            $exporter = new \DAC\Core\BlocksToSchema( $ds_path );
            $schema   = $exporter->convert( $page->post_content );
        } catch ( \Throwable $e ) {
            \WP_CLI::error( "Conversion error: " . $e->getMessage() . "\n" . $e->getTraceAsString() );
        }

        // Add page level parameters
        $schema = array_merge( [
            'title' => $page->post_title,
            'slug'  => $page->post_name,
        ], $schema );

        // Save
        $dest_dir = dirname( $dest_path );
        if ( ! is_dir( $dest_dir ) ) {
            mkdir( $dest_dir, 0777, true );
        }

        $json_data = json_encode( $schema, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES );
        if ( false === file_put_contents( $dest_path, $json_data ) ) {
            \WP_CLI::error( "Failed to write schema to: {$dest_path}" );
        }

        \WP_CLI::success( "Page '{$page->post_title}' exported successfully to: {$dest_path}" );
    }

    /**
     * Validate schema string for allowed blocks only.
     * Design classes are no longer validated — visual properties
     * are expressed as Divi 5 native decoration attributes.
     */
    private function validate_schema_string( string $raw ): array {
        $errors = [];

        // Build allowlist: native Divi blocks + modules registered via Module_Registry.
        if ( empty( $this->allowed_blocks ) ) {
            $custom_blocks = [];
            if ( class_exists( '\DAC\Core\Module_Registry' ) ) {
                $custom_blocks = \DAC\Core\Module_Registry::get_allowed_blocks();
            }
            $this->allowed_blocks = array_merge( $this->native_blocks, $custom_blocks );
        }

        $schema = json_decode( $raw, true );
        if ( json_last_error() !== JSON_ERROR_NONE ) {
            return [ "Invalid JSON: " . json_last_error_msg() ];
        }
        if ( ! isset( $schema['sections'] ) || ! is_array( $schema['sections'] ) ) {
            return [ "Schema must have a 'sections' array" ];
        }
        foreach ( $schema['sections'] as $sec_idx => $section ) {
            if ( isset( $section['rows'] ) && is_array( $section['rows'] ) ) {
                foreach ( $section['rows'] as $row_idx => $row ) {
                    if ( isset( $row['columns'] ) && is_array( $row['columns'] ) ) {
                        foreach ( $row['columns'] as $col_idx => $column ) {
                            if ( isset( $column['modules'] ) && is_array( $column['modules'] ) ) {
                                foreach ( $column['modules'] as $mod_idx => $module ) {
                                    $block = $module['_type'] ?? (is_string($module['module'] ?? null) ? $module['module'] : '');
                                    if ( $block && ! in_array( $block, $this->allowed_blocks, true ) ) {
                                        // Allow any divi/*, dac/* or dgpc/* prefixed block (custom/third-party modules)
                                        if ( str_starts_with( $block, 'divi/' ) || str_starts_with( $block, 'dac/' ) || str_starts_with( $block, 'dgpc/' ) ) {
                                            $this->allowed_blocks[] = $block;
                                        } else {
                                            $errors[] = "Block '{$block}' is not allowed at section {$sec_idx}, row {$row_idx}, column {$col_idx}, module {$mod_idx}";
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        return $errors;
    }
}
