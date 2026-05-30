<?php
// Divi 5 Blocks → Schema JSON converter
// Reads Divi 5 block content from database and generates a proper schema JSON
// Preserves all design properties and reverse-maps colors/styles to tokens

namespace DAC\Core;

class BlocksToSchema {
    
    private array $color_tokens = [];
    
    public function __construct(?string $design_system_path = null) {
        if ($design_system_path && file_exists($design_system_path)) {
            $raw = file_get_contents($design_system_path);
            $raw = ltrim($raw, "\xEF\xBB\xBF");
            $ds = json_decode($raw, true);
            if (json_last_error() === JSON_ERROR_NONE) {
                $this->color_tokens = $ds['tokens']['color'] ?? [];
            }
        }
    }
    
    public function convert(string $block_content): array {
        $blocks = parse_blocks($block_content);
        $schema = ['sections' => []];
        
        $sections = $this->find_sections($blocks);
        foreach ($sections as $section_block) {
            $section_data = $this->convert_section($section_block);
            if ($section_data) {
                $schema['sections'][] = $section_data;
            }
        }
        
        // Clean empty values and reverse resolve design tokens
        $schema = $this->clean_array($schema);
        if (!empty($this->color_tokens)) {
            $schema = $this->reverse_resolve_tokens($schema, $this->color_tokens);
        }
        
        return $schema;
    }
    
    private function find_sections(array $blocks): array {
        $sections = [];
        foreach ($blocks as $block) {
            if ($block['blockName'] === 'divi/section') {
                $sections[] = $block;
            }
            if (!empty($block['innerBlocks'])) {
                $sections = array_merge($sections, $this->find_sections($block['innerBlocks']));
            }
        }
        return $sections;
    }
    
    private function convert_section(array $block): ?array {
        if ($block['blockName'] !== 'divi/section') return null;
        
        $attrs = $block['attrs']['module'] ?? [];
        $section = [];
        
        // Extracción de tipo de sección (regular, specialty, fullwidth)
        $section_type = $attrs['advanced']['type']['desktop']['value'] ?? 'regular';
        if ($section_type !== 'regular') {
            $section['type'] = $section_type;
        }
        
        // Extraer decoraciones comunes
        $this->extract_common_styles($block, $section);
        
        // Convertir filas internas
        $rows = [];
        foreach ($block['innerBlocks'] as $row_block) {
            $row = $this->convert_row($row_block);
            if ($row) {
                $rows[] = $row;
            }
        }
        if (!empty($rows)) {
            $section['rows'] = $rows;
        }
        
        return $section;
    }
    
    private function convert_row(array $block): ?array {
        if ($block['blockName'] !== 'divi/row') return null;
        
        $attrs = $block['attrs']['module'] ?? [];
        $row = [];
        
        // Estructura de columnas
        $cs = $attrs['advanced']['columnStructure'] ?? [];
        if (isset($cs['desktop']['value'])) {
            if (isset($cs['tablet']) || isset($cs['phone'])) {
                $row['column_structure'] = [];
                foreach (['desktop', 'tablet', 'phone'] as $bp) {
                    if (isset($cs[$bp]['value'])) {
                        $row['column_structure'][$bp] = $cs[$bp]['value'];
                    }
                }
            } else {
                $row['column_structure'] = $cs['desktop']['value'];
            }
        }
        
        // Extraer decoraciones comunes
        $this->extract_common_styles($block, $row);
        
        // Convertir columnas
        $columns = [];
        foreach ($block['innerBlocks'] as $col_block) {
            $col = $this->convert_column($col_block);
            if ($col) {
                $columns[] = $col;
            }
        }
        if (!empty($columns)) {
            $row['columns'] = $columns;
        }
        
        return $row;
    }
    
    private function convert_column(array $block): ?array {
        if ($block['blockName'] !== 'divi/column' && $block['blockName'] !== 'divi/column-inner') return null;
        
        $attrs = $block['attrs']['module'] ?? [];
        $type = $attrs['advanced']['type']['desktop']['value'] ?? '';
        if (!$type) return null;
        
        $column = ['type' => $type];
        
        // Extraer decoraciones comunes
        $this->extract_common_styles($block, $column);
        
        // Convertir módulos
        $modules = [];
        foreach ($block['innerBlocks'] as $mod_block) {
            $module = $this->convert_module($mod_block);
            if ($module) {
                $modules[] = $module;
            }
        }
        if (!empty($modules)) {
            $column['modules'] = $modules;
        }
        
        return $column;
    }
    
