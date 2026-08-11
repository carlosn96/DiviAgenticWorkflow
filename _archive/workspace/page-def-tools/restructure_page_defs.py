import os, json, shutil

base = 'DAW_bundle/site/lopezvelarde/page-defs'

# 1. Create new dirs
os.makedirs(f'{base}/inicio/sections', exist_ok=True)

# 2. Move section files
old_sections = f'{base}/sections'
section_files = sorted(os.listdir(old_sections))
for f in section_files:
    shutil.move(f'{old_sections}/{f}', f'{base}/inicio/sections/{f}')
    print(f'Moved: {f}')

# 3. Remove old sections dir
os.rmdir(old_sections)

# 4. Update manifest paths
with open(f'{base}/inicio.json', encoding='utf-8') as f:
    manifest = json.load(f)

manifest['sections'] = [f'inicio/sections/{f}' for f in section_files]

with open(f'{base}/inicio.json', 'w', encoding='utf-8') as f:
    json.dump(manifest, f, ensure_ascii=False, indent=4)

print(f'\nManifest updated with {len(section_files)} sections')
for p in manifest['sections']:
    print(f'  {p}')

# 5. Remove old combined file
combined = f'{base}/inicio-combined.json'
if os.path.exists(combined):
    os.remove(combined)
    print(f'\nRemoved old combined file')
