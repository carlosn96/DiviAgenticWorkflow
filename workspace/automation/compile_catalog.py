#!/usr/bin/env python3
import os
import re
import json
import sys
from pathlib import Path

# Force CPU execution to keep it simple
os.environ["CUDA_VISIBLE_DEVICES"] = ""

SCRIPT_DIR = Path(__file__).parent.resolve()
DAW_ROOT = SCRIPT_DIR.parent.parent
CATALOG_DIR = DAW_ROOT / "workspace" / "catalog" / "jsons"
OUTPUT_DIR = DAW_ROOT / "workspace" / "sections" / "catalog"
DESIGN_SYSTEM_PATH = DAW_ROOT / "site" / "bibliotheca" / "design-system" / "divitheme.json"

# Divi 4 tag to Divi 5 block mapping
TAG_MAPPING = {
    'et_pb_section': 'divi/section',
    'et_pb_row': 'divi/row',
    'et_pb_column': 'divi/column',
    'et_pb_row_inner': 'divi/row-inner',
    'et_pb_column_inner': 'divi/column-inner',
    'et_pb_text': 'divi/text',
    'et_pb_heading': 'divi/heading',
    'et_pb_image': 'divi/image',
    'et_pb_button': 'divi/button',
    'et_pb_divider': 'divi/divider',
    'et_pb_blurb': 'divi/blurb',
    'et_pb_testimonial': 'divi/testimonial',
    'dipl_double_color_heading': 'divi/heading',
    'dipl_button': 'divi/button',
    'dipl_button_item': 'divi/button',
    'dipl_list': 'divi/icon-list',
    'dipl_list_item': 'divi/icon-list-item',
    'dipl_flipbox': 'divi/blurb',
    'dipl_floating_image': 'divi/image',
    'dipl_separator': 'divi/divider',
    'dipl_image_card': 'divi/blurb',
    'dipl_fancy_text': 'divi/text',
    'dipl_text_animator': 'divi/text',
}

TOKEN_RE = re.compile(r'(\[[a-zA-Z0-9_-]+[^\]]*?/?\]|\[/[a-zA-Z0-9_-]+\])')
ATTR_RE = re.compile(r'(\w+)\s*=\s*(?:"([^"\\]*(?:\\.[^"\\]*)*)"|\'([^\'\\]*(?:\\.[^\'\\]*)*)\'|([^\s]+))')

class ShortcodeNode:
    def __init__(self, tag, attrs, content_str=""):
        self.tag = tag
        self.attrs = attrs
        self.content_str = content_str
        self.children = []

def parse_attrs(attr_str):
    attrs = {}
    for m in ATTR_RE.finditer(attr_str):
        key = m.group(1)
        val = m.group(2) or m.group(3) or m.group(4) or ""
        attrs[key] = val
    return attrs

def parse_shortcodes(text):
    parts = TOKEN_RE.split(text)
    root = ShortcodeNode("root", {})
    stack = [root]

    for part in parts:
        if not part.strip():
            continue
        if part.startswith("[") and part.endswith("]"):
            if part.startswith("[/"):
                # Closing tag
                tag_name = part[2:-1].strip()
                # Find matching tag on stack
                if len(stack) > 1:
                    stack.pop()
            else:
                # Opening or self-closing
                tag_content = part[1:-1].strip()
                is_self_closing = tag_content.endswith("/")
                if is_self_closing:
                    tag_content = tag_content[:-1].strip()
                
                space_idx = tag_content.find(" ")
                if space_idx != -1:
                    tag_name = tag_content[:space_idx]
                    attr_str = tag_content[space_idx+1:]
                else:
                    tag_name = tag_content
                    attr_str = ""
                
                attrs = parse_attrs(attr_str)
                node = ShortcodeNode(tag_name, attrs)
                stack[-1].children.append(node)
                
                # If not self-closing and not a known self-closing tag
                if not is_self_closing and tag_name not in ('et_pb_divider', 'dipl_separator'):
                    stack.append(node)
        else:
            # Plain text
            if len(stack) > 0:
                stack[-1].content_str += part.strip()
                
    return root.children

