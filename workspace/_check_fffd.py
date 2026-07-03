import json, os

dst = 'DAW_bundle/site/sanpablo/references/Semana biblica/sections'
problems = ['cta-final-pro.json','faq-pro.json','program-pro.json','register-pro.json','tema-central-pro.json','testimonials-pro.json']

for fname in problems:
    fpath = os.path.join(dst, fname)
    with open(fpath, 'r', encoding='utf-8') as f:
        text = f.read()
    count = text.count('\ufffd')
    print(f'{fname}: {count} FFFD chars')
    
    # Show first few contexts
    if count > 0:
        idx = text.find('\ufffd')
        for n in range(min(3, count)):
            start = max(0, idx - 30)
            end = min(len(text), idx + 60)
            chunk = text[start:end]
            # Escape FFFD for display
            escaped = chunk.replace('\ufffd', '\\xFFFD')
            print(f'  [{n}] ...{escaped}...')
            idx = text.find('\ufffd', idx + 1)
