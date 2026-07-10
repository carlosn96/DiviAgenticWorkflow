import json
d = json.load(open('DAW_bundle/site/lopezvelarde/page-defs/inicio/sections/06-conocenos.json'))
for row_idx, row in enumerate(d['rows']):
    for col_idx, col in enumerate(row.get('columns',[])):
        for mod_idx, mod in enumerate(col.get('modules',[])):
            if mod.get('type') == 'divi/blurb':
                title = mod.get('title', '?')
                if isinstance(title, dict):
                    title = title.get('text', str(title))
                print(f'Row {row_idx} Col {col_idx} Mod {mod_idx}:')
                print(f'  title={title}')
                print(f'  content={mod.get("content","")[:80]}')
                print(f'  decoration keys: {list(mod.get("decoration",{}).keys())}')
                print()
