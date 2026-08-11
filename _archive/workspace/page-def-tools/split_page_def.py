"""
Split flat exported page-def JSON into manifest + sections/ structure.
"""
import json, os, re

site = 'lopezvelarde'
base = f'DAW_bundle/site/{site}/page-defs'

# Read the flat export
with open(f'{base}/inicio.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

sections = data['sections']

# Define section slugs and labels
section_labels = [
    ('hero', 'Hero Section'),
    ('stats', 'Stats Counters'),
    ('facebook-reel', 'Facebook Reel Embed'),
    ('oferta-educativa', 'Oferta Educativa Cards'),
    ('comunidad', 'Comunidad + Social'),
    ('conocenos', 'Conocenos Cards'),
    ('cta-final', 'CTA Final'),
]

# Ensure directories exist (flat sections/ per DAW convention)
sections_dir = f'{base}/sections'
os.makedirs(sections_dir, exist_ok=True)

# Write each section file
for i, (slug, label) in enumerate(section_labels):
    section_data = sections[i]
    
    # Add _section marker
    section_data['_section'] = True
    
    # Clean redundant module_class when it matches htmlAttributes.class
    adv = section_data.get('advanced', {})
    ha = adv.get('htmlAttributes', {}).get('desktop', {}).get('value', {})
    html_class = ha.get('class', '')
    mc = section_data.get('module_class', '')
    
    if mc and mc == html_class:
        del section_data['module_class']
    
    # Write section file
    filepath = f'{sections_dir}/{i+1:02d}-{slug}.json'
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(section_data, f, ensure_ascii=False, indent=4)
    
    print(f'  {filepath}')

# Remove old flat file first (same path as new manifest)
old_flat = f'{base}/inicio.json'
if os.path.exists(old_flat):
    os.remove(old_flat)
    print(f'  Removed old flat: {old_flat}')

# Create manifest
manifest = {
    '_manifest': 'v1',
    'title': 'Inicio',
    'slug': 'inicio',
    'sections': [
        f'sections/{i+1:02d}-{slug}.json'
        for i, (slug, _) in enumerate(section_labels)
    ]
}

manifest_path = f'{base}/inicio.json'
with open(manifest_path, 'w', encoding='utf-8') as f:
    json.dump(manifest, f, ensure_ascii=False, indent=4)

print(f'\nDone!')
print(f'Manifest: {manifest_path}')
print(f'Sections: {len(sections)} files in {sections_dir}/')