# Hex to RGB
def hex_to_rgb(hex_str):
    hex_str = hex_str.strip().lstrip('#')
    if len(hex_str) == 3:
        hex_str = ''.join(c*2 for c in hex_str)
    if len(hex_str) == 6:
        try:
            return int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16)
        except ValueError:
            return None
    return None

def rgb_to_lab(r, g, b):
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    def linearize(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = linearize(r), linearize(g), linearize(b)
    x = r * 0.4124564 + g * 0.3575761 + b * 0.1804375
    y = r * 0.2126729 + g * 0.7151522 + b * 0.0721750
    z = r * 0.0193339 + g * 0.1191920 + b * 0.9503041
    xn, yn, zn = 0.95047, 1.0, 1.08883
    x, y, z = x / xn, y / yn, z / zn
    def f(t):
        return t ** (1/3) if t > 0.008856 else (903.3 * t + 16) / 116
    fx, fy, fz = f(x), f(y), f(z)
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))

def cie76(lab1, lab2):
    return ((lab1[0]-lab2[0])**2 + (lab1[1]-lab2[1])**2 + (lab1[2]-lab2[2])**2) ** 0.5

def color_distance(rgb1, rgb2):
    return cie76(rgb_to_lab(*rgb1), rgb_to_lab(*rgb2))

def find_closest_brand_color(rgb, brand_colors):
    closest_token = "ink"
    closest_dist = 999999.0
    closest_rgb = (0,0,0)
    for token, hex_val in brand_colors.items():
        b_rgb = hex_to_rgb(hex_val)
        if b_rgb:
            dist = color_distance(rgb, b_rgb)
            if dist < closest_dist:
                closest_dist = dist
                closest_token = token
                closest_rgb = b_rgb
    return closest_token, closest_rgb

def resolve_color(color_val, brand_colors):
    if not color_val or color_val in ('transparent', 'rgba(0,0,0,0)'):
        return color_val
    
    # Check if rgba
    rgba_match = re.match(r'rgba?\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*([\d\.]+)\s*)?\)', color_val)
    if rgba_match:
        r, g, b = int(rgba_match.group(1)), int(rgba_match.group(2)), int(rgba_match.group(3))
        a = float(rgba_match.group(4)) if rgba_match.group(4) is not None else 1.0
        closest_token, closest_rgb = find_closest_brand_color((r, g, b), brand_colors)
        if a == 1.0:
            return f"{{{{design:color:{closest_token}}}}}"
        else:
            return f"rgba({closest_rgb[0]},{closest_rgb[1]},{closest_rgb[2]},{a})"
            
    # Check if hex
    hex_match = re.match(r'^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$', color_val)
    if hex_match:
        rgb = hex_to_rgb(color_val)
        if rgb:
            closest_token, _ = find_closest_brand_color(rgb, brand_colors)
            return f"{{{{design:color:{closest_token}}}}}"
            
    return color_val

def parse_padding_margin(val):
    parts = val.split('|')
    res = {}
    keys = ['top', 'right', 'bottom', 'left']
    for idx, k in enumerate(keys):
        if idx < len(parts) and parts[idx] and parts[idx] != 'on' and parts[idx] != 'false':
            res[k] = parts[idx]
    return res

def parse_border_radii(val):
    parts = val.split('|')
    if len(parts) >= 5:
        return {
            "topLeft": parts[1],
            "topRight": parts[2],
            "bottomRight": parts[3],
            "bottomLeft": parts[4]
        }
    return None

