<?php
namespace DAC\Core;

require_once __DIR__ . '/trait-module-metadata.php';
require_once __DIR__ . '/renderers/trait-block-helpers.php';

/**
 * Layout Engine v12.1 — Divi 5.7.4 Native Render (Metadata-Driven)
 *
 * Pure structural compiler: receives a pre-resolved schema and maps it
 * to Divi 5 blocks. Uses official Divi 5 metadata for serialization paths.
 *
 * All design resolution happens BEFORE this engine runs, via Design_Resolver.
 */
class Layout_Engine {
    use \Module_Metadata;
    use \Divi_Agentic_Core\Core\Renderers\Block_Helpers;

    private string $d5_version = DIVI_BUILDER_VERSION;

    public function compile( $schema ): string {
        if ( is_string( $schema ) ) {
            $schema = str_replace( '{{SITE_URL}}', get_site_url(), $schema );
            $schema = str_replace( '{{SITE_NAME}}', get_bloginfo( 'name' ), $schema );

            $schema = ltrim( $schema, "\xEF\xBB\xBF" );
            $schema = trim( $schema );

            $decoded = json_decode( $schema, true );
            if ( json_last_error() !== JSON_ERROR_NONE ) {
                $enc = mb_detect_encoding( $schema, 'UTF-8,Windows-1252,ISO-8859-1', true );
                $schema = mb_convert_encoding( $schema, 'UTF-8', $enc ?: 'Windows-1252' );
                $decoded = json_decode( $schema, true );
                if ( json_last_error() !== JSON_ERROR_NONE ) {
                    \WP_CLI::error( "JSON Decode Error: " . json_last_error_msg() );
                    return '';
                }
            }
            $schema = $decoded;
        }
        if ( ! isset( $schema['sections'] ) ) return '';

        $output = "";
        foreach ( $schema['sections'] as $section ) {
            $output .= $this->render_block( 'divi/section', $section, 'rows' );
        }

        return $output;
    }

