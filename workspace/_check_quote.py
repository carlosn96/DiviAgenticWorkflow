import json

f = 'DAW_bundle/site/sanpablo/references/Semana biblica/sections/testimonials-pro.json'
d = json.load(open(f, 'r', encoding='utf-8'))
c = d['rows'][0]['columns'][0]['modules'][3]['content']

# Check for >?La pattern
pattern = '\u003e\u003fLa Semana'  # = 
print(f'Pattern: {repr(pattern)}')
print(f'Found: {c.find(pattern)}')
print(f'Count: {c.count(pattern)}')

# What does the actual text look like?
idx = c.find('La Semana')
print(f'Context at La Semana: {repr(c[idx-10:idx+30])}')

# Check last testimonial for closing quote
idx2 = c.find('irrepetible')
if idx2 >= 0:
    print(f'Irrepetible context: {repr(c[idx2-5:idx2+50])}')
