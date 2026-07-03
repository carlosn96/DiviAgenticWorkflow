"""Fix faq-pro.json encoding more precisely."""
import json

f = 'DAW_bundle/site/sanpablo/references/Semana biblica/sections/faq-pro.json'
with open(f, 'r', encoding='utf-8') as fh:
    data = json.load(fh)

# Fix module[2] content - this is fine, escríbenos is correct
# Fix module[3] content - the FAQ items
c2 = data['rows'][0]['columns'][0]['modules'][2]['content']
c3 = data['rows'][0]['columns'][0]['modules'][3]['content']

# Fix module[2] - escríbenos should be correct already (all FFFD -> í was right)
# Check if module[2] is correct
print(f'Module[2] has FFFD: {chr(0xfffd) in c2}')

# Fix module[3] - targeted replacements
# Questions (all start with í in place of ¿):
fixes = [
    # Question 1: ¿A quién está dirigida la Semana Bíblica?
    ('\u00edA qui\u00edn est\u00ed dirigida la Semana B\u00edblica?', '¿A quién está dirigida la Semana Bíblica?'),
    # Answer 1: público
    ('p\u00edblico', 'público'),
    # Question 2: ¿Los ponentes son solo de la Ciudad de México?
    ('\u00edLos ponentes son solo de la Ciudad de M\u00e9xico', '¿Los ponentes son solo de la Ciudad de México'),
    ('\u00edLos ponentes son solo de la Ciudad de M\u00edxico', '¿Los ponentes son solo de la Ciudad de México'),
    # Question 3: ¿Hay opción virtual?
    ('\u00edHay opci\u00f3n virtual', '¿Hay opción virtual'),
    # Check what opción looks like now
    # Answer 3: Sí, todas / quedarán grabadas
    ('S\u00ed, todas', 'Sí, todas'),  # this sí is correct
    ('quedar\u00edn', 'quedarán'),
    # Question 4: ¿Cuál es el costo?
    ('\u00edCu\u00e1l es el costo', '¿Cuál es el costo'),
    ('\u00edCu\u00edl', '¿Cuál'),
    # Answer 4: registrarte (no accent)
]

print("\nModule[3] fixes:")
for old, new in fixes:
    if old in c3:
        c3 = c3.replace(old, new)
        print(f'  OK: {repr(old[:50])}')
    else:
        # Check what's actually there
        first_word = old.split()[0] if old else ''
        idx = c3.find(first_word[:5])
        if idx >= 0:
            actual = c3[idx:idx+len(old)]
            print(f'  PARTIAL: looking for {repr(old[:50])}')
            print(f'    Found: {repr(actual[:50])}')
        else:
            # Try scanning for key patterns
            for ch in old.split()[0][:3]:
                if ord(ch) > 127:
                    ch_ord = ord(ch)
                    print(f'  Looking for char U+{ch_ord:04X}...')
            print(f'  MISS: {repr(old[:50])}')

data['rows'][0]['columns'][0]['modules'][2]['content'] = c2
data['rows'][0]['columns'][0]['modules'][3]['content'] = c3

with open(f, 'w', encoding='utf-8') as fh:
    json.dump(data, fh, ensure_ascii=False, indent=2)

print("\nDone!")
