import os

new_path = 'DAW_bundle/site/lopezvelarde/brand/assets/css/brand-new.css'
old_path = 'DAW_bundle/site/lopezvelarde/brand/assets/css/brand.css'

with open(new_path, 'r', encoding='utf-8') as f:
    css = f.read()
with open(old_path, 'r', encoding='utf-8-sig') as f:
    orig = f.read()

print('=== DEDUP COMPLETE ===')
print(f'Original: {len(orig)} chars, {orig.count(chr(10))+1} lines')
print(f'New:      {len(css)} chars, {css.count(chr(10))+1} lines')
print(f'Saved:    {len(orig)-len(css)} chars ({100*(len(orig)-len(css))//len(orig)}%)')
print(f':root blocks: {css.count(":root {")}')

checks = ['sp5-btn-back', 'NOTICIAS PAGE', 'SOCIAL FEEDS', 'SOBREESCRITURAS', 'scene-404',
          'sp5-timeline', 'sp5-faq', 'sp5-campus-gallery', 'sp5-card', 'sp5-display', 'sp5-navbar']
for ck in checks:
    print(f'  {ck}: {ck in css}')

with open(new_path, 'rb') as f:
    bom = f.read(3)
print(f'BOM: {bom == b"\\xef\\xbb\\xbf"}')

lines = css.split(chr(10))
print(f'\nFirst 6 lines:')
for l in lines[:6]:
    print(l)
print(f'\nLast 3 lines:')
for l in lines[-3:]:
    print(l)