def build_decoration(attrs, brand_colors):
    dec = {}
    
    # Background color
    bg_color = attrs.get('background_color')
    if bg_color:
        dec.setdefault('background', {}).setdefault('desktop', {}).setdefault('value', {})['color'] = resolve_color(bg_color, brand_colors)
    
    # Background gradient
    if attrs.get('use_background_color_gradient') == 'on':
        start = attrs.get('background_color_gradient_start')
        end = attrs.get('background_color_gradient_end')
        direction = attrs.get('background_color_gradient_direction', '180deg')
        if not direction.endswith('deg') and direction.isdigit():
            direction = direction + 'deg'
        dec.setdefault('background', {}).setdefault('desktop', {}).setdefault('value', {})['gradient'] = {
            'enabled': 'on',
            'type': attrs.get('background_color_gradient_type', 'linear'),
            'direction': direction,
            'overlaysImage': attrs.get('background_color_gradient_overlays_image', 'on'),
            'stops': [
                {'color': resolve_color(start, brand_colors) if start else 'rgba(0,0,0,0.6)', 'position': '0%'},
                {'color': resolve_color(end, brand_colors) if end else 'rgba(0,0,0,0)', 'position': '100%'}
            ]
        }
        
    # Background Image
    bg_image = attrs.get('background_image')
    if bg_image:
        dec.setdefault('background', {}).setdefault('desktop', {}).setdefault('value', {})['image'] = {
            'url': bg_image,
            'size': attrs.get('background_size', 'cover'),
            'position': attrs.get('background_position', 'center center'),
            'repeat': attrs.get('background_repeat', 'no-repeat'),
            'parallax': {'enabled': attrs.get('parallax', 'off')}
        }

    # Spacing (Padding/Margin)
    padding_val = attrs.get('custom_padding')
    if padding_val:
        padding_map = parse_padding_margin(padding_val)
        if padding_map:
            dec.setdefault('spacing', {}).setdefault('desktop', {}).setdefault('value', {})['padding'] = padding_map
            
    margin_val = attrs.get('custom_margin')
    if margin_val:
        margin_map = parse_padding_margin(margin_val)
        if margin_map:
            dec.setdefault('spacing', {}).setdefault('desktop', {}).setdefault('value', {})['margin'] = margin_map

    # Borders
    border_radii_val = attrs.get('border_radii')
    if border_radii_val:
        radius_map = parse_border_radii(border_radii_val)
        if radius_map:
            dec.setdefault('border', {}).setdefault('desktop', {}).setdefault('value', {})['radius'] = radius_map
            
    border_width = attrs.get('border_width')
    border_color = attrs.get('border_color')
    if border_width or border_color:
        border_style = attrs.get('border_style', 'solid')
        dec.setdefault('border', {}).setdefault('desktop', {}).setdefault('value', {}).setdefault('styles', {})['all'] = {
            'style': border_style,
            'width': border_width if border_width else '1px',
            'color': resolve_color(border_color, brand_colors) if border_color else '{{design:color:parchment-200}}'
        }

    # Box Shadow
    shadow_style = attrs.get('box_shadow_style')
    if shadow_style and shadow_style != 'none':
        dec.setdefault('boxShadow', {}).setdefault('desktop', {}).setdefault('value', {})['style'] = shadow_style
        shadow_color = attrs.get('box_shadow_color')
        if shadow_color:
            dec['boxShadow']['desktop']['value']['color'] = resolve_color(shadow_color, brand_colors)

    return dec