    private function render_block( string $block_name, array $data, string $content_key = '' ): string {
        $mapping = [
            'core/paragraph' => 'divi/text',
            'core/heading'   => 'divi/text',
            'core/image'     => 'divi/image',
            'core/button'    => 'divi/button',
            'core/quote'     => 'divi/text',
            'core/list'      => 'divi/text',
            'et_pb_text'     => 'divi/text',
            'et_pb_image'    => 'divi/image',
            'et_pb_button'   => 'divi/button'
        ];

        $slug = $mapping[$block_name] ?? $block_name;

        if ( $slug === 'divi/row-inner' ) {
            $content_key = 'columns-inner';
        } elseif ( $slug === 'divi/column-inner' ) {
            $content_key = 'modules';
        }

        $content = '';
        $inner_html = '';

        // Render children FIRST so they propagate into contact-form, slider, accordion, etc.
        $children_html = '';
        if ( isset( $data['children'] ) && is_array( $data['children'] ) ) {
            foreach ( $data['children'] as $child ) {
                $child_type = $child['_type'] ?? (is_string($child['module'] ?? null) ? $child['module'] : null) ?? $child['type'] ?? 'divi/contact-field';
                $child_key = '';
                if ( in_array( $child_type, [ 'divi/column', 'divi/column-inner' ], true ) ) {
                    $child_key = 'modules';
                } elseif ( in_array( $child_type, [ 'divi/row', 'divi/row-inner', 'divi/group', 'divi/group-carousel' ], true ) ) {
                    $child_key = 'columns';
                }
                $children_html .= $this->render_block( $child_type, $child, $child_key );
            }
        }

        $attrs = [
            'builderVersion' => $this->d5_version,
            'module' => []
        ];

        $is_divi = strpos( $slug, 'divi/' ) === 0;

        $is_divi = strpos( $slug, 'divi/' ) === 0;

        $attrs = [
            'builderVersion' => $this->d5_version,
            'module' => []
        ];

        // --- DGPCommerce Product Carousel: custom third-party block ---
        // Handled early because it is NOT a native Divi 5 block; it stores
        // its settings as top-level attrs alongside a module{} decoration.
        if ( $slug === 'dgpc/product-carousel' ) {
            $renderer = new \Divi_Agentic_Core\Core\Renderers\Dgpc_Renderer( $this->d5_version );
            $result = $renderer->render( $slug, $data, $content_key, $children_html );
            $attrs  = $result['attrs'];
            $inner  = $result['inner'];
            $inner_html = $result['inner_html'];

            // Preserve the original type attr so the block is recognized by the plugin.
            if ( ! isset( $attrs['type'] ) ) {
                $attrs['type'] = 'dgpc/product-carousel';
            }

            // Apply shared post-processing (gcid, gradient, background) and serialize.
            $attrs = self::convert_gcid_to_variable_syntax( $attrs );
            $attrs = self::normalize_gradient_stops( $attrs );
            $attrs = self::normalize_empty_background( $attrs );

            $json_attrs = json_encode( $attrs, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES );
            return "<!-- wp:{$slug} {$json_attrs} -->\n{$inner}{$inner_html}<!-- /wp:{$slug} -->\n";
        } elseif ( $slug === 'dgbm_blog_module' ) {
            $renderer = new \Divi_Agentic_Core\Core\Renderers\Dgbm_Renderer();
            $result = $renderer->render( $slug, $data, $content_key, $children_html );
            $shortcode = $result['inner_html'];

            $wrapper_attrs = [
                'shortcodeName' => 'dgbm_blog_module',
                'nonconvertible' => 'yes',
                'innerHTML'     => $shortcode,
            ];

            $json_attrs = json_encode( $wrapper_attrs, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_HEX_QUOT );
            return "<!-- wp:divi/shortcode-module {$json_attrs} -->\n{$shortcode}\n<!-- /wp:divi/shortcode-module -->\n";
        } elseif ( $is_divi ) {
            // --- GROUP 1: Structural containers ---
            $structural_slugs = [ 'divi/section', 'divi/row', 'divi/column', 'divi/column-inner' ];
            if ( in_array( $slug, $structural_slugs, true ) ) {
                $renderer = new \Divi_Agentic_Core\Core\Renderers\Divi_Structural_Renderer();
            } else {
                $renderer = $this->resolve_divi_renderer( $slug );
            }

            $result     = $renderer->render( $slug, $data, $content_key, $children_html );
            $attrs      = $result['attrs'];
            $inner      = $result['inner'] ?? '';
            $inner_html = $result['inner_html'] ?? '';

            // Pass through navigation/control block-level attributes not handled by renderers
            foreach ( [ 'arrows', 'pagination', 'dotNav' ] as $key ) {
                if ( isset( $data[ $key ] ) && ! isset( $attrs[ $key ] ) ) {
                    $attrs[ $key ] = $data[ $key ];
                }
            }
        }

        // Children from content_key (rows, columns, modules)
        $items_to_render = [];
        if ( $is_divi && $content_key ) {
            if ( $content_key === 'columns-inner' && isset( $data['columns'] ) ) {
                $items_to_render = $data['columns'];
            } elseif ( isset( $data[ $content_key ] ) ) {
                $items_to_render = $data[ $content_key ];
            }
        }

        if ( ! empty( $items_to_render ) ) {
            foreach ( $items_to_render as $item ) {
                switch ( $content_key ) {
                    case 'rows':
                        $content .= $this->render_block( 'divi/row', $item, 'columns' );
                        break;
                    case 'columns':
                        $content .= $this->render_block( 'divi/column', $item, 'modules' );
                        break;
                    case 'columns-inner':
                        $content .= $this->render_block( 'divi/column-inner', $item, 'modules' );
                        break;
                    case 'modules':
                        $module_type = $item['_type'] ?? (is_string($item['module'] ?? null) ? $item['module'] : null) ?? $item['type'] ?? 'divi/text';
                        $children_key = in_array( $module_type, [
                            'divi/row', 'divi/row-inner', 'divi/group', 'divi/group-carousel'
                        ], true ) ? 'columns' : '';
                        $content .= $this->render_block( $module_type, $item, $children_key );
                        break;
                }
            }
        }

        // Convert var(--gcid-*) to $variable() syntax for Divi 5 VB recognition.
        // The frontend resolver (resolve_dynamic_variable) converts it back.
        $attrs = self::convert_gcid_to_variable_syntax( $attrs );

        // Normalize gradient stop positions: strip trailing % if present.
        $attrs = self::normalize_gradient_stops( $attrs );

        // Fix: Ensure no "value":[] exists in any background.
        $attrs = self::normalize_empty_background( $attrs );

        if ( $attrs['module'] === [] ) { unset( $attrs['module'] ); }

        $json_attrs = json_encode( $attrs, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES );

        $inner = ( $content !== '' || $inner_html !== '' ) ? "{$content}{$inner_html}" : '';
        return "<!-- wp:{$slug} {$json_attrs} -->\n{$inner}<!-- /wp:{$slug} -->\n";
    }

