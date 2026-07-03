"""Fix faq-pro.json: all corrupted chars are currently U+00ED (í)."""
import json

f = 'DAW_bundle/site/sanpablo/references/Semana biblica/sections/faq-pro.json'
with open(f, 'r', encoding='utf-8') as fh:
    data = json.load(fh)

c2 = data['rows'][0]['columns'][0]['modules'][2]['content']
c3 = data['rows'][0]['columns'][0]['modules'][3]['content']

# Module[2]: escríbenos - this is already correct (í is the right char)
# Just verify
if 'escríbenos' in c2:
    print("Module[2]: correct")
else:
    print("Module[2]: needs review")
    # Fix if needed
    c2 = c2.replace('escr\u00edbenos', 'escríbenos')

# Module[3]: fix each question/answer
# Full question strings for precise replacement
replacements = [
    # Question 1
    ('\u00edA qui\u00edn est\u00ed dirigida la Semana B\u00edblica?', '¿A quién está dirigida la Semana Bíblica?'),
    # Answer 1: público
    ('A todo p\u00edblico', 'A todo público'),
    # Question 2
    ('\u00edLos ponentes son solo de la Ciudad de M\u00edxico?', '¿Los ponentes son solo de la Ciudad de México?'),
    # Answer 2: investigación
    ('investigaci\u00edn b\u00edblica', 'investigación bíblica'),
    # Question 3
    ('\u00edHay opci\u00edn virtual?', '¿Hay opción virtual?'),
    # Answer 3: quedarán
    ('quedar\u00edn grabadas', 'quedarán grabadas'),
    # Question 4  
    ('\u00edCu\u00edl es el costo?', '¿Cuál es el costo?'),
    # Additional: already correct ones (Bíblica, teología, Sí)
    # Bíblica is correct, teología is correct, Sí is correct
]

changes = 0
for old, new in replacements:
    if old in c3:
        c3 = c3.replace(old, new)
        changes += 1
        # Verify
        if new in c3:
            print(f'  Fixed: {repr(new[:60])}')
        else:
            print(f'  FAILED: {repr(new[:60])}')
    else:
        print(f'  NOT FOUND: {repr(old[:60])}')

# Final check for any remaining non-standard chars
# The only non-ASCII chars that should remain are: í in Bíblica, teología, Sí
# Check for any non-ASCII that isn't U+00ED (í), U+00E1 (á), U+00E9 (é), U+00FA (ú), U+00F3 (ó), U+00BF (¿)
remaining = []
for i, ch in enumerate(c3):
    if ord(ch) > 127 and ch not in 'íéáóú¿S':
        remaining.append((i, ord(ch), repr(ch)))

if remaining:
    print(f'\nWARNING: {len(remaining)} unexpected chars:')
    for pos, code, char in remaining:
        ctx = c3[max(0,pos-10):pos+10]
        print(f'  pos {pos}: U+{code:04X} {char} context: {repr(ctx)}')
else:
    print(f'\nAll chars valid. Total changes: {changes}')

data['rows'][0]['columns'][0]['modules'][2]['content'] = c2
data['rows'][0]['columns'][0]['modules'][3]['content'] = c3

with open(f, 'w', encoding='utf-8') as fh:
    json.dump(data, fh, ensure_ascii=False, indent=2)

print('Saved.')