def assign_column_indices(section_node, section_type):
    # Only assign indices for list-type sections
    if section_type not in ('features', 'testimonials', 'stats', 'gallery', 'team'):
        return {}
        
    column_indices = {}
    
    # Collect all columns in order
    all_columns = []
    def collect_columns(node):
        if node.tag in ('et_pb_column', 'et_pb_column_inner'):
            all_columns.append(node)
        for child in node.children:
            collect_columns(child)
            
    collect_columns(section_node)
    
    # Collect all rows (both outer and inner)
    rows = []
    def collect_rows(node):
        if node.tag in ('et_pb_row', 'et_pb_row_inner'):
            rows.append(node)
        for child in node.children:
            collect_rows(child)
    collect_rows(section_node)
    
    is_alternating_two_col = False
    if rows:
        two_col_rows = 0
        alternating_cols = 0
        for row in rows:
            cols = [c for c in row.children if c.tag in ('et_pb_column', 'et_pb_column_inner')]
            if len(cols) == 2:
                two_col_rows += 1
                def has_text_module(col_node):
                    for child in col_node.children:
                        if child.tag in ('et_pb_text', 'et_pb_heading', 'et_pb_blurb', 'dipl_double_color_heading', 'et_pb_testimonial'):
                            return True
                        if has_text_module(child):
                            return True
                    return False
                
                has_t0 = has_text_module(cols[0])
                has_t1 = has_text_module(cols[1])
                if has_t0 != has_t1:  # one has text, one doesn't
                    alternating_cols += 1
                    
        if two_col_rows > 0 and (alternating_cols / two_col_rows) >= 0.5:
            is_alternating_two_col = True

    if is_alternating_two_col:
        # In alternating 2-column layout, each row represents exactly one item.
        row_idx = 0
        for row in rows:
            cols = [c for c in row.children if c.tag in ('et_pb_column', 'et_pb_column_inner')]
            if len(cols) == 2:
                for col in cols:
                    column_indices[id(col)] = row_idx
                row_idx += 1
    else:
        # Standard layout: each column is a separate item.
        col_global_idx = 0
        for row in rows:
            cols = [c for c in row.children if c.tag in ('et_pb_column', 'et_pb_column_inner')]
            if len(cols) > 1:
                for col in cols:
                    column_indices[id(col)] = col_global_idx
                    col_global_idx += 1
                    
    return column_indices

