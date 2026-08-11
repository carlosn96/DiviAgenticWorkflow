import re

path = 'DAW_bundle/site/lopezvelarde/brand/assets/css/brand-new.css'
with open(path, 'r', encoding='utf-8') as f:
    css = f.read()

# Find all :root block positions
positions = []
pos = 0
while True:
    pos = css.find(':root {', pos)
    if pos == -1:
        break
    end = css.find('}', pos) + 1
    positions.append((pos, end))
    pos = end

print(f'Found {len(positions)} :root blocks')

# Find and remove duplicate
for i, (start, end) in enumerate(positions):
    block = css[start:end]
    norm = re.sub(r'\s+', ' ', block).strip()
    
    # Compare with all previous blocks
    for j in range(i):
        prev_start, prev_end = positions[j]
        prev_block = css[prev_start:prev_end]
        prev_norm = re.sub(r'\s+', ' ', prev_block).strip()
        
        if norm == prev_norm:
            print(f'Removing duplicate :root block #{i+1} at {start}-{end} (same as #{j+1})')
            # Remove this block and leading whitespace
            cut_start = start
            while cut_start > 0 and css[cut_start-1] in '\n \t':
                cut_start -= 1
            css = css[:cut_start] + css[end:]
            print(f'New size: {len(css)} chars')

with open(path, 'w', encoding='utf-8') as f:
    f.write(css)

print(f':root blocks remaining: {css.count(":root {")}')
