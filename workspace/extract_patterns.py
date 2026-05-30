#!/usr/bin/env python3
"""
extract_patterns.py — One-time extractor that analyzes 892 Divi 4 catalog templates
and produces design-patterns.json for the orquestador.

Output: design-patterns.json (~10KB) with:
  - composition_archetypes: what modules/structure co-occur
  - color_palettes: color clusters found
  - module_affinity: which modules appear together
  - section_types: categorized by structural fingerprint

This is destilled design intelligence from human-made pages.
No ML model, no embeddings, no 500MB dependencies.
"""

import os
import re
import json
import sys
from pathlib import Path
from collections import Counter, defaultdict
from html import unescape

CATALOG_DIR = Path(__file__).parent / "catalog" / "jsons"
OUTPUT_PATH = Path(__file__).parent / "design-patterns.json"

# Divi 4 module name → category mapping
DIVI4_CATEGORIES = {
    'et_pb_section': 'section',
    'et_pb_row': 'row',
    'et_pb_column': 'column',
    'et_pb_text': 'text',
    'et_pb_heading': 'heading',
    'et_pb_image': 'image',
    'et_pb_blurb': 'blurb',
    'et_pb_button': 'button',
    'et_pb_countdown_timer': 'countdown',
    'et_pb_counter': 'counter',
    'et_pb_number_counter': 'number-counter',
    'et_pb_pricing_tables': 'pricing',
    'et_pb_testimonial': 'testimonial',
    'et_pb_slider': 'slider',
    'et_pb_blog': 'blog',
    'et_pb_accordion': 'accordion',
    'et_pb_toggle': 'toggle',
    'et_pb_tabs': 'tabs',
    'et_pb_video': 'video',
    'et_pb_audio': 'audio',
    'et_pb_map': 'map',
    'et_pb_divider': 'divider',
    'et_pb_signup': 'signup',
    'et_pb_contact_form': 'contact-form',
    'et_pb_post_slider': 'post-slider',
    'et_pb_post_title': 'post-title',
    'et_pb_post_nav': 'post-nav',
    'et_pb_search': 'search',
    'et_pb_social_media_follow': 'social-follow',
    'et_pb_fullwidth_slider': 'fullwidth-slider',
    'et_pb_fullwidth_header': 'fullwidth-header',
    'et_pb_fullwidth_menu': 'fullwidth-menu',
    'et_pb_fullwidth_code': 'fullwidth-code',
    'et_pb_code': 'code',
    'et_pb_sidebar': 'sidebar',
    'et_pb_comments': 'comments',
    'et_pb_portfolio': 'portfolio',
    'et_pb_gallery': 'gallery',
    'et_pb_team_member': 'team-member',
    'et_pb_pricing_table': 'pricing-table',
    'et_pb_circle_counter': 'circle-counter',
    'et_pb_progress_bar': 'progress-bar',
    'et_pb_filterable_portfolio': 'filterable-portfolio',
    'et_pb_shop': 'shop',
    'et_pb_login': 'login',
    'et_pb_menu': 'menu',
    'et_pb_icon': 'icon',
    'et_pb_social_media_follow_network': 'social-network',
    'dipl_text_animator': 'text-animator',
    'dipl_button': 'dipl-button',
    'dipl_button_item': 'dipl-button-item',
    'dipl_double_color_heading': 'double-heading',
    'dipl_image_hotspot': 'image-hotspot',
    'dipl_image_card': 'image-card',
    'dipl_image_accordion': 'image-accordion',
    'dipl_modal_popup': 'modal-popup',
    'dipl_team_member': 'dipl-team',
    'dipl_testimonial': 'dipl-testimonial',
    'dipl_logo_slider': 'logo-slider',
    'dipl_pricing_table': 'dipl-pricing',
    'dipl_flipbox': 'flipbox',
    'dipl_breadcrumb': 'breadcrumb',
    'dipl_timeline': 'timeline',
    'dipl_timeline_item': 'timeline-item',
    'dipl_faq_schema': 'faq-schema',
    'dipl_gravity_form_styler': 'gravity-form',
    'dipl_contact_form_7_styler': 'cf7-form',
    'dipl_caldera_form_styler': 'caldera-form',
    'dipl_wpforms_styler': 'wpforms',
}