def translate_node(node, brand_colors, col_idx=0, num_cols=1, section_type='generic', column_indices=None):
    tag = node.tag
    attrs = node.attrs
    content = node.content_str.strip()

    block_type = TAG_MAPPING.get(tag, 'divi/placeholder')
    
    # Standard base block
    res = {
        'type': block_type,
        'module': block_type
    }

    # Extract styling parameters
    dec = build_decoration(attrs, brand_colors)
    if dec:
        res['decoration'] = dec

    # Children / Rows / Columns mapping
    if tag == 'et_pb_section':
        res['type'] = attrs.get('type', 'regular')
        res['rows'] = []
        
        # Calculate column indices for the entire section
        column_indices = assign_column_indices(node, section_type)
        
        # Support specialty sections (direct et_pb_column children) by wrapping them in a synthesized row
        direct_columns = [child for child in node.children if child.tag == 'et_pb_column']
        if direct_columns:
            # Map column types like "1_2 specialty_columns=2" to just "1_2" or "4_4" to avoid invalid structures
            clean_types = []
            for col in direct_columns:
                t = col.attrs.get('type', '4_4')
                # If it has spaces like "1_2 specialty_columns=2", take the first part
                if ' ' in t:
                    t = t.split(' ')[0]
                clean_types.append(t)
            row_attrs = {
                'column_structure': ','.join(clean_types)
            }
            synthesized_row = ShortcodeNode('et_pb_row', row_attrs)
            synthesized_row.children = direct_columns
            res['rows'].append(translate_node(synthesized_row, brand_colors, section_type=section_type, column_indices=column_indices))
        else:
            for child in node.children:
                if child.tag == 'et_pb_row':
                    res['rows'].append(translate_node(child, brand_colors, section_type=section_type, column_indices=column_indices))
                
    elif tag == 'et_pb_row' or tag == 'et_pb_row_inner':
        col_struct = attrs.get('column_structure', '4_4')
        res['column_structure'] = col_struct
        res['columns'] = []
        cols = col_struct.split(',')
        num_cols = len(cols)
        
        for c_idx, child in enumerate(node.children):
            if child.tag in ('et_pb_column', 'et_pb_column_inner'):
                res['columns'].append(translate_node(child, brand_colors, col_idx=c_idx, num_cols=num_cols, section_type=section_type, column_indices=column_indices))
                
    elif tag in ('et_pb_column', 'et_pb_column_inner'):
        res['type'] = attrs.get('type', '4_4')
        res['modules'] = []
        
        # Look up column's index in the global column_indices map
        col_id = id(node)
        col_item_idx = column_indices.get(col_id, col_idx) if column_indices else col_idx
        
        for child in node.children:
            translated = translate_node(child, brand_colors, col_idx=col_item_idx, num_cols=num_cols, section_type=section_type, column_indices=column_indices)
            if translated:
                res['modules'].append(translated)
                
    else:
        # It's a module
        # Set alignment
        align = attrs.get('align') or attrs.get('button_alignment')
        if align:
            res.setdefault('decoration', {}).setdefault('layout', {}).setdefault('desktop', {}).setdefault('value', {})['textAlign'] = align

        # Module-specific property mappings
        if block_type == 'divi/text':
            res['content'] = content if content else (attrs.get('content') or "")
            # Typography replacements
            text_color = attrs.get('text_text_color')
            text_size = attrs.get('text_font_size')
            if text_color or text_size:
                res.setdefault('bodyFont', {}).setdefault('desktop', {}).setdefault('value', {})['fontFamily'] = '{{design:font:body}}'
                if text_color:
                    res['bodyFont']['desktop']['value']['color'] = resolve_color(text_color, brand_colors)
                if text_size:
                    res['bodyFont']['desktop']['value']['size'] = text_size

        elif block_type == 'divi/heading':
            heading_text = content
            if tag == 'dipl_double_color_heading':
                pre = attrs.get('heading_pre_part', '')
                main = attrs.get('heading_main_part', '')
                post = attrs.get('heading_post_part', '')
                heading_text = f"{pre} {main} {post}".strip()
            res['content'] = heading_text if heading_text else (attrs.get('title') or "")
            res['level'] = attrs.get('level', 'h2')

        elif block_type == 'divi/image':
            res['src'] = attrs.get('src') or attrs.get('image_url') or ""
            res['alt'] = attrs.get('alt') or ""

        elif block_type == 'divi/button':
            res['button_text'] = attrs.get('button_text') or content or "Acción"
            res['button_url'] = attrs.get('button_url') or "#"

        elif block_type == 'divi/divider':
            res['show_divider'] = attrs.get('show_divider', 'on')

        elif block_type == 'divi/blurb':
            res['title'] = attrs.get('title') or ""
            res['content'] = content or attrs.get('content') or ""
            res['src'] = attrs.get('image') or ""

        elif block_type == 'divi/icon-list':
            res['children'] = []
            for child in node.children:
                if child.tag == 'dipl_list_item':
                    res['children'].append({
                        'type': 'divi/icon-list-item',
                        'module': 'divi/icon-list-item',
                        'content': child.content_str.strip() or child.attrs.get('content', '')
                    })

        # Apply slot placeholders for content text
        apply_slot_placeholders(res, col_idx, num_cols, section_type)

    return res

def apply_slot_placeholders(res, col_idx, num_cols, section_type):
    module = res.get('module')
    if not module:
        return

    # Check for lists (features, testimonials, stats)
    if num_cols > 1 and section_type in ('features', 'testimonials', 'stats', 'gallery', 'team'):
        if module == 'divi/heading' or module == 'divi/blurb':
            # Heading title
            if 'title' in res:
                res['title'] = f"{{{{slot:{section_type}[{col_idx}].title}}}}"
            elif 'content' in res:
                res['content'] = f"{{{{slot:{section_type}[{col_idx}].title}}}}"
        elif module == 'divi/text':
            res['content'] = f"{{{{slot:{section_type}[{col_idx}].text}}}}"
        elif module == 'divi/image':
            res['src'] = f"{{{{slot:{section_type}[{col_idx}].image}}}}"
        elif module == 'divi/button':
            res['button_text'] = f"{{{{slot:{section_type}[{col_idx}].btn_text}}}}"
            res['button_url'] = f"{{{{slot:{section_type}[{col_idx}].btn_url}}}}"
    else:
        # Non-list standard slots
        if module == 'divi/heading':
            res['content'] = "{{slot:title}}"
        elif module == 'divi/text':
            # Check length to see if it's subtitle/eyebrow or body text
            content_len = len(res.get('content', ''))
            if content_len > 0 and content_len < 25:
                # Eyebrow
                res['content'] = "{{slot:eyebrow}}"
            else:
                res['content'] = "{{slot:text}}"
        elif module == 'divi/button':
            res['button_text'] = "{{slot:btn_primary_text}}"
            res['button_url'] = "{{slot:btn_primary_url}}"

