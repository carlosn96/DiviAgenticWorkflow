<?php
namespace DAC\CLI;

/**
 * Agentic Command v3.0 — Deploys pages and global layouts with Divi 5.5.0.
 *
 * Validates schema blocks, resolves design tokens via Design_Resolver,
 * then compiles to Divi 5 blocks via Layout_Engine.
 */
class Agentic_Command {

    private array $allowed_blocks = [
        // Structure
        'divi/section', 'divi/row', 'divi/column', 'divi/row-inner', 'divi/column-inner',
        // Content
        'divi/text', 'divi/image', 'divi/button', 'divi/code', 'divi/video',
        'divi/audio', 'divi/heading', 'divi/icon', 'divi/link', 'divi/divider',
        'divi/gallery', 'divi/breadcrumbs',
        // Interactive
        'divi/menu', 'divi/toggle', 'divi/accordion', 'divi/accordion-item',
        'divi/tabs', 'divi/tab', 'divi/dropdown',
        'divi/contact-form', 'divi/contact-field', 'divi/contact-form-7',
        'divi/signup', 'divi/signup-custom-field',
        // Social
        'divi/social-media-follow', 'divi/social-media-follow-network',
        // Dynamic
        'divi/blog', 'divi/post-title', 'divi/post-content', 'divi/post-nav',
        'divi/post-slider', 'divi/comments', 'divi/search',
        // Design
        'divi/blurb', 'divi/cta', 'divi/pricing-table', 'divi/pricing-tables',
        'divi/team-member', 'divi/testimonial', 'divi/icon-list', 'divi/icon-list-item',
        'divi/lottie', 'divi/before-after-image', 'divi/canvas-portal', 'divi/svg',
        // Counters
        'divi/number-counter', 'divi/counter', 'divi/counters',
        'divi/circle-counter',
        // Sliders
        'divi/slider', 'divi/slide', 'divi/video-slider', 'divi/video-slider-item',
        // Fullwidth
        'divi/fullwidth-code', 'divi/fullwidth-header', 'divi/fullwidth-image',
        'divi/fullwidth-map', 'divi/fullwidth-menu', 'divi/fullwidth-portfolio',
        'divi/fullwidth-post-content', 'divi/fullwidth-post-slider',
        'divi/fullwidth-post-title', 'divi/fullwidth-slider',
        // Special
        'divi/group', 'divi/group-carousel', 'divi/global-layout',
        'divi/portfolio', 'divi/filterable-portfolio', 'divi/sidebar',
        'divi/login', 'divi/countdown-timer', 'divi/map', 'divi/map-pin',
        'divi/shortcode-module', 'divi/placeholder', 'divi/layout',
        // WooCommerce
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
            $customizer_slots = [
                'primary'   => 'gcid-primary-color',
                'secondary' => 'gcid-secondary-color',
                'heading'   => 'gcid-heading-color',
                'body'      => 'gcid-body-color',
                'link'      => 'gcid-link-color',
            ];
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

            $resolver = new \DAC\Core\Design_Resolver( $assoc_args['design-system'] );
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
     * Deploys the Global Theme Builder Ecosystem.
     *
     * ## OPTIONS
     *
     * --header=<path>
     * : Path to the Header JSON.
     *
     * --footer=<path>
     * : Path to the Footer JSON.
     *
     * --body=<path>
     * : Path to the Body JSON.
     *
     * [--design-system=<path>]
     * : Path to the design-system JSON file for token/preset resolution.
     *
     * @when after_wp_load
     */
    public function deploy_global_ecosystem( $args, $assoc_args ) {
        $engine = new \DAC\Core\Layout_Engine();

        $ds_path = $assoc_args['design-system'] ?? null;

        // 1. Get or Create Default Template
        $template_id = $this->get_or_create_default_template();
        \WP_CLI::log( "Using Default Template ID: {$template_id}" );

        // 2. Deploy Header
        $header_id = $this->deploy_tb_component( $assoc_args['header'], 'et_header_layout', 'Global Header', $ds_path );
        update_post_meta( $template_id, '_et_header_layout_id', $header_id );
        update_post_meta( $template_id, '_et_header_layout_enabled', '1' );

        // 3. Deploy Footer
        $footer_id = $this->deploy_tb_component( $assoc_args['footer'], 'et_footer_layout', 'Global Footer', $ds_path );
        update_post_meta( $template_id, '_et_footer_layout_id', $footer_id );
        update_post_meta( $template_id, '_et_footer_layout_enabled', '1' );

        // 4. Deploy Body
        $body_id = $this->deploy_tb_component( $assoc_args['body'], 'et_body_layout', 'Global Body', $ds_path );
        update_post_meta( $template_id, '_et_body_layout_id', $body_id );
        update_post_meta( $template_id, '_et_body_layout_enabled', '1' );

        if ( function_exists( 'et_core_clear_wp_cache' ) ) {
            et_core_clear_wp_cache();
        }

        \WP_CLI::success( "Global Theme Builder Ecosystem fully reconstructed!" );
    }

    private function deploy_tb_component( $path, $type, $title, $ds_path = null ) {
        if ( ! file_exists( $path ) ) \WP_CLI::error( "File not found: {$path}" );

        $raw = file_get_contents( $path );

        if ( $ds_path ) {
            $resolver = new \DAC\Core\Design_Resolver( $ds_path );
            $raw = $resolver->resolve_schema_string( $raw );
        }

        $engine = new \DAC\Core\Layout_Engine();
        $blocks = $engine->compile( $raw );

        // Find existing to avoid duplicates in TB — use post_type only, not title
        $existing = get_posts([
            'post_type'      => $type,
            'posts_per_page' => 1,
            'post_status'    => 'publish',
            'orderby'        => 'ID',
            'order'          => 'ASC'
        ]);

        $post_data = [
            'post_title'   => sanitize_text_field( $title ),
            'post_content' => wp_slash( $blocks ),
            'post_status'  => 'publish',
            'post_type'    => $type,
            'post_author'  => 1,
        ];

        if ( ! empty( $existing ) ) {
            $post_data['ID'] = $existing[0]->ID;
            $post_id = wp_update_post( $post_data );
            \WP_CLI::log( "Updated {$type} ID: {$post_id}" );
        } else {
            $post_id = wp_insert_post( $post_data );
            \WP_CLI::log( "Created {$type} ID: {$post_id}" );
        }

        $this->apply_divi_meta( $post_id );
        return $post_id;
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

    private function apply_divi_meta( $post_id ) {
        update_post_meta( $post_id, '_et_pb_use_builder', 'on' );
        update_post_meta( $post_id, '_et_pb_use_divi_5', 'on' );
        update_post_meta( $post_id, '_et_pb_show_page_creation', 'off' );
        update_post_meta( $post_id, '_et_pb_built_with_d5', '1' );
        update_post_meta( $post_id, '_et_builder_version', '5.5.0' );
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

        // 1. Read brand.css
        $brand_css_path = $daw_root . '/site/' . $site . '/brand/assets/css/brand.css';
        $brand_css = '';
        if ( file_exists( $brand_css_path ) ) {
            $brand_css = file_get_contents( $brand_css_path );
            \WP_CLI::log( "Loaded brand CSS (" . strlen( $brand_css ) . " chars) from: {$brand_css_path}" );
        } else {
            \WP_CLI::warning( "brand.css not found at: {$brand_css_path}" );
        }

        // 2. Generate CSS vars from design system
        $ds_path = $daw_root . '/site/' . $site . '/design-system/divitheme.json';
        $css_vars = '';
        if ( file_exists( $ds_path ) ) {
            $vars = \daw_generate_css_vars( $ds_path );
            if ( $vars ) {
                $css_vars = $vars;
            }
        } else {
            \WP_CLI::warning( "Design system not found at: {$ds_path}" );
        }

        // 3. Concatenate: brand.css first, then CSS vars (CSS vars override via :root specificity)
        $combined = '';
        if ( $brand_css ) {
            $combined .= "/*** DAW Brand CSS ***/\n" . $brand_css . "\n\n";
        }
        if ( $css_vars ) {
            $combined .= "/*** DAW Design Tokens ***/\n" . $css_vars . "\n";
        }

        if ( empty( $combined ) ) {
            \WP_CLI::error( 'Nothing to sync — no brand.css and no design system found.' );
        }

        // 4. Store in WordPress Custom CSS (wp_update_custom_css_post)
        if ( function_exists( 'wp_update_custom_css_post' ) ) {
            $result = wp_update_custom_css_post( $combined );
            if ( is_wp_error( $result ) ) {
                \WP_CLI::error( 'Failed to update custom CSS: ' . $result->get_error_message() );
            }
            \WP_CLI::success( 'Brand CSS + design tokens synced to WordPress Custom CSS (' . strlen( $combined ) . ' chars).' );
        } else {
            \WP_CLI::error( 'wp_update_custom_css_post() not available. Are you on WP 4.7+?' );
        }
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
                                    $block = $module['module'] ?? '';
                                    if ( $block && ! in_array( $block, $this->allowed_blocks, true ) ) {
                                        $errors[] = "Block '{$block}' is not allowed at section {$sec_idx}, row {$row_idx}, column {$col_idx}, module {$mod_idx}";
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