SECTION_TYPE_KEYWORDS = {
    'hero': ['hero', 'heroes', 'landing', 'cover', 'intro', 'banner', 'header', 'under construction', 'coming soon'],
    'about': ['about', 'story', 'who we are', 'our story', 'our mission'],
    'features': ['feature', 'features', 'service', 'services', 'what we do', 'we offer', 'why choose', 'our expertise', 'capabilities', 'offering', 'offerings'],
    'testimonials': ['testimonial', 'testimonials', 'review', 'reviews', 'client', 'clients', 'customer say', 'customer says', 'feedback', 'people say', 'love'],
    'cta': ['call to action', 'cta', 'ctas', 'get started', 'sign up', 'join', 'register', 'book'],
    'pricing': ['pricing', 'pricings', 'plan', 'plans', 'package', 'packages', 'subscription', 'subscriptions', 'membership', 'memberships', 'tier', 'tiers'],
    'team': ['team', 'teams', 'member', 'members', 'people', 'expert', 'experts', 'trainer', 'trainers', 'staff', 'founder', 'founders'],
    'footer': ['footer', 'footers', 'bottom'],
    'contact': ['contact', 'contacts', 'contacting', 'contacted', 'get in touch', 'reach', 'location', 'locations'],
    'gallery': ['gallery', 'galleries', 'portfolio', 'portfolios', 'project', 'projects', 'work', 'works', 'showcase', 'showcases', 'collection', 'collections'],
    'blog': ['blog', 'blogs', 'news', 'article', 'articles', 'post', 'posts', 'update', 'updates'],
    'faq': ['faq', 'faqs', 'question', 'questions', 'doubt', 'doubts', 'answer', 'answers'],
    'stats': ['counter', 'counters', 'stat', 'stats', 'number', 'numbers', 'achievement', 'achievements', 'milestone', 'milestones'],
    'countdown': ['countdown', 'countdowns', 'coming soon', 'sale', 'offer', 'deal', 'limited'],
    'logos': ['logo', 'logos', 'brand', 'brands', 'partner', 'partners', 'client logo', 'client logos', 'collaborator', 'collaborators'],
    'timeline': ['timeline', 'timelines', 'process', 'processes', 'journey', 'journeys', 'roadmap', 'roadmaps', 'history'],
    'product': ['product', 'products', 'shop', 'shops', 'store', 'stores', 'item', 'items', 'collection', 'collections', 'category', 'categories'],
}

def parse_shortcode_attr_value(value: str) -> str:
    """Extract the actual value from a shortcode attribute, handling edge cases."""
    if value.startswith('"') and value.endswith('"'):
        value = value[1:-1]
    if value.startswith("'") and value.endswith("'"):
        value = value[1:-1]
    return unescape(value)