def main():
    print("[COMPILE] Loading design system...")
    if not DESIGN_SYSTEM_PATH.exists():
        print(f"Error: Design system not found: {DESIGN_SYSTEM_PATH}", file=sys.stderr)
        return 1
        
    ds = json.loads(DESIGN_SYSTEM_PATH.read_text('utf-8'))
    brand_colors = ds.get('tokens', {}).get('color', {})
    
    if not CATALOG_DIR.exists():
        print(f"Error: Catalog directory not found: {CATALOG_DIR}", file=sys.stderr)
        return 1
        
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    total = 0
    errors = 0
    
    # Iterate through all subdirectories
    subdirs = sorted([d for d in CATALOG_DIR.iterdir() if d.is_dir()])
    print(f"[COMPILE] Translating {len(subdirs)} templates...")
    
    for subdir in subdirs:
        json_files = list(subdir.glob('*.json'))
        if not json_files:
            continue
            
        json_path = json_files[0]
        folder_name = subdir.name
        
        # Determine section type based on folder name
        section_type = 'generic'
        name_lower = folder_name.lower()
        
        # Add workspace folder to system path to import extract_patterns
        sys.path.append(str(DAW_ROOT / "workspace"))
        # Score each category
        from extract_patterns import SECTION_TYPE_KEYWORDS, categorize_section, extract_divi_info
        
        try:
            raw = json_path.read_text('utf-8')
            data = json.loads(raw)
            
            # Extract shortcode content
            inner = data.get('data', {})
            shortcode_text = ''
            for val in inner.values():
                if isinstance(val, str):
                    shortcode_text += val
                    
            if not shortcode_text.strip():
                continue
                
            # Extract structural info for categorization
            info = extract_divi_info(shortcode_text, folder_name, json_path)
            section_type = categorize_section(folder_name, info)
            
            # Parse shortcodes to tree
            nodes = parse_shortcodes(shortcode_text)
            if not nodes:
                continue
                
            # We want to find the first section node
            section_node = None
            for n in nodes:
                if n.tag == 'et_pb_section':
                    section_node = n
                    break
            
            if not section_node:
                # If no section node is found at root, wrap in a default one
                section_node = ShortcodeNode("et_pb_section", {"type": "regular"})
                section_node.children = nodes
                
            # Translate section tree to Divi 5 schema
            translated_section = translate_node(section_node, brand_colors, section_type=section_type)
            
            # Output layout section JSON
            out_path = OUTPUT_DIR / f"{folder_name}.section.json"
            out_path.write_text(
                json.dumps(translated_section, indent=2, ensure_ascii=False),
                'utf-8'
            )
            total += 1
            
            if total % 100 == 0:
                print(f"[COMPILE]  Translated {total} elements...")
                
        except Exception as e:
            errors += 1
            if errors <= 5:
                print(f"[WARN] Error compiling {folder_name}: {e}", file=sys.stderr)
                import traceback
                traceback.print_exc()

    print(f"[COMPILE] Success! Pre-compiled {total} layout templates in Divi 5 (with {errors} errors).")
    return 0

if __name__ == '__main__':
    sys.exit(main())
