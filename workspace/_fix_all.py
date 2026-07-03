"""Fix encoding damage in section JSON files - raw byte level."""
import os

dst = 'DAW_bundle/site/sanpablo/references/Semana biblica/sections'

# Each entry: (filename, hex_bytes_to_find, hex_bytes_to_replace_with)
# The bytes to find include the corrupted FFFD + surrounding corruption
# The bytes to replace with are the correct UTF-8

fixes = [
    # ===== cta-final: Inscríbete ahora =====
    # Inscr FFFD bete ahora -> Inscríbete ahora
    # FFFD = EF BF BD, should be í = C3 AD
    ('cta-final-pro.json',
     'EFBFBD',
     'C3AD'),

    # ===== faq: escríbenos =====
    # escr FFFD benos -> escríbenos
    ('faq-pro.json',
     'EFBFBD',
     'C3AD'),

    # ===== faq: blico -> blico (need more context)
    # FFFD -> í (C3 AD) everywhere
    # But also: FFFD -> é (C3 A9), FFFD -> á (C3 A1), FFFD -> ¿ (C2 BF)

    # ===== program: FFFD ?? -> — (em dash, E2 80 94) =====
    # This one is special: FFFD + 3F 3F -> E2 80 94
    ('program-pro.json',
     'EFBFBD3F3F',
     'E28094'),

    # ===== register: participaci FFFD ? ³ n -> participación =====
    # FFFD + 3F + C2 B3 -> C3 B3 (ó)
    ('register-pro.json',
     'EFBFBD3FC2B3',
     'C3B3'),

    # ===== register: FFFD ? ¡ -> ¡ =====
    # FFFD + 3F + C2 A1 -> C2 A1 (¡)
    ('register-pro.json',
     'EFBFBD3FC2A1',
     'C2A1'),

    # ===== register: B FFFD ? ­ blica -> Bíblica =====
    # FFFD + 3F + C2 AD -> C3 AD (í)
    ('register-pro.json',
     'EFBFBD3FC2AD',
     'C3AD'),

    # ===== register: confirmaci FFFD ? ³ n -> confirmación =====
    # FFFD + 3F + C2 B3 -> C3 B3 (ó)
    ('register-pro.json',
     'EFBFBD3FC2B3',
     'C3B3'),

    # ===== register: Librer FFFD ? ­ a -> Librería =====
    # FFFD + 3F + C2 AD -> C3 AD (í)
    ('register-pro.json',
     'EFBFBD3FC2AD',
     'C3AD'),

    # ===== register: Vie FFFD ? · -> Vie — =====
    # FFFD + 3F + C2 B7 -> E2 80 94 (—)
    ('register-pro.json',
     'EFBFBD3FC2B7',
     'E28094'),

    # ===== tema-central: FFFD ?? Tú -> "Tú =====
    # FFFD + 3F 3F + 54 C3 BA -> E2 80 9C 54 C3 BA
    ('tema-central-pro.json',
     'EFBFBD3F3F54C3BA',
     'E2809C54C3BA'),

    # ===== tema-central: Pedro FFFD ? FFFD . -> Pedro", =====
    # FFFD 3F FFFD -> E2 80 9D 2C
    ('tema-central-pro.json',
     'EFBFBD3FEFBFBD2E',
     'E2809D2C'),

    # ===== tema-central: FFFD ? FFFD </span> -> "</span> =====
    ('tema-central-pro.json',
     'EFBFBD3FEFBFBD',
     'E2809D'),
]

# Group fixes by file
from collections import defaultdict
file_fixes = defaultdict(list)
for fname, old_hex, new_hex in fixes:
    file_fixes[fname].append((bytes.fromhex(old_hex), bytes.fromhex(new_hex)))

# Some generic fixes for faq: FFFD alone -> í (context-dependent but most are í)
# We'll handle faq specifically below

# Process each file
for fname in sorted(file_fixes.keys()):
    fpath = os.path.join(dst, fname)
    with open(fpath, 'rb') as f:
        raw = bytearray(f.read())
    
    print(f'\n=== {fname} ===')
    for old_bytes, new_bytes in file_fixes[fname]:
        count = raw.count(old_bytes)
        if count > 0:
            raw = bytearray(raw.replace(old_bytes, new_bytes))
            print(f'  Replaced {count}x {old_bytes.hex()} -> {new_bytes.hex()}')
        else:
            print(f'  NOT FOUND: {old_bytes.hex()}')
    
    with open(fpath, 'wb') as f:
        f.write(raw)

# Now handle faq specially - replace all remaining FFFD with correct chars
# Based on context: the FFFD in faq are: í, é, á, ¿
# Let's do a context-aware pass on decoded text
print('\n=== faq-pro.json (smart fix) ===')
fpath = os.path.join(dst, 'faq-pro.json')
with open(fpath, 'r', encoding='utf-8') as f:
    text = f.read()

FFFD = '\ufffd'
for old, new in [
    (f'{FFFD}benos', 'íbenos'),
    (f'{FFFD}A', '¿A'),
    (f'qui{FFFD}n', 'quién'),
    (f'est{FFFD} d', 'está d'),
    (f'{FFFD}Los', '¿Los'),
    (f'{FFFD}Qu{FFFD} requisitos', '¿Qué requisitos'),
    (f'{FFFD}Cu{FFFD}nto', '¿Cuánto'),
    (f'{FFFD}Hay', '¿Hay'),
    (f'{FFFD}Habr{FFFD}', '¿Habrá'),
]:
    if old in text:
        text = text.replace(old, new)
        print(f'  OK: {old[:30]}')

with open(fpath, 'w', encoding='utf-8') as f:
    f.write(text)

# Final verification
print('\n=== Final verification ===')
for fname in sorted(set(f for f, _, _ in fixes) | {'faq-pro.json'}):
    fpath = os.path.join(dst, fname)
    with open(fpath, 'rb') as f:
        raw = f.read()
    count = raw.count(b'\xef\xbf\xbd')
    if count > 0:
        print(f'  {fname}: {count} FFFD remaining!')
        # Show context
        idx = raw.find(b'\xef\xbf\xbd')
        ctx = raw[max(0,idx-20):idx+20]
        print(f'    Context: {ctx}')
    else:
        print(f'  {fname}: CLEAN ✓')
