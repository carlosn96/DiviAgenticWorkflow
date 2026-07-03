import os, json, sys

dst = 'DAW_bundle/site/sanpablo/references/Semana biblica/sections'
problems = ['cta-final-pro.json','faq-pro.json','program-pro.json','register-pro.json','tema-central-pro.json','testimonials-pro.json']

out = []
for fname in problems:
    fpath = os.path.join(dst, fname)
    with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
        text = f.read()
    
    data = json.loads(text)
    out.append(f'=== {fname} ===')
    
    def find_fffd(obj, path=''):
        if isinstance(obj, str):
            if '\ufffd' in obj:
                idx = obj.find('\ufffd')
                offset_before_bytes = len(obj[:idx].encode('utf-8'))
                # Read raw file bytes at this position
                with open(fpath, 'rb') as f:
                    raw = f.read()
                raw_idx = offset_before_bytes
                start_raw = max(0, raw_idx - 16)
                end_raw = min(len(raw), raw_idx + 32)
                chunk = raw[start_raw:end_raw]
                out.append(f'  Path: {path}')
                out.append(f'  Context: {obj[max(0,idx-40):min(len(obj),idx+60)]!r}')
                out.append(f'  Raw hex: {" ".join(f"{b:02X}" for b in chunk)}')
                out.append(f'  Raw at damage: {" ".join(f"{b:02X}" for b in raw[raw_idx:raw_idx+10])}')
                out.append('')
        elif isinstance(obj, dict):
            for k, v in obj.items():
                find_fffd(v, f'{path}.{k}' if path else k)
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                find_fffd(v, f'{path}[{i}]')
    
    find_fffd(data)

with open(os.path.join(dst, '..', 'damage_report.txt'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print('Report written to damage_report.txt')