    /**
     * Resolve a Divi block slug to its dedicated renderer.
     *
     * @param string $slug Resolved block slug.
     * @return \Divi_Agentic_Core\Core\Renderers\Block_Renderer_Interface
     */
    private function resolve_divi_renderer( string $slug ): \Divi_Agentic_Core\Core\Renderers\Block_Renderer_Interface {
        $text_slugs = [
            'divi/text', 'divi/code', 'divi/heading',
            'divi/fullwidth-code', 'divi/shortcode-module',
        ];
        if ( in_array( $slug, $text_slugs, true ) ) {
            return new \Divi_Agentic_Core\Core\Renderers\Divi_Text_Renderer();
        }
        if ( $slug === 'divi/button' ) {
            return new \Divi_Agentic_Core\Core\Renderers\Divi_Button_Renderer();
        }

        $media_slugs = [
            'divi/image', 'divi/fullwidth-image', 'divi/video', 'divi/audio',
            'divi/gallery', 'divi/lottie', 'divi/svg',
        ];
        if ( in_array( $slug, $media_slugs, true ) ) {
            return new \Divi_Agentic_Core\Core\Renderers\Divi_Media_Renderer();
        }

        $form_slugs = [
            'divi/contact-form', 'divi/contact-field', 'divi/login',
            'divi/subscribe', 'divi/search',
        ];
        if ( in_array( $slug, $form_slugs, true ) ) {
            return new \Divi_Agentic_Core\Core\Renderers\Divi_Form_Renderer();
        }

        $content_slugs = [
            'divi/blurb',
            'divi/number-counter', 'divi/counter', 'divi/circle-counter',
            'divi/icon', 'divi/toggle',
            'divi/accordion-item', 'divi/slide', 'divi/tab', 'divi/video-slider-item',
            'divi/cta', 'divi/testimonial', 'divi/team-member', 'divi/pricing-table',
            'divi/fullwidth-header', 'divi/countdown-timer',
        ];
        if ( in_array( $slug, $content_slugs, true ) ) {
            return new \Divi_Agentic_Core\Core\Renderers\Divi_ContentModule_Renderer();
        }

        $container_slugs = [
            'divi/menu', 'divi/fullwidth-menu',
            'divi/row-inner', 'divi/group', 'divi/group-carousel',
            'divi/timeline',
            'divi/global-layout', 'divi/layout', 'divi/placeholder',
            'divi/slider', 'divi/video-slider', 'divi/accordion',
            'divi/tabs', 'divi/social-media-follow', 'divi/icon-list',
            'divi/fullwidth-slider', 'divi/pricing-tables', 'divi/fullwidth-portfolio',
        ];
        if ( in_array( $slug, $container_slugs, true ) ) {
            return new \Divi_Agentic_Core\Core\Renderers\Divi_Container_Renderer();
        }

        $dynamic_slugs = [
            'divi/post-title', 'divi/post-content', 'divi/post-nav',
            'divi/comments', 'divi/fullwidth-post-title', 'divi/fullwidth-post-content',
        ];
        if ( in_array( $slug, $dynamic_slugs, true ) ) {
            return new \Divi_Agentic_Core\Core\Renderers\Divi_Dynamic_Renderer();
        }

        if ( strpos( $slug, 'divi/woocommerce-' ) === 0 || $slug === 'divi/shop' ) {
            return new \Divi_Agentic_Core\Core\Renderers\Divi_Woo_Renderer();
        }

        return new \Divi_Agentic_Core\Core\Renderers\Divi_Generic_Renderer();
    }
}

