"""Fix faq by examining actual codepoints."""
import json

f = 'DAW_bundle/site/sanpablo/references/Semana biblica/sections/faq-pro.json'
with open(f, 'r', encoding='utf-8') as fh:
    data = json.load(fh)

c3 = data['rows'][0]['columns'][0]['modules'][3]['content']

# Show each non-ASCII char in context
out_lines = []
for i, ch in enumerate(c3):
    if ord(ch) > 127:
        start = max(0, i-5)
        end = min(len(c3), i+5)
        ctx = c3[start:end]
        out_lines.append(f'  pos {i}: U+{ord(ch):04X} ({ch!r}) context: {repr(ctx)}')

with open('faq_codepoints.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out_lines))
print(f'Found {len(out_lines)} non-ASCII chars')
