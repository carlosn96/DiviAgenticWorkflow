import os

dst = 'DAW_bundle/site/sanpablo/references/Semana biblica/sections'
problems = ['cta-final-pro.json','faq-pro.json','program-pro.json','register-pro.json','tema-central-pro.json','testimonials-pro.json']

for fname in problems:
    fpath = os.path.join(dst, fname)
    with open(fpath, 'rb') as f:
        raw = f.read()
    
    print(f'\n=== {fname} ===')
    
    # Find each U+FFFD (EF BF BD in UTF-8)
    idx = 0
    count = 0
    while True:
        idx = raw.find(b'\xef\xbf\xbd', idx)
        if idx < 0:
            break
        count += 1
        # Show 32 bytes before and 32 bytes after
        start = max(0, idx - 32)
        end = min(len(raw), idx + 32)
        ctx = raw[start:end]
        
        # Try to show ASCII representation (replace non-ASCII with .)
        ascii_repr = ''
        for b in ctx:
            if 32 <= b < 127:
                ascii_repr += chr(b)
            else:
                ascii_repr += '.'
        
        # Mark where FFFD is
        fffd_pos_in_ctx = idx - start
        marker = ' ' * fffd_pos_in_ctx + '^^^'
        
        print(f'\n  #{count} at byte {idx}:')
        print(f'  Hex: {" ".join(f"{b:02X}" for b in ctx)}')
        print(f'  Asc: {ascii_repr}')
        print(f'       {marker}')
        
        idx += 3
        if count >= 8:
            remaining = raw.count(b'\xef\xbf\xbd') - count
            if remaining > 0:
                print(f'  ... and {remaining} more')
            break