    private function convert_module(array $block): ?array {
        $name = $block['blockName'];
        if (!$name || strpos($name, 'divi/') !== 0) return null;
        
        $attrs = $block['attrs'];
        $module = ['type' => $name];
        
        // Extraer decoraciones comunes
        $this->extract_common_styles($block, $module);
        
        // Mapeo específico según el tipo de bloque
        switch ($name) {
            case 'divi/text':
            case 'divi/code':
            case 'divi/heading':
            case 'divi/fullwidth-code':
            case 'divi/shortcode-module':
                $content = $attrs['content']['innerContent']['desktop']['value'] ?? '';
                if ($content !== '') {
                    $module['content'] = $content;
                }
                
                // Tipografías
                $dec = $attrs['content']['decoration'] ?? [];
                if (isset($dec['headingFont'])) {
                    $module['headingFont'] = $dec['headingFont'];
                }
                if (isset($dec['bodyFont'])) {
                    $module['bodyFont'] = $dec['bodyFont'];
                }
                break;
                
            case 'divi/image':
            case 'divi/fullwidth-image':
                $img = $attrs['image']['innerContent']['desktop']['value'] ?? [];
                if (!empty($img['src'])) {
                    $module['src'] = $img['src'];
                    $module['alt'] = $img['alt'] ?? '';
                }
                break;
                
            case 'divi/button':
                $btn = $attrs['button']['innerContent']['desktop']['value'] ?? [];
                if (!empty($btn['text'])) {
                    $module['button_text'] = $btn['text'];
                    $module['button_url'] = $btn['linkUrl'] ?? '#';
                }
                break;
                
            case 'divi/blurb':
                $module['title'] = $attrs['title']['innerContent']['desktop']['value'] ?? '';
                $module['content'] = $attrs['content']['innerContent']['desktop']['value'] ?? '';
                
                $img_icon = $attrs['imageIcon']['innerContent']['desktop']['value'] ?? [];
                if (($img_icon['useIcon'] ?? '') === 'on' && !empty($img_icon['icon'])) {
                    $module['icon'] = $img_icon['icon'];
                }
                
                // Mapear fuentes si existían en sus decoraciones de título/contenido
                $title_font = $attrs['title']['decoration']['font']['font'] ?? '';
                if ($title_font) {
                    $module['headingFont'] = [$title_font];
                }
                $content_font = $attrs['content']['decoration']['bodyFont'] ?? [];
                if ($content_font) {
                    $module['bodyFont'] = $content_font;
                }
                break;
                
            case 'divi/number-counter':
            case 'divi/counter':
            case 'divi/circle-counter':
                $module['title'] = $attrs['title']['innerContent']['desktop']['value'] ?? '';
                
                $num = $attrs['number']['innerContent']['desktop']['value'] ?? '';
                $pct = $attrs['number']['advanced']['enablePercentSign']['desktop']['value'] ?? 'off';
                if ($pct === 'on') {
                    $num .= '%';
                }
                $module['number'] = $num;
                break;
                
            case 'divi/icon':
                $icon_data = $attrs['icon']['innerContent']['desktop']['value'] ?? [];
                if (!empty($icon_data['icon'])) {
                    $module['icon'] = $icon_data['icon'];
                    if (!empty($icon_data['linkUrl'])) {
                        $module['link_url'] = $icon_data['linkUrl'];
                    }
                }
                break;
                
            case 'divi/divider':
                $line_props = $attrs['divider']['advanced']['line']['desktop']['value'] ?? [];
                foreach (['show', 'color', 'style', 'position', 'weight'] as $prop) {
                    if (isset($line_props[$prop])) {
                        $module[$prop] = $line_props[$prop];
                    }
                }
                break;
                
            case 'divi/toggle':
            case 'divi/accordion-item':
            case 'divi/tab':
            case 'divi/slide':
                $module['title'] = $attrs['title']['innerContent']['desktop']['value'] ?? '';
                $module['content'] = $attrs['content']['innerContent']['desktop']['value'] ?? '';
                
                $img = $attrs['image']['innerContent']['desktop']['value'] ?? [];
                if (!empty($img['src'])) {
                    $module['src'] = $img['src'];
                    $module['alt'] = $img['alt'] ?? '';
                }
                $btn = $attrs['button']['innerContent']['desktop']['value'] ?? [];
                if (!empty($btn['text'])) {
                    $module['button_text'] = $btn['text'];
                    $module['button_url'] = $btn['linkUrl'] ?? '#';
                }
                break;
                
            case 'divi/row-inner':
                // Soporte recursivo de sub-filas Bento Grid
                $cs = $attrs['module']['advanced']['columnStructure'] ?? [];
                if (isset($cs['desktop']['value'])) {
                    $module['column_structure'] = $cs['desktop']['value'];
                }
                
                $columns = [];
                foreach ($block['innerBlocks'] as $col_block) {
                    $col = $this->convert_column($col_block);
                    if ($col) {
                        $columns[] = $col;
                    }
                }
                if (!empty($columns)) {
                    $module['columns'] = $columns;
                }
                break;
                
            default:
                // Módulo genérico (ej. accordion, tabs, signup, contact-form)
                // Conserva hijos de forma nativa e intenta extraer contenido básico
                if (!empty($block['innerBlocks'])) {
                    $children = [];
                    foreach ($block['innerBlocks'] as $child_block) {
                        $child = $this->convert_module($child_block);
                        if ($child) {
                            $children[] = $child;
                        }
                    }
                    if (!empty($children)) {
                        $module['children'] = $children;
                    }
                }
                break;
        }
        
        return $module;
    }
    
