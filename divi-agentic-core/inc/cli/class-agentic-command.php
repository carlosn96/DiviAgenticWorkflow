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
            $resolver = new \DAC\Core\Design_Resolver( $assoc_args['design-system'] );
            $raw = $resolver->resolve_schema_string( $raw );
            \WP_CLI::log( "Design tokens resolved from: {$assoc_args['design-system']}" );
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