SHORTCODE_RE = re.compile(r'\[(\w+)([^\]]*)\](.*?)\[\/\1\]', re.DOTALL)
SELFCLOSING_RE = re.compile(r'\[(\w+)([^\]]*?)/\]')
ATTR_RE = re.compile(r'(\w+)\s*=\s*("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'|(?:[^\s"\']+))')

def extract_divi_info(shortcode_text: str, dir_name: str, file_path: str) -> dict:
    """Extract structural info from Divi 4 shortcodes."""
    info = {
        'source': f'{dir_name}/{os.path.basename(file_path)}',
        'dir_name': dir_name,
        'modules': [],
        'column_structures': [],
        'bg_colors': [],
        'text_colors': [],
        'section_count': 0,
        'row_count': 0,
        'module_count': 0,
        'has_divider': False,
        'has_background_gradient': False,
        'has_background_image': False,
        'third_party_modules': [],
    }

    def parse_attrs(attr_str: str) -> dict:
        attrs = {}
        for match in ATTR_RE.finditer(attr_str):
            key = match.group(1)
            val = parse_shortcode_attr_value(match.group(2))
            attrs[key] = val
        return attrs

    def walk(text: str):
        for match in SHORTCODE_RE.finditer(text):
            tag = match.group(1)
            attr_str = match.group(2)
            content = match.group(3)
            attrs = parse_attrs(attr_str)
            
            category = DIVI4_CATEGORIES.get(tag, 'other')
            info['modules'].append({
                'tag': tag,
                'category': category,
                'attrs': attrs,
            })
            info['module_count'] += 1

            if tag == 'et_pb_section':
                info['section_count'] += 1
                if attrs.get('bottom_divider_style', '') or attrs.get('top_divider_style', ''):
                    info['has_divider'] = True
                if 'background_color' in attrs:
                    info['bg_colors'].append(attrs['background_color'])
                if attrs.get('background_color_gradient_start', ''):
                    info['has_background_gradient'] = True
                if attrs.get('background_image', ''):
                    info['has_background_image'] = True
            elif tag == 'et_pb_row':
                info['row_count'] += 1
                col_struct = attrs.get('column_structure', '4_4')
                info['column_structures'].append(col_struct)
            elif tag == 'et_pb_text':
                if 'text_color' in attrs:
                    info['text_colors'].append(attrs['text_color'])
                if 'header_text_color' in attrs and attrs['header_text_color']:
                    info['text_colors'].append(attrs['header_text_color'])
            
            # Track third-party modules
            if tag.startswith('dipl_') or (not tag.startswith('et_pb_') and not tag.startswith('/')):
                if tag not in ['et_pb_section', 'et_pb_row', 'et_pb_column']:
                    info['third_party_modules'].append(tag)
            
            walk(content)

        # Also check for self-closing tags
        for match in SELFCLOSING_RE.finditer(text):
            tag = match.group(1)
            attr_str = match.group(2)
            category = DIVI4_CATEGORIES.get(tag, 'other')
            info['modules'].append({
                'tag': tag,
                'category': category,
                'attrs': parse_attrs(attr_str),
            })
            info['module_count'] += 1

    walk(shortcode_text)
    return info

def categorize_section(dir_name: str, info: dict) -> str:
    """Categorize a section by its directory name and module fingerprint."""
    name_lower = dir_name.lower()
    
    # Score each category by keyword overlap (name is highly authoritative)
    scores = {}
    for cat, keywords in SECTION_TYPE_KEYWORDS.items():
        score = 0
        for kw in keywords:
            # Match only whole words to avoid sub-word matching (like "working" matching "work")
            pattern = r'\b' + re.escape(kw) + r'\b'
            if re.search(pattern, name_lower):
                if name_lower.startswith(kw):
                    score += 15  # Directory explicitly starts with category keyword
                # Check if it ends with the keyword (optionally followed by common section terms)
                elif re.search(r'\b' + re.escape(kw) + r'(?:\s+(?:section|block|layout|page|module|template|us|me))?\s*$', name_lower):
                    score += 15  # Directory explicitly ends with category keyword
                else:
                    score += 5   # Word match
        if score > 0:
            scores[cat] = score
    
    # Boost by module fingerprint
    module_categories = [m['category'] for m in info.get('modules', [])]
    cat_counts = Counter(module_categories)
    
    fingerprint_boosts = {
        'testimonials': ['testimonial', 'dipl-testimonial'],
        'pricing': ['pricing', 'pricing-table', 'dipl-pricing'],
        'team': ['team-member', 'dipl-team'],
        'features': ['blurb', 'flipbox'],
        'stats': ['counter', 'number-counter', 'circle-counter', 'progress-bar'],
        'cta': ['signup', 'button'],
        'gallery': ['gallery', 'image', 'image-accordion', 'image-card'],
        'blog': ['blog', 'post-slider', 'post-title'],
        'faq': ['faq-schema', 'accordion', 'toggle'],
        'hero': ['heading', 'text-animator'],
        'logos': ['logo-slider'],
        'timeline': ['timeline', 'timeline-item'],
    }
    
    for cat, modules in fingerprint_boosts.items():
        for mod in modules:
            if cat_counts.get(mod, 0) > 0:
                scores[cat] = scores.get(cat, 0) + 3
    
    # Sections with single row and few modules are often hero sections
    if info.get('section_count', 0) == 1 and info.get('row_count', 0) <= 2 and info.get('module_count', 0) <= 5:
        scores['hero'] = scores.get('hero', 0) + 1
    
    if not scores:
        return 'generic'
    
    return max(scores, key=scores.get)

def extract_color_palettes(infos: list) -> dict:
    """Extract common color palettes from background colors."""
    color_counter = Counter()
    for info in infos:
        for c in info['bg_colors']:
            if c and c != 'rgba(0,0,0,0)' and c != 'transparent':
                color_counter[c] += 1
        for c in info['text_colors']:
            if c and c != 'rgba(0,0,0,0)' and c != 'transparent':
                color_counter[c] += 1
    
    # Group by color families (simplified: just return top colors)
    top_colors = color_counter.most_common(30)
    return {
        'most_common_bg': [{'color': c, 'count': n} for c, n in top_colors if n > 1],
        'total_unique': len(color_counter),
    }

def extract_composition_archetypes(infos: list) -> list:
    """Extract common composition patterns."""
    # Group by section category and find top module patterns
    by_category = defaultdict(list)
    for info in infos:
        cat = info['section_type']
        module_sequence = tuple(m['category'] for m in info['modules'] 
                              if m['category'] not in ('section', 'row', 'column'))
        by_category[cat].append({
            'modules': module_sequence,
            'column_structures': info['column_structures'],
            'has_divider': info['has_divider'],
            'has_bg_gradient': info['has_background_gradient'],
        })
    
    archetypes = []
    for cat, items in by_category.items():
        if len(items) < 3:
            continue
        # Find most common module sequences
        seq_counter = Counter()
        col_struct_counter = Counter()
        divider_count = 0
        gradient_count = 0
        
        for item in items:
            seq_counter[item['modules']] += 1
            for cs in item['column_structures']:
                col_struct_counter[cs] += 1
            if item['has_divider']:
                divider_count += 1
            if item['has_bg_gradient']:
                gradient_count += 1
        
        top_seq = seq_counter.most_common(3)
        top_col = col_struct_counter.most_common(5)
        
        archetypes.append({
            'section_type': cat,
            'total_samples': len(items),
            'common_module_sequences': [
                {'modules': list(seq), 'count': count}
                for seq, count in top_seq
            ],
            'common_column_structures': [
                {'structure': cs, 'count': count}
                for cs, count in top_col
            ],
            'divider_frequency': round(divider_count / len(items), 2),
            'gradient_frequency': round(gradient_count / len(items), 2),
            'avg_modules': round(sum(len(i['modules']) for i in items) / len(items), 1),
            'avg_rows': round(sum(sum(1 for cs in i['column_structures']) for i in items) / len(items), 1),
        })
    
    return sorted(archetypes, key=lambda x: x['total_samples'], reverse=True)

def extract_module_affinity(infos: list) -> list:
    """Extract which modules appear together frequently."""
    # For each section category, find module co-occurrence
    by_category = defaultdict(list)
    for info in infos:
        cat = info['section_type']
        modules = set(m['category'] for m in info['modules'] 
                     if m['category'] not in ('section', 'row', 'column'))
        by_category[cat].append(modules)
    
    affinities = []
    for cat, module_sets in by_category.items():
        if len(module_sets) < 3:
            continue
        # Find most common module combinations
        pair_counter = Counter()
        single_counter = Counter()
        for modules in module_sets:
            single_counter.update(modules)
            mod_list = list(modules)
            for i in range(len(mod_list)):
                for j in range(i+1, len(mod_list)):
                    pair = tuple(sorted([mod_list[i], mod_list[j]]))
                    pair_counter[pair] += 1
        
        top_pairs = [{'modules': list(p), 'count': c} for p, c in pair_counter.most_common(10) if c > 1]
        top_singles = [{'module': m, 'count': c} for m, c in single_counter.most_common(15)]
        
        affinities.append({
            'section_type': cat,
            'total_samples': len(module_sets),
            'top_modules': top_singles,
            'top_pairs': top_pairs,
        })
    
    return sorted(affinities, key=lambda x: x['total_samples'], reverse=True)


def main():
    print("[EXTRACT] Scanning catalog jsons...")
    
    if not CATALOG_DIR.exists():
        print(f"Error: Catalog directory not found: {CATALOG_DIR}", file=sys.stderr)
        return 1
    
    all_infos = []
    total = 0
    errors = 0
    
    # Iterate through all subdirectories
    for entry in sorted(os.listdir(CATALOG_DIR)):
        entry_path = CATALOG_DIR / entry
        if not entry_path.is_dir():
            continue
        
        json_files = list(entry_path.glob('*.json'))
        if not json_files:
            continue
        
        json_path = json_files[0]
        try:
            raw = json_path.read_text('utf-8')
            data = json.loads(raw)
            
            # Extract shortcode content from Divi 4 format
            inner = data.get('data', {})
            shortcode_text = ''
            for val in inner.values():
                if isinstance(val, str):
                    shortcode_text += val
            
            if not shortcode_text.strip():
                continue
            
            info = extract_divi_info(shortcode_text, entry, json_path)
            info['section_type'] = categorize_section(entry, info)
            all_infos.append(info)
            total += 1
            
            if total % 100 == 0:
                print(f"[EXTRACT]  Processed {total}...")
                
        except (json.JSONDecodeError, KeyError, Exception) as e:
            errors += 1
            if errors <= 5:
                print(f"[WARN]  Error in {entry}: {e}", file=sys.stderr)
    
    print(f"[EXTRACT] Done. {total} sections parsed, {errors} errors.")
    
    # Build design-patterns.json — O(1) keyed by section_type
    archetypes_list = extract_composition_archetypes(all_infos)
    affinity_list = extract_module_affinity(all_infos)
    
    patterns = {
        'meta': {
            'total_sections_analyzed': total,
            'error_count': errors,
            'description': 'Design patterns extracted from Divi 4 catalog templates. '
                          'Use as reference for section composition, not as transcoding source.',
        },
        'composition_archetypes': {a['section_type']: a for a in archetypes_list},
        'module_affinity': {a['section_type']: a for a in affinity_list},
        'color_palettes': extract_color_palettes(all_infos),
    }
    
    OUTPUT_PATH.write_text(
        json.dumps(patterns, indent=2, ensure_ascii=False),
        'utf-8'
    )
    file_size = os.path.getsize(OUTPUT_PATH)
    print(f"[EXTRACT] Written: {OUTPUT_PATH} ({file_size}B)")
    
    # Print summary
    print("\n[SUMMARY] Section type distribution:")
    type_counts = Counter(info['section_type'] for info in all_infos)
    for cat, count in type_counts.most_common(20):
        pct = round(count / total * 100, 1)
        bar = '█' * int(pct / 2)
        print(f"  {cat:16s} {count:4d} ({pct:5.1f}%) {bar}")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
