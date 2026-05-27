<?php
// Divi 5 Blocks → Schema JSON converter
// Reads remote Divi 5 block content and generates a proper schema JSON
// Handles unsupported modules (number-counter, blurb) by rendering to HTML via divi/code

namespace DAC\Core;

class BlocksToSchema {
    
    public function convert(string $block_content): array {
        $blocks = parse_blocks($block_content);
        $schema = ['sections' => []];
        
        // Find sections inside divi/placeholder (or directly)
        $sections = $this->find_sections($blocks);
        
        foreach ($sections as $section_block) {
            $section_data = $this->convert_section($section_block);
            if ($section_data) {
                $schema['sections'][] = $section_data;
            }
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
        $section = ['type' => $attrs['advanced']['type']['desktop']['value'] ?? 'regular'];
        
        // Extract decoration (background, spacing, layout)
        $decoration = [];
        $raw_deco = $attrs['decoration'] ?? [];
        foreach (['background', 'spacing', 'layout'] as $key) {
            if (isset($raw_deco[$key]['desktop']['value'])) {
                $decoration[$key] = $raw_deco[$key]['desktop']['value'];
            }
        }
        if (!empty($decoration)) {
            $section['decoration'] = $decoration;
        }
        
        // Extract class from section-level htmlAttributes
        $class = $attrs['advanced']['htmlAttributes']['desktop']['value']['class'] ?? '';
        if ($class) {
            $section['module_class'] = $class;
        }
        
        // Convert rows
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
        
        // Extract column structure with breakpoints
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
        
        // Convert columns
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
        if ($block['blockName'] !== 'divi/column') return null;
        
        $attrs = $block['attrs']['module'] ?? [];
        $type = $attrs['advanced']['type']['desktop']['value'] ?? '';
        if (!$type) return null;
        
        $column = ['type' => $type];
        
        // Convert modules
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
        $attrs = $block['attrs'];
        $module = ['module' => $name];
        
        // Extract class
        $class = $attrs['module']['advanced']['htmlAttributes']['desktop']['value']['class'] ?? '';
        if ($class) {
            $module['module_class'] = $class;
        }
        
        switch ($name) {
            case 'divi/text':
            case 'divi/code':
                $content = $attrs['content']['innerContent']['desktop']['value'] ?? '';
                if ($content) {
                    $module['content'] = $content;
                }
                break;
                
            case 'divi/image':
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
                
            case 'divi/number-counter':
            case 'divi/blurb':
                // Convert unsupported modules to divi/code by rendering
                $module['module'] = 'divi/code';
                $rendered = render_block($block);
                if ($rendered) {
                    $module['content'] = $rendered;
                } else {
                    $module['content'] = '<!-- Unsupported module -->';
                }
                break;
                
            default:
                // Unknown module, try to render
                $rendered = render_block($block);
                if ($rendered) {
                    $module['module'] = 'divi/code';
                    $module['content'] = $rendered;
                } else {
                    return null; // Skip unsupported
                }
        }
        
        return $module;
    }
}
