"""Fix remaining corrupted files: tema-central, testimonials."""
import os

dst = 'DAW_bundle/site/sanpablo/references/Semana biblica/sections'

# ===== tema-central: 1 remaining FFFD =====
# FFFD?? -> " (U+201C, left curly double quote) 
fpath = os.path.join(dst, 'tema-central-pro.json')
with open(fpath, 'rb') as f:
    raw = f.read()
old = bytes.fromhex('EFBFBD3F3F')
new = '\u201c'.encode('utf-8')  # E2 80 9C
count = raw.count(old)
if count > 0:
    raw = raw.replace(old, new)
    print(f'tema-central: replaced {count}x FFFD?? -> U+201C')
    with open(fpath, 'wb') as f:
        f.write(raw)
else:
    print('tema-central: pattern not found')

# ===== testimonials: 11 FFFD remaining =====
fpath = os.path.join(dst, 'testimonials-pro.json')
with open(fpath, 'r', encoding='utf-8') as f:
    text = f.read()

FFFD = '\ufffd'

# All fixes: (corrupted_string, fixed_string)
fixes = [
    # Opening curly quote + Bíblica + transformó
    (f'\u003e?La Semana B{FFFD}blica transform{FFFD}',
     '\u003e\u201cLa Semana Bíblica transformó'),
    # María Rodríguez
    (f'Mar{FFFD}a Rodr{FFFD}guez', 'María Rodríguez'),
    # días / oración
    (f'd{FFFD}as de estudio y oraci{FFFD}n', 'días de estudio y oración'),
    # José / Hernández
    (f'Jos{FFFD} Luis Hern{FFFD}ndez', 'José Luis Hernández'),
    # Diácono
    (f'Di{FFFD}cono permanente', 'Diácono permanente'),
    # único + closing quote
    (f'algo {FFFD}nico e irrepetible.?', 'algo único e irrepetible.\u201d'),
    # Teología
    (f'Teolog{FFFD}a', 'Teología'),
    # Closing quote before end div in other testimonials:
    # The closing pattern: texto irrepetible.? → texto irrepetible."
    # We need to handle the last ? before closing div
    (f'?{FFFD}nico', '\u201dúnico'),  # Wait, this doesn't match
]

# More precise: just use byte-level replacements since text is tricky
# Replace each FFFD + context
text_fixes = [
    (f'B{FFFD}blica', 'Bíblica'),
    (f'transform{FFFD} mi', 'transformó mi'),
    (f'Mar{FFFD}a Rodr{FFFD}guez', 'María Rodríguez'),
    (f'Jos{FFFD} Luis Hern{FFFD}ndez', 'José Luis Hernández'),
    (f'd{FFFD}as de estudio', 'días de estudio'),
    (f'oraci{FFFD}n me dieron', 'oración me dieron'),
    (f'Di{FFFD}cono permanente', 'Diácono permanente'),
    (f'algo {FFFD}nico', 'algo único'),
    (f'Teolog{FFFD}a', 'Teología'),
    # Opening curly quote: \u003e?La -> \u003e"La (U+201C)
    # Raw JSON text has literal \\u003e, not decoded >
    ('\\u003e?La Semana', '\\u003e\u201cLa Semana'),
    # Closing curly quote: irrepetible.? -> irrepetible." (U+201D)
    (f'irrepetible.?', 'irrepetible.\u201d'),
]

changes = 0
for old, new in text_fixes:
    if old in text:
        text = text.replace(old, new)
        changes += 1
        first_bit = old[:30].replace('\ufffd', '\\xFFFD')
        print(f'  Fixed: {first_bit}')
    else:
        # Escape FFFD for debug print
        escaped_old = old[:50].replace('\ufffd', '\\xFFFD')
        # Find with first 5 non-FFFD chars
        clean = ''.join(c for c in old if c != '\ufffd')[:10]
        if clean:
            idx = text.find(clean)
            if idx >= 0:
                actual = text[idx:idx+len(old)]
                escaped_actual = actual.replace('\ufffd', '\\xFFFD')
                print(f'  PARTIAL: expected {escaped_old}')
                print(f'    found: {escaped_actual}')
            else:
                print(f'  MISS: {escaped_old}')
        else:
            print(f'  MISS: {escaped_old}')

with open(fpath, 'w', encoding='utf-8') as f:
    f.write(text)
print(f'\nTestimonials: {changes} fixes applied (out of {len(text_fixes)} patterns)')

# Final verification
print('\n=== Final verification ===')
for fname in ['cta-final-pro.json', 'faq-pro.json', 'program-pro.json', 
              'register-pro.json', 'tema-central-pro.json', 'testimonials-pro.json']:
    fpath = os.path.join(dst, fname)
    with open(fpath, 'rb') as f:
        raw = f.read()
    count = raw.count(b'\xef\xbf\xbd')
    if count > 0:
        print(f'  {fname}: {count} FFFD remaining')
    else:
        print(f'  {fname}: CLEAN')
