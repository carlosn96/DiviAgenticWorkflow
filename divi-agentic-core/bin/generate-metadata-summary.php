<?php
/**
 * Generates a compact JSON summary from Divi 5's official metadata files.
 * Output: workspace/divi-metadata/blocks-summary.json
 * 
 * This extracts ONLY the essential info (name, slug, category, attributes, render paths)
 * from the 2.6MB metadata file, producing a ~200KB reference that's:
 *   1) Consumable by the DAW skill (architect/designer reference)
 *   2) Fast to load without parsing the full metadata
 *   3) Human-readable for schema authoring
 */

$meta_file = __DIR__ . '/../data/_all_modules_metadata.php';
$render_file = __DIR__ . '/../data/_all_modules_default_render_attributes.php';

if (!file_exists($meta_file)) {
    die("Metadata file not found: $meta_file\n");
}

echo "Reading metadata... ";
$meta = include $meta_file;
echo count($meta) . " modules found.\n";

$render = file_exists($render_file) ? include $render_file : [];
echo count($render) . " render attribute sets found.\n";

$summary = [];

foreach ($meta as $slug => $mod) {
    $entry = [
        'name' => $mod['name'] ?? "divi/$slug",
        'slug' => $slug,
        'title' => $mod['title'] ?? '',
        'category' => $mod['category'] ?? 'unknown',
        'childModule' => $mod['childModuleName'] ?? null,
        'children' => $mod['childrenName'] ?? [],
        'parent' => $mod['parentModuleName'] ?? null,
        'd4Shortcode' => $mod['d4Shortcode'] ?? null,
    ];

    // Compact attributes: type, default, render path, settings groups
    $attrs = [];
    if (isset($mod['attributes'])) {
        foreach ($mod['attributes'] as $attr_name => $attr_def) {
            $a = [];
            
            // Type
            $a['type'] = $attr_def['type'] ?? 'object';
            
            // Default (simplified)
            if (isset($attr_def['default'])) {
                $default = $attr_def['default'];
                if (is_string($default)) {
                    $a['default'] = mb_strlen($default) > 100 ? mb_substr($default, 0, 100) . '...' : $default;
                } elseif (is_bool($default)) {
                    $a['default'] = $default ? 'true' : 'false';
                } elseif (is_array($default)) {
                    $flat = array_filter($default, function($v) { return !is_array($v) && $v !== null; });
                    $a['default'] = !empty($flat) ? json_encode($flat) : null;
                } else {
                    $a['default'] = $default;
                }
            }
            
            // Render path from default_render_attributes
            if (isset($render[$slug][$attr_name])) {
                $a['render'] = $render[$slug][$attr_name];
            }
            
            // Settings groups (structure hint)
            if (isset($attr_def['settings'])) {
                $a['settings'] = [];
                foreach ($attr_def['settings'] as $group => $gdef) {
                    $info = [];
                    if (isset($gdef['groupType'])) {
                        $info['groupType'] = $gdef['groupType'];
                    }
                    if (isset($gdef['items'])) {
                        $info['items'] = array_keys($gdef['items']);
                        // Show types for innerContent items
                        if ($group === 'innerContent' && $info['groupType'] === 'group-items') {
                            foreach ($gdef['items'] as $ik => $iv) {
                                $info['item_types'][$ik] = $iv['subName'] ?? $ik;
                            }
                        }
                    }
                    $a['settings'][$group] = $info;
                }
            }
            
            // inlineEditor hint
            if (!empty($attr_def['inlineEditor'])) {
                $a['editor'] = $attr_def['inlineEditor'];
            }
            
            // tagName hint (for HTML elements)
            if (!empty($attr_def['tagName'])) {
                $a['tag'] = $attr_def['tagName'];
            }
            
            // selector CSS
            if (!empty($attr_def['selector'])) {
                $a['selector'] = $attr_def['selector'];
            }
            
            $attrs[$attr_name] = $a;
        }
    }
    
    $entry['attributes'] = $attrs;
    $summary[$slug] = $entry;
}

// Write output
$out_dir = __DIR__ . '/../../workspace/divi-metadata';
if (!is_dir($out_dir)) {
    mkdir($out_dir, 0755, true);
}

$out_file = "$out_dir/blocks-summary.json";
$json = json_encode($summary, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
file_put_contents($out_file, $json);

$size_kb = round(strlen($json) / 1024);
echo "Written: $out_file ($size_kb KB)\n";
echo "Done.\n";