    private function extract_common_styles(array $block, array &$out): void {
        $attrs = $block['attrs']['module'] ?? [];
        
        // 1. Extraer decoraciones (nativas de Divi 5)
        $style_keys = ['decoration', 'boxShadow', 'spacing', 'meta', 'advanced', 'headingFont', 'bodyFont', 'animation', 'transform'];
        foreach ($style_keys as $key) {
            if (isset($attrs[$key])) {
                // Limpiar estructuras desktop.value para hacer el JSON más amigable y corto
                $val = $attrs[$key];
                if ($key === 'decoration' && is_array($val)) {
                    $val = $this->unwrap_decoration($val);
                }
                if (!empty($val)) {
                    $out[$key] = $val;
                }
            }
        }
        
        // 2. Extraer clase e ID de htmlAttributes
        $html_attrs = $attrs['advanced']['htmlAttributes']['desktop']['value'] ?? [];
        if (!empty($html_attrs['class'])) {
            $out['module_class'] = $html_attrs['class'];
        }
        if (!empty($html_attrs['id'])) {
            $out['module_id'] = $html_attrs['id'];
        }
    }
    
    /**
     * Simplifica las estructuras "desktop => [value => X]" de decoración en el JSON
     */
    private function unwrap_decoration(array $dec): array {
        $clean = [];
        foreach ($dec as $k => $v) {
            if (is_array($v) && isset($v['desktop']['value']) && count($v) === 1) {
                $clean[$k] = $v['desktop']['value'];
            } else {
                $clean[$k] = $v;
            }
        }
        return $clean;
    }
    
    /**
     * Limpia recursivamente arreglos de valores nulos o vacíos para mantener el JSON pulido.
     */
    private function clean_array(array $arr): array {
        foreach ($arr as $k => $v) {
            if (is_array($v)) {
                $arr[$k] = $this->clean_array($v);
                if (empty($arr[$k]) && $arr[$k] !== 0 && $arr[$k] !== '0') {
                    unset($arr[$k]);
                }
            } elseif ($v === null || $v === '') {
                unset($arr[$k]);
            }
        }
        return $arr;
    }
    
    private function reverse_resolve_tokens(array $arr, array $color_tokens): array {
        foreach ($arr as $k => $v) {
            if (is_string($v)) {
                // 1. Detect global color ID (gcid-*) in string and replace entire value with the token
                if (preg_match('/gcid-([a-zA-Z0-9_-]+)/', $v, $m)) {
                    $key = $m[1];
                    // Map common customizer overrides to their short names
                    $customizer_slots = [
                        'primary-color' => 'primary',
                        'secondary-color' => 'secondary',
                        'heading-color' => 'heading',
                        'body-color' => 'body',
                        'link-color' => 'link'
                    ];
                    $mapped_key = $customizer_slots[$key] ?? $key;
                    
                    if (isset($color_tokens[$mapped_key]) || isset($customizer_slots[$key])) {
                        $arr[$k] = "{{design:color:{$mapped_key}}}";
                        continue;
                    }
                }
                
                // 2. Fallback: Re-abstraer colores hexadecimales planos a tokens
                foreach ($color_tokens as $token_name => $hex) {
                    if (strcasecmp($v, $hex) === 0) {
                        $v = "{{design:color:{$token_name}}}";
                        break;
                    }
                }
                
                $arr[$k] = $v;
            } elseif (is_array($v)) {
                $arr[$k] = $this->reverse_resolve_tokens($v, $color_tokens);
            }
        }
        return $arr;
    }
}

