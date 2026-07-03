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

    private string $d5_version = '5.7.4';

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
                $children_html .= $this->render_block( $child_type, $child, '' );
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

            // Apply shared post-processing (gcid, gradient, background) and serialize.
            $attrs = self::convert_gcid_to_variable_syntax( $attrs );
            $attrs = self::normalize_gradient_stops( $attrs );
            $attrs = self::normalize_empty_background( $attrs );

            if ( $attrs['module'] === [] ) { $attrs['module'] = (object)[]; }

            $json_attrs = json_encode( $attrs, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES );
            return "<!-- wp:{$slug} {$json_attrs} -->\n{$inner}{$inner_html}<!-- /wp:{$slug} -->\n";
        } elseif ( $is_divi ) {
            // --- GROUP 1: Structural containers ---
            $structural_slugs = [ 'divi/section', 'divi/row', 'divi/column', 'divi/column-inner' ];
            if ( in_array( $slug, $structural_slugs, true ) ) {
                $renderer = new \Divi_Agentic_Core\Core\Renderers\Divi_Structural_Renderer();
                $result   = $renderer->render( $slug, $data, $content_key, $children_html );
                $attrs    = $result['attrs'];
            } else {
                // Base attrs preparation for remaining Divi blocks.
                $base  = new \Divi_Agentic_Core\Core\Renderers\Divi_Base_Renderer();
                $attrs = $base->prepare_base_attrs( $data, $this->d5_version );

                // ---------------------------------------------------------------
                // BLOCK-SPECIFIC HANDLERS (legacy, a migrar por fases)
                // ---------------------------------------------------------------

                // --- GROUP 2: Text-like (content.innerContent.desktop.value) ---
                if ( in_array( $slug, [
                    'divi/text', 'divi/code', 'divi/heading',
                    'divi/fullwidth-code', 'divi/shortcode-module'
                ], true ) ) {
                    if ( isset( $data['content'] ) ) {
                        if ( is_string( $data['content'] ) ) {
                            // Raw string: wrap in standard structure
                            $attrs['content']['innerContent'] = [
                                'desktop' => ['value' => $data['content']]
                            ];
                        } elseif ( isset( $data['content']['innerContent'] ) ) {
                            // Already structured (from build_page.php deep_merge): use as-is
                            $attrs['content'] = $data['content'];
                        } else {
                            // Fallback: assume array with keys to merge
                            $attrs['content']['innerContent'] = [
                                'desktop' => ['value' => $data['content']]
                            ];
                        }
                    }
                    
                    // Fix: In Divi 5, text fonts belong to content.decoration, not module
                    if ( $slug === 'divi/text' || $slug === 'divi/heading' ) {
                        if ( isset( $data['headingFont'] ) ) {
                            $attrs['content']['decoration']['headingFont'] = $data['headingFont'];
                            unset( $attrs['module']['headingFont'] );
                        }
                        if ( isset( $data['bodyFont'] ) ) {
                            $attrs['content']['decoration']['bodyFont'] = $data['bodyFont'];
                            unset( $attrs['module']['bodyFont'] );
                        }
                    }
                    
                    // Fix: divi/heading needs title.innerContent + headingLevel for Divi 5
                    if ( $slug === 'divi/heading' && isset( $data['content'] ) ) {
                        $heading_text = $data['content'];
                        $heading_level = $data['level'] ?? 'h2';
                        if ( preg_match( '/<h([1-6])>/', $heading_text, $m ) ) {
                            $heading_level = 'h' . $m[1];
                            $heading_text = strip_tags( $heading_text );
                        } elseif ( isset( $data['title']['level'] ) ) {
                            $heading_level = $data['title']['level'];
                        }
                        $attrs['title']['innerContent'] = [ 'desktop' => [ 'value' => $heading_text ] ];
                        $attrs['title']['decoration']['font']['font']['desktop']['value']['headingLevel'] = $heading_level;
                    }

                    // Fix: VIE puts font in module.decoration.font, but Divi 5 expects:
                    //   divi/text    → content.decoration.bodyFont
                    //   divi/heading → title.decoration.font.font
                    $font_src = $attrs['module']['decoration']['font'] ?? null;
                    if ( $font_src ) {
                        if ( $slug === 'divi/text' ) {
                            $attrs['content']['decoration']['bodyFont'] = $font_src;
                        } elseif ( $slug === 'divi/heading' ) {
                            $attrs['title']['decoration']['font']['font'] = $font_src;
                        }
                        unset( $attrs['module']['decoration']['font'] );
                    }
                }

            // --- GROUP 3: Image-like (image.innerContent.desktop.value) ---
            elseif ( in_array( $slug, [
                'divi/image', 'divi/fullwidth-image'
            ], true ) ) {
                if ( isset( $data['src'] ) ) {
                    $attrs['image']['innerContent'] = [
                        'desktop' => ['value' => [
                            'src' => $data['src'],
                            'alt' => $data['alt'] ?? ''
                        ]]
                    ];
                }
            }

            // --- GROUP 4: Button-like (button.innerContent.desktop.value) ---
            elseif ( $slug === 'divi/button' ) {
                if ( isset( $data['button_text'] ) ) {
                    $attrs['button']['innerContent'] = [
                        'desktop' => ['value' => [
                            'text' => $data['button_text'],
                            'linkUrl' => $data['button_url'] ?? '#',
                            'linkTarget' => 'off',
                            'rel' => []
                        ]]
                    ];
                }
                // Fix: Map the custom preset attributes under module.decoration.button
                // to standard Divi 5 button attributes under button.decoration
                if ( isset( $attrs['module']['decoration']['button'] ) ) {
                    $btn_styles = $attrs['module']['decoration']['button'];
                    unset( $attrs['module']['decoration']['button'] );
                    
                    if ( ! isset( $attrs['button']['decoration'] ) ) {
                        $attrs['button']['decoration'] = [];
                    }
                    
                    $target_dec =& $attrs['button']['decoration'];
                    
                    foreach ( [ 'desktop', 'tablet', 'phone', 'hover' ] as $state_key ) {
                        if ( ! isset( $btn_styles[ $state_key ]['value'] ) ) {
                            continue;
                        }
                        $vals = $btn_styles[ $state_key ]['value'];
                        
                        $breakpoint = 'desktop';
                        $state      = 'value';
                        
                        if ( in_array( $state_key, [ 'desktop', 'tablet', 'phone' ], true ) ) {
                            $breakpoint = $state_key;
                            $state      = 'value';
                        } elseif ( $state_key === 'hover' ) {
                            $breakpoint = 'desktop';
                            $state      = 'hover';
                        }
                        
                        $val = $vals; // shorthand

                        // 1. Background Color
                        if ( isset( $val['backgroundColor'] ) ) {
                            $target_dec['background'][ $breakpoint ][ $state ]['color'] = $val['backgroundColor'];
                        }

                        // 2. Text Color (accept both 'color' (VIE) and 'textColor')
                        $btn_color = $val['textColor'] ?? $val['color'] ?? null;
                        if ( $btn_color !== null ) {
                            $target_dec['font']['font'][ $breakpoint ][ $state ]['color'] = $btn_color;
                        }

                        // 2b. Hover state from VIE's hover-prefixed keys in desktop.value
                        if ( $state_key === 'desktop' ) {
                            if ( isset( $val['hoverBackgroundColor'] ) ) {
                                $target_dec['background']['desktop']['hover']['color'] = $val['hoverBackgroundColor'];
                            }
                            $hover_color = $val['hoverColor'] ?? $val['hoverTextColor'] ?? null;
                            if ( $hover_color !== null ) {
                                $target_dec['font']['font']['desktop']['hover']['color'] = $hover_color;
                            }
                        }

                        // 3. Border Radius
                        if ( isset( $val['borderRadius'] ) ) {
                            $rad = $val['borderRadius'];
                            $target_dec['border'][ $breakpoint ][ $state ]['radius'] = [
                                'topLeft'     => $rad,
                                'topRight'    => $rad,
                                'bottomRight' => $rad,
                                'bottomLeft'  => $rad,
                                'sync'        => 'on'
                            ];
                        }

                        // 4. Padding (accept both object and string)
                        if ( isset( $val['padding'] ) ) {
                            $pad = $val['padding'];
                            if ( is_string( $pad ) ) {
                                $parts = preg_split( '/\s+/', trim( $pad ) );
                                if ( count( $parts ) === 2 ) {
                                    $top_bottom = $parts[0];
                                    $left_right = $parts[1];
                                    $target_dec['spacing'][ $breakpoint ][ $state ]['padding'] = [
                                        'top'    => $top_bottom,
                                        'bottom' => $top_bottom,
                                        'left'   => $left_right,
                                        'right'  => $left_right
                                    ];
                                } elseif ( count( $parts ) === 4 ) {
                                    $target_dec['spacing'][ $breakpoint ][ $state ]['padding'] = [
                                        'top'    => $parts[0],
                                        'right'  => $parts[1],
                                        'bottom' => $parts[2],
                                        'left'   => $parts[3]
                                    ];
                                } else {
                                    $target_dec['spacing'][ $breakpoint ][ $state ]['padding'] = [
                                        'top'    => $pad,
                                        'bottom' => $pad,
                                        'left'   => $pad,
                                        'right'  => $pad
                                    ];
                                }
                            } else {
                                $target_dec['spacing'][ $breakpoint ][ $state ]['padding'] = $pad;
                            }
                        }

                        // 5. Font Styles (VIE uses 'font' and 'size'; handler expects 'fontFamily'/'fontSize')
                        $btn_family = $val['fontFamily'] ?? $val['font'] ?? null;
                        if ( $btn_family !== null ) {
                            $target_dec['font']['font'][ $breakpoint ][ $state ]['fontFamily'] = $btn_family;
                        }
                        if ( isset( $val['fontWeight'] ) ) {
                            $target_dec['font']['font'][ $breakpoint ][ $state ]['fontWeight'] = $val['fontWeight'];
                        }
                        $btn_size = $val['fontSize'] ?? $val['size'] ?? null;
                        if ( $btn_size !== null ) {
                            $target_dec['font']['font'][ $breakpoint ][ $state ]['size'] = $btn_size;
                        }
                        if ( isset( $val['letterSpacing'] ) ) {
                            $target_dec['font']['font'][ $breakpoint ][ $state ]['letterSpacing'] = $val['letterSpacing'];
                        }
                        if ( isset( $val['textTransform'] ) ) {
                            $target_dec['font']['font'][ $breakpoint ][ $state ]['textTransform'] = $val['textTransform'];
                        }

                        // 6. Border Styles (accept both flat keys and structured 'border' object)
                        if ( isset( $val['border'] ) && is_array( $val['border'] ) ) {
                            $b_all = $val['border']['all'] ?? [];
                            $target_dec['border'][ $breakpoint ][ $state ]['styles']['all'] = $b_all;
                        } else {
                            if ( isset( $val['borderColor'] ) || isset( $val['borderWidth'] ) || isset( $val['borderStyle'] ) ) {
                                $b_color = $val['borderColor'] ?? '';
                                $b_width = $val['borderWidth'] ?? '';
                                $b_style = $val['borderStyle'] ?? 'solid';
                                $border_all = [];
                                if ( $b_color !== '' ) $border_all['color'] = $b_color;
                                if ( $b_width !== '' ) $border_all['width'] = $b_width;
                                if ( $b_style !== '' ) $border_all['style'] = $b_style;
                                if ( ! empty( $border_all ) ) {
                                    $target_dec['border'][ $breakpoint ][ $state ]['styles']['all'] = $border_all;
                                }
                            }
                        }
                    }
                }
            }

            // --- GROUP 5: Menu blocks ---
            elseif ( in_array( $slug, [ 'divi/menu', 'divi/fullwidth-menu' ], true ) ) {
                if ( isset( $data['menu_id'] ) ) {
                    // Flat format (legacy)
                    $attrs['menu']['advanced']['menuId'] = [
                        'desktop' => ['value' => $data['menu_id']]
                    ];
                }
                if ( isset( $data['menu'] ) && is_array( $data['menu'] ) ) {
                    // Structured format from page-def deep_merge
                    $attrs['menu'] = array_merge( $attrs['menu'] ?? [], $data['menu'] );
                }
            }

            // --- GROUP 6: Video ---
            elseif ( $slug === 'divi/video' || $slug === 'divi/audio' ) {
                if ( isset( $data['src'] ) ) {
                    $attrs['video']['innerContent'] = [
                        'desktop' => ['value' => [
                            'video' => $data['src'],
                            'webm'  => $data['webm'] ?? ''
                        ]]
                    ];
                }
            }

            // --- GROUP 7: Divider (decoration + line properties) ---
            elseif ( $slug === 'divi/divider' ) {
                // Divider has no innerContent — decoration is enough
                $line_props = [];
                foreach ( ['show', 'color', 'style', 'position', 'weight'] as $prop ) {
                    if ( isset( $data[ $prop ] ) ) {
                        $line_props[ $prop ] = $data[ $prop ];
                    }
                }
                if ( ! empty( $line_props ) ) {
                    $attrs['divider']['advanced']['line'] = [
                        'desktop' => ['value' => $line_props]
                    ];
                }
            }

            // --- GROUP 8: Contact form ---
            elseif ( $slug === 'divi/contact-form' ) {
                if ( isset( $data['email_to'] ) ) {
                    $attrs['email']['innerContent'] = [
                        'desktop' => ['value' => ['email' => $data['email_to']]]
                    ];
                }
                if ( isset( $data['success_message'] ) ) {
                    $attrs['messageSuccess']['innerContent'] = [
                        'desktop' => ['value' => $data['success_message']]
                    ];
                }
                if ( isset( $data['submit_text'] ) ) {
                    $attrs['button']['innerContent'] = [
                        'desktop' => ['value' => ['text' => $data['submit_text']]]
                    ];
                }
                $attrs['advanced']['spamProtection']['desktop']['value'] = [
                    'enabled'          => isset( $data['use_captcha'] ) && $data['use_captcha'] ? 'on' : 'off',
                    'useBasicCaptcha'  => isset( $data['use_captcha'] ) && $data['use_captcha'] ? 'on' : 'off',
                ];
                $inner_html = $children_html;
                $children_html = '';
            }

            elseif ( $slug === 'divi/contact-field' ) {
                if ( isset( $data['field_type'], $data['field_label'] ) ) {
                    $field_id = isset( $data['field_id'] ) ? $data['field_id'] : sanitize_title( $data['field_label'] );
                    $attrs['fieldItem']['advanced']['type']['desktop']['value'] = $data['field_type'];
                    $attrs['fieldItem']['advanced']['required']['desktop']['value'] = ( isset( $data['required'] ) && $data['required'] ) ? 'on' : 'off';
                    $attrs['fieldItem']['advanced']['id']['desktop']['value'] = $field_id;
                    $attrs['fieldItem']['innerContent']['desktop']['value'] = $data['field_label'];
                    if ( isset( $data['placeholder'] ) ) {
                        $field_id_attr = 'fieldItemPlaceholder';
                        $attrs[ $field_id_attr ]['desktop']['value'] = $data['placeholder'];
                    }
                }
            }

            // --- GROUP 9: Blurb (icon/image + title + content) ---
            elseif ( $slug === 'divi/blurb' ) {
                // title: innerContent only — tagName defaults to h4 in metadata
                if ( isset( $data['title'] ) && is_array( $data['title'] ) && isset( $data['title']['innerContent'] ) ) {
                    $title_val = $data['title']['innerContent']['desktop']['value'] ?? '';
                    $attrs['title']['innerContent'] = [ 'desktop' => ['value' => $title_val] ];
                } else {
                    $attrs['title']['innerContent'] = [ 'desktop' => ['value' => $data['title'] ?? ''] ];
                }
                // content: supports both flat string and structured {innerContent:{desktop:{value:...}}}
                if ( isset( $data['content'] ) && is_array( $data['content'] ) && isset( $data['content']['innerContent'] ) ) {
                    $content_val = $data['content']['innerContent']['desktop']['value'] ?? '';
                    $attrs['content']['innerContent'] = [ 'desktop' => ['value' => $content_val] ];
                } else {
                    $attrs['content']['innerContent'] = [ 'desktop' => ['value' => $data['content'] ?? ''] ];
                }
                // Copy imageIcon from data if explicitly provided (e.g., useIcon: off)
                if ( isset( $data['imageIcon'] ) ) {
                    $attrs['imageIcon'] = $data['imageIcon'];
                } elseif ( isset( $data['icon'] ) ) {
                    // Fix: icon must be {unicode, type, weight} object, not plain string
                    $attrs['imageIcon']['innerContent'] = [
                        'desktop' => ['value' => [
                            'useIcon'   => 'on',
                            'icon'      => [
                                'unicode' => $data['icon'],
                                'type'    => 'divi',
                                'weight'  => '400'
                            ],
                            'src'       => '',
                            'animation' => 'off'
                        ]]
                    ];
                }
            }

            // --- GROUP 10: Number Counter / Counter / Circle Counter ---
            elseif ( in_array( $slug, [ 'divi/number-counter', 'divi/counter', 'divi/circle-counter' ], true ) ) {
                $title_value = $data['title'] ?? '';
                if ( is_array( $title_value ) ) {
                    $title_value = $title_value['innerContent']['desktop']['value'] ?? ( $data['label'] ?? '' );
                }
                if ( '' === $title_value && isset( $data['label'] ) ) {
                    $title_value = $data['label'];
                }
                $attrs['title']['innerContent'] = [ 'desktop' => ['value' => $title_value ] ];
                
                // EnablePercentSign: schema value wins, else auto-detect from %
                if ( isset( $data['enablePercentSign'] ) ) {
                    $attrs['number']['advanced']['enablePercentSign'] = [ 'desktop' => [ 'value' => $data['enablePercentSign'] ] ];
                }
                $number_raw = $data['number'] ?? '0';
                // Handle both schema shorthand (string) and Divi 5 block attribute (nested object)
                if ( is_array( $number_raw ) ) {
                    $number_val = $number_raw['innerContent']['desktop']['value'] ?? '0';
                } else {
                    $number_val = $number_raw;
                }
                if ( is_string( $number_val ) && strpos( $number_val, '%' ) !== false ) {
                    $number_val = str_replace( '%', '', $number_val );
                    if ( ! isset( $data['enablePercentSign'] ) ) {
                        $attrs['number']['advanced']['enablePercentSign'] = [ 'desktop' => [ 'value' => 'on' ] ];
                    }
                }
                $attrs['number']['innerContent'] = [ 'desktop' => ['value' => $number_val ] ];

                // Fix: Propagate headingFont to number.decoration.font (the big stat) without overwriting existing structure
                if ( isset( $data['headingFont'] ) && is_array( $data['headingFont'] ) ) {
                    $font_data = current( $data['headingFont'] );
                    if ( isset( $font_data['font'] ) ) {
                        $attrs['number']['decoration']['font']['font'] = array_merge(
                            $attrs['number']['decoration']['font']['font'] ?? [],
                            $font_data['font']
                        );
                    } else {
                        $attrs['number']['decoration']['font']['font'] = array_merge(
                            $attrs['number']['decoration']['font']['font'] ?? [],
                            $font_data
                        );
                    }
                    unset( $attrs['module']['headingFont'] );
                }
                // Fix: Propagate bodyFont to title.decoration.font (the label below) without overwriting existing structure
                if ( isset( $data['bodyFont'] ) && is_array( $data['bodyFont'] ) ) {
                    $font_data = current( $data['bodyFont'] );
                    if ( isset( $font_data['font'] ) ) {
                        $attrs['title']['decoration']['font']['font'] = array_merge(
                            $attrs['title']['decoration']['font']['font'] ?? [],
                            $font_data['font']
                        );
                    } else {
                        $attrs['title']['decoration']['font']['font'] = array_merge(
                            $attrs['title']['decoration']['font']['font'] ?? [],
                            $font_data
                        );
                    }
                    unset( $attrs['module']['bodyFont'] );
                }
            }

            // --- GROUP 11: Icon ---
            elseif ( $slug === 'divi/icon' ) {
                if ( isset( $data['icon'] ) ) {
                    $attrs['icon']['innerContent'] = [
                        'desktop' => ['value' => [
                            'icon'      => $data['icon'],
                            'link'      => $data['link'] ?? '',
                            'linkUrl'   => $data['link_url'] ?? ''
                        ]]
                    ];
                }
            }

            // --- GROUP 12: Toggle (expandable single item) ---
            elseif ( $slug === 'divi/toggle' ) {
                if ( isset( $data['title'] ) ) {
                    $attrs['title']['innerContent'] = [ 'desktop' => ['value' => $data['title']] ];
                }
                if ( isset( $data['content'] ) ) {
                    $attrs['content']['innerContent'] = [ 'desktop' => ['value' => $data['content']] ];
                }
                // Propagate headingFont to title.decoration.font
                if ( isset( $data['headingFont'] ) && is_array( $data['headingFont'] ) ) {
                    $attrs['title']['decoration']['font']['font'] = $data['headingFont'];
                    unset( $attrs['module']['headingFont'] );
                }
                // Propagate bodyFont to content.decoration.bodyFont
                if ( isset( $data['bodyFont'] ) ) {
                    $attrs['content']['decoration']['bodyFont'] = $data['bodyFont'];
                    unset( $attrs['module']['bodyFont'] );
                }
                // Pass through toggle state styling directly
                foreach ( [ 'openToggle', 'closedToggle', 'openToggleIcon' ] as $tk ) {
                    if ( isset( $data[ $tk ] ) ) {
                        $attrs[ $tk ] = $data[ $tk ];
                    }
                }
            }

            // --- GROUP 13: Accordion Item / Slide / Tab (child modules with content) ---
            elseif ( in_array( $slug, [ 'divi/accordion-item', 'divi/slide', 'divi/tab', 'divi/video-slider-item' ], true ) ) {
                if ( isset( $data['title'] ) ) {
                    $attrs['title']['innerContent'] = [ 'desktop' => ['value' => $data['title']] ];
                }
                if ( isset( $data['content'] ) ) {
                    $attrs['content']['innerContent'] = [ 'desktop' => ['value' => $data['content']] ];
                }
                if ( isset( $data['src'] ) ) {
                    $attrs['image']['innerContent'] = [ 'desktop' => ['value' => [ 'src' => $data['src'], 'alt' => $data['alt'] ?? '' ]] ];
                }
                if ( isset( $data['button_text'] ) ) {
                    $attrs['button']['innerContent'] = [ 'desktop' => ['value' => [
                        'text'    => $data['button_text'],
                        'linkUrl' => $data['button_url'] ?? '#'
                    ]] ];
                }
            }

            // --- GROUP 14: Search ---
            elseif ( $slug === 'divi/search' ) {
                // Uses advanced fields, not innerContent
                $attrs['search'] = [ 'advanced' => [
                    'showButton'    => [ 'desktop' => ['value' => $data['show_button'] ?? 'on'] ],
                    'excludePages'  => [ 'desktop' => ['value' => $data['exclude_pages'] ?? 'off'] ],
                    'excludePosts'  => [ 'desktop' => ['value' => $data['exclude_posts'] ?? 'off'] ],
                ] ];
            }

            // --- GROUP 15: Social Media Follow Network (child) ---
            elseif ( $slug === 'divi/social-media-follow-network' ) {
                if ( isset( $data['social_network'] ) ) {
                    $attrs['socialNetwork']['innerContent'] = [
                        'desktop' => ['value' => [
                            'socialNetworkTitle'       => $data['social_network'],
                            'socialNetworkLink'        => $data['link'] ?? '',
                            'socialNetworkSkypeUrl'    => $data['skype_url'] ?? '',
                            'socialNetworkSkypeAction' => $data['skype_action'] ?? 'call'
                        ]]
                    ];
                }
            }

            // --- GROUP 16: Map ---
            elseif ( $slug === 'divi/map' || $slug === 'divi/fullwidth-map' ) {
                if ( isset( $data['address'] ) ) {
                    $attrs['map']['innerContent'] = [
                        'desktop' => ['value' => $data['address']]
                    ];
                }
                if ( isset( $data['mouse_wheel'] ) ) {
                    $attrs['map']['advanced']['mouseWheel'] = [ 'desktop' => ['value' => $data['mouse_wheel']] ];
                }
                if ( isset( $data['mobile_dragging'] ) ) {
                    $attrs['map']['advanced']['mobileDragging'] = [ 'desktop' => ['value' => $data['mobile_dragging']] ];
                }
            }

            // --- GROUP 17: Gallery ---
            elseif ( $slug === 'divi/gallery' ) {
                if ( isset( $data['gallery_ids'] ) ) {
                    $attrs['image']['advanced']['galleryIds'] = [ 'desktop' => ['value' => $data['gallery_ids']] ];
                }
                if ( isset( $data['fullwidth'] ) ) {
                    $attrs['module']['advanced']['fullwidth'] = [ 'desktop' => ['value' => $data['fullwidth']] ];
                }
            }

            // --- GROUP 18: Blog ---
            elseif ( $slug === 'divi/blog' ) {
                $post_attrs = [];
                foreach ( [ 'type', 'number', 'categories', 'dateFormat', 'excerptLength', 'offset',
                            'showExcerpt', 'showAuthor', 'showDate', 'showCategories', 'showComments',
                            'useCurrentLoop' ] as $key ) {
                    if ( isset( $data[$key] ) ) {
                        $post_attrs[$key] = $data[$key];
                    }
                }
                if ( ! empty( $post_attrs ) ) {
                    $attrs['post']['advanced'] = [];
                    foreach ( $post_attrs as $k => $v ) {
                        $attrs['post']['advanced'][$k] = [ 'desktop' => ['value' => $v ] ];
                    }
                }
                if ( isset( $data['show_featured_image'] ) ) {
                    $attrs['image']['advanced']['enable'] = [ 'desktop' => ['value' => $data['show_featured_image']] ];
                }
            }

            // --- GROUP 19: Sidebar ---
            elseif ( $slug === 'divi/sidebar' ) {
                if ( isset( $data['area'] ) ) {
                    $attrs['sidebar']['innerContent'] = [
                        'desktop' => ['value' => [ 'area' => $data['area'] ]]
                    ];
                }
                if ( isset( $data['show_border'] ) ) {
                    $attrs['sidebar']['advanced']['layout'] = [ 'desktop' => ['value' => [ 'showBorder' => $data['show_border'] ] ] ];
                }
            }

            // --- GROUP 20: CTA / Call to Action ---
            elseif ( $slug === 'divi/cta' ) {
                if ( isset( $data['title'] ) ) {
                    $attrs['title']['innerContent'] = [ 'desktop' => ['value' => $data['title']] ];
                }
                if ( isset( $data['content'] ) ) {
                    $attrs['content']['innerContent'] = [ 'desktop' => ['value' => $data['content']] ];
                }
                if ( isset( $data['button_text'] ) ) {
                    $attrs['button']['innerContent'] = [ 'desktop' => ['value' => [
                        'text' => $data['button_text'], 'linkUrl' => $data['button_url'] ?? '#'
                    ]] ];
                }
            }

            // --- GROUP 21: Testimonial ---
            elseif ( $slug === 'divi/testimonial' ) {
                if ( isset( $data['content'] ) ) {
                    $attrs['content']['innerContent'] = [ 'desktop' => ['value' => $data['content']] ];
                }
                if ( isset( $data['author'] ) ) {
                    $attrs['author'] = $data['author']; // simple string or innerContent pattern
                }
                if ( isset( $data['src'] ) ) {
                    $attrs['image']['innerContent'] = [ 'desktop' => ['value' => [ 'src' => $data['src'], 'alt' => $data['alt'] ?? '' ]] ];
                }
            }

            // --- GROUP 22: Team Member ---
            elseif ( $slug === 'divi/team-member' ) {
                if ( isset( $data['name'] ) ) {
                    $attrs['name'] = [ 'innerContent' => [ 'desktop' => ['value' => $data['name']] ] ];
                }
                if ( isset( $data['position'] ) ) {
                    $attrs['position'] = [ 'innerContent' => [ 'desktop' => ['value' => $data['position']] ] ];
                }
                if ( isset( $data['content'] ) ) {
                    $attrs['content']['innerContent'] = [ 'desktop' => ['value' => $data['content']] ];
                }
                if ( isset( $data['src'] ) ) {
                    $attrs['image']['innerContent'] = [ 'desktop' => ['value' => [ 'src' => $data['src'], 'alt' => $data['alt'] ?? '' ]] ];
                }
            }

            // --- GROUP 23: Pricing Table ---
            elseif ( $slug === 'divi/pricing-table' ) {
                if ( isset( $data['title'] ) ) {
                    $attrs['title']['innerContent'] = [ 'desktop' => ['value' => $data['title']] ];
                }
                if ( isset( $data['subtitle'] ) ) {
                    $attrs['subtitle']['innerContent'] = [ 'desktop' => ['value' => $data['subtitle']] ];
                }
                if ( isset( $data['price'] ) ) {
                    $attrs['price']['innerContent'] = [ 'desktop' => ['value' => $data['price']] ];
                }
                if ( isset( $data['currencyFrequency'] ) ) {
                    $cf_raw = $data['currencyFrequency'];
                    if ( is_array( $cf_raw ) ) {
                        $attrs['currencyFrequency']['innerContent'] = [ 'desktop' => ['value' => $cf_raw] ];
                    } else {
                        $attrs['currencyFrequency']['innerContent'] = [ 'desktop' => ['value' => [
                            'currency' => [ 'innerContent' => [ 'desktop' => ['value' => $cf_raw] ] ],
                            'per'      => [ 'innerContent' => [ 'desktop' => ['value' => ''] ] ],
                        ] ] ];
                    }
                }
                if ( isset( $data['content'] ) ) {
                    $attrs['content']['innerContent'] = [ 'desktop' => ['value' => $data['content']] ];
                }
                if ( isset( $data['excluded'] ) ) {
                    $attrs['excluded']['innerContent'] = [ 'desktop' => ['value' => $data['excluded']] ];
                }
                if ( isset( $data['featured'] ) ) {
                    if ( ! isset( $attrs['module']['advanced'] ) ) {
                        $attrs['module']['advanced'] = [];
                    }
                    $attrs['module']['advanced']['featured'] = [ 'desktop' => ['value' => $data['featured']] ];
                }
                if ( isset( $data['button_text'] ) || isset( $data['button_url'] ) ) {
                    $attrs['button']['innerContent'] = [ 'desktop' => ['value' => [
                        'text' => $data['button_text'] ?? 'Select', 'linkUrl' => $data['button_url'] ?? '#'
                    ]] ];
                } elseif ( isset( $data['button'] ) && is_array( $data['button'] ) ) {
                    $attrs['button'] = $data['button'];
                }
            }

            // --- GROUP 24: Fullwidth Header ---
            elseif ( $slug === 'divi/fullwidth-header' ) {
                if ( isset( $data['title'] ) ) {
                    $attrs['title']['innerContent'] = [ 'desktop' => ['value' => $data['title']] ];
                }
                if ( isset( $data['subtitle'] ) ) {
                    $attrs['subtitle'] = [ 'innerContent' => [ 'desktop' => ['value' => $data['subtitle']] ] ];
                }
                if ( isset( $data['content'] ) ) {
                    $attrs['content']['innerContent'] = [ 'desktop' => ['value' => $data['content']] ];
                }
                if ( isset( $data['button_text'] ) ) {
                    $attrs['button']['innerContent'] = [ 'desktop' => ['value' => [
                        'text' => $data['button_text'], 'linkUrl' => $data['button_url'] ?? '#'
                    ]] ];
                }
                if ( isset( $data['logo_src'] ) ) {
                    $attrs['logo']['innerContent'] = [ 'desktop' => ['value' => [ 'src' => $data['logo_src'], 'alt' => $data['logo_alt'] ?? '' ]] ];
                }
            }

            // --- GROUP 25: Post Title / Post Content (dynamic) ---
            elseif ( in_array( $slug, [ 'divi/post-title', 'divi/post-content', 'divi/post-nav',
                                        'divi/comments', 'divi/fullwidth-post-title',
                                        'divi/fullwidth-post-content' ], true ) ) {
                // Dynamic content blocks have no static innerContent
                // Just decoration passes through
            }

            // --- GROUP 26: Countdown Timer ---
            elseif ( $slug === 'divi/countdown-timer' ) {
                if ( isset( $data['title'] ) ) {
                    if ( is_array( $data['title'] ) ) {
                        $attrs['title']['innerContent'] = [ 'desktop' => ['value' => $data['title']['innerContent']['desktop']['value'] ?? ''] ];
                        if ( isset( $data['title']['decoration'] ) ) {
                            $attrs['title']['decoration'] = $data['title']['decoration'];
                        }
                    } else {
                        $attrs['title']['innerContent'] = [ 'desktop' => ['value' => $data['title']] ];
                    }
                }
                if ( isset( $data['content'] ) && is_array( $data['content'] ) ) {
                    $attrs['content']['innerContent'] = [ 'desktop' => ['value' => $data['content']['innerContent']['desktop']['value'] ?? ''] ];
                    if ( isset( $data['content']['advanced'] ) ) {
                        $attrs['content']['advanced'] = $data['content']['advanced'];
                    }
                    if ( isset( $data['content']['decoration'] ) ) {
                        $attrs['content']['decoration'] = $data['content']['decoration'];
                    }
                }
                foreach ( ['number', 'label', 'separator'] as $attr ) {
                    if ( isset( $data[$attr] ) && is_array( $data[$attr] ) ) {
                        foreach ( $data[$attr] as $k => $v ) {
                            if ( $k !== 'innerContent' && ! isset( $attrs[$attr][$k] ) ) {
                                $attrs[$attr][$k] = $v;
                            }
                        }
                    }
                }
            }

            // --- GROUP 27: Login ---
            elseif ( $slug === 'divi/login' ) {
                if ( isset( $data['content'] ) ) {
                    $attrs['content']['innerContent'] = [ 'desktop' => ['value' => $data['content']] ];
                }
                if ( isset( $data['button_text'] ) ) {
                    $attrs['button']['innerContent'] = [ 'desktop' => ['value' => [ 'text' => $data['button_text'] ]] ];
                }
            }

            // --- GROUP 28: Contact Form 7 / Signup ---
            elseif ( $slug === 'divi/contact-form-7' ) {
                if ( isset( $data['form_id'] ) ) {
                    $attrs['content']['innerContent'] = [ 'desktop' => ['value' => "[contact-form-7 id=\"{$data['form_id']}\"]" ] ];
                }
            }

            // --- GROUP 29: Icon List Item ---
            elseif ( $slug === 'divi/icon-list-item' ) {
                // Support both 'title' (new) and 'content' (legacy template) keys
                $label = $data['title'] ?? ( isset( $data['content'] ) && is_string( $data['content'] ) ? $data['content'] : null );
                if ( $label !== null ) {
                    $attrs['title']['innerContent'] = [ 'desktop' => ['value' => $label] ];
                }
                if ( isset( $data['icon'] ) ) {
                    $attrs['icon'] = [ 'advanced' => [ 'icon' => [ 'desktop' => ['value' => $data['icon'] ] ] ] ];
                }
            }

            // --- GROUP 30: Lottie ---
            elseif ( $slug === 'divi/lottie' ) {
                if ( isset( $data['src'] ) ) {
                    $attrs['lottie'] = [ 'innerContent' => [ 'desktop' => ['value' => $data['src']] ] ];
                }
            }

            // --- GROUP 31: SVG ---
            elseif ( $slug === 'divi/svg' ) {
                if ( isset( $data['content'] ) ) {
                    $attrs['content']['innerContent'] = [ 'desktop' => ['value' => $data['content']] ];
                }
            }

            // --- GROUP 32: Map Pin (child of map) ---
            elseif ( $slug === 'divi/map-pin' ) {
                if ( isset( $data['address'] ) ) {
                    $attrs['pin'] = [ 'innerContent' => [ 'desktop' => ['value' => $data['address'] ] ] ];
                }
                if ( isset( $data['content'] ) ) {
                    $attrs['content']['innerContent'] = [ 'desktop' => ['value' => $data['content'] ] ];
                }
            }

            // --- GROUP 33: Dropdown ---
            elseif ( $slug === 'divi/dropdown' ) {
                if ( isset( $data['title'] ) ) {
                    $attrs['title']['innerContent'] = [ 'desktop' => ['value' => $data['title'] ] ];
                }
                if ( isset( $data['content'] ) ) {
                    $attrs['content']['innerContent'] = [ 'desktop' => ['value' => $data['content'] ] ];
                }
            }

            // --- GROUP 34: Portfolio / Filterable Portfolio ---
            elseif ( in_array( $slug, [ 'divi/portfolio', 'divi/filterable-portfolio' ], true ) ) {
                if ( isset( $data['number'] ) ) {
                    $attrs['module']['advanced']['postsNumber'] = [ 'desktop' => ['value' => $data['number'] ] ];
                }
            }

            // --- GROUP 35: Child containers (no own content, just children) ---
            elseif ( in_array( $slug, [
                'divi/row-inner', 'divi/group', 'divi/group-carousel',
                'divi/global-layout', 'divi/layout', 'divi/placeholder'
            ], true ) ) {
                $inner_html = $children_html;
                $children_html = '';
            }

            // --- GROUP 36: Slider / Accordion / Tabs / Icon List / Social Follow (parent containers) ---
            elseif ( in_array( $slug, [
                'divi/slider', 'divi/video-slider', 'divi/accordion',
                'divi/tabs', 'divi/social-media-follow', 'divi/icon-list',
                'divi/fullwidth-slider', 'divi/pricing-tables', 'divi/fullwidth-portfolio'
            ], true ) ) {
                // Parent containers rely on children_html
                $inner_html = $children_html;
                $children_html = '';
            }

            // --- GROUP 37: WooCommerce blocks (all) ---
            elseif ( strpos( $slug, 'divi/woocommerce-' ) === 0 || $slug === 'divi/shop' ) {
                // Pass through any woocommerce-specific data as innerContent
                if ( isset( $data['content'] ) ) {
                    $attrs['content']['innerContent'] = [ 'desktop' => ['value' => $data['content'] ] ];
                }
            }

            // --- GROUP 98: Static decoration-only blocks ---
            elseif ( in_array( $slug, [
                'divi/before-after-image', 'divi/canvas-portal', 'divi/breadcrumbs',
                'divi/link', 'divi/post-slider', 'divi/signup', 'divi/signup-custom-field'
            ], true ) ) {
                // Decoration-only; pass through specific data
                if ( isset( $data['before_src'] ) && isset( $data['after_src'] ) ) {
                    $attrs['image'] = [
                        'innerContent' => [ 'desktop' => ['value' => [
                            'before' => $data['before_src'],
                            'after'  => $data['after_src']
                        ]] ]
                    ];
                }
            }

            // --- GROUP 99: Fullwidth blocks (generic fallthrough) ---
            elseif ( strpos( $slug, 'divi/fullwidth-' ) === 0 ) {
                if ( isset( $data['content'] ) ) {
                    $attrs['content']['innerContent'] = [ 'desktop' => ['value' => $data['content'] ] ];
                }
            }

            // --- METADATA-DRIVEN FALLBACK: handles any of the 102 blocks not matched above ---
            else {
                $meta = self::get_module_meta( $slug );
                if ( $meta && isset( $meta['attributes'] ) ) {
                    $auto_merged = [ 'decoration', 'boxShadow', 'spacing', 'meta', 'advanced',
                                     'headingFont', 'bodyFont', 'animation', 'transform', 'presets',
                                     'children', 'module', '_type' ];
                    foreach ( $meta['attributes'] as $attr_name => $attr_def ) {
                        if ( in_array( $attr_name, $auto_merged, true ) ) continue;
                        if ( ! isset( $data[ $attr_name ] ) ) continue;

                        $inner_schema = self::get_inner_content_schema( $slug, $attr_name );
                        if ( $inner_schema ) {
                            if ( self::is_group_items( $slug, $attr_name ) ) {
                                $items = self::get_inner_content_items( $slug, $attr_name );
                                $val = [];
                                foreach ( $items as $item_key ) {
                                    if ( isset( $data[ $attr_name ][ $item_key ] ) ) {
                                        $val[ $item_key ] = $data[ $attr_name ][ $item_key ];
                                    }
                                }
                                if ( ! empty( $val ) ) {
                                    $attrs[ $attr_name ]['innerContent'] = [
                                        'desktop' => [ 'value' => $val ]
                                    ];
                                }
                            } else {
                                $raw = $data[ $attr_name ];
                                // If the value already has innerContent.desktop.value structure, use it directly.
                                if ( is_array( $raw ) && isset( $raw['innerContent']['desktop']['value'] ) ) {
                                    $attrs[ $attr_name ] = $raw;
                                } else {
                                    $attrs[ $attr_name ]['innerContent'] = [
                                        'desktop' => [ 'value' => $raw ]
                                    ];
                                }
                            }
                        } else {
                            // Not an innerContent schema attribute — pass through if not already set.
                            if ( ! isset( $attrs[ $attr_name ] ) ) {
                                $attrs[ $attr_name ] = $data[ $attr_name ];
                            }
                        }
                    }
                } else {
                    // CATCH-ALL for custom/third-party modules without metadata.
                    // Pass through all content attributes from $data that aren't already set.
                    $skip_keys = [ 'module', 'presets', 'decoration', 'advanced', 'meta',
                                   'children', 'type', '_type', 'module_class', 'module_id',
                                   'section_type', 'adminLabel', 'css' ];
                    foreach ( $data as $key => $val ) {
                        if ( in_array( $key, $skip_keys, true ) ) continue;
                        if ( isset( $attrs[ $key ] ) ) continue;
                        $attrs[ $key ] = $val;
                    }
                    // Custom container modules use children_html as inner content.
                    if ( $children_html !== '' ) {
                        $inner_html = $children_html;
                    }
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
                            'divi/row-inner', 'divi/group', 'divi/group-carousel'
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

        if ( $attrs['module'] === [] ) { $attrs['module'] = (object)[]; }

        $json_attrs = json_encode( $attrs, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES );

        $inner = ( $content !== '' || $inner_html !== '' ) ? "{$content}{$inner_html}" : '';
        return "<!-- wp:{$slug} {$json_attrs} -->\n{$inner}<!-- /wp:{$slug} -->\n";
    }

}

}
