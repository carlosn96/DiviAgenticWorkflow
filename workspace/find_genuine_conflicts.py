import re
from collections import defaultdict

path = 'DAW_bundle/site/lopezvelarde/brand/assets/css/brand.css'
with open(path, 'r', encoding='utf-8') as f:
    css = f.read()

# Parse all rules with position
class Rule:
    def __init__(self, selector, body, pos, line):
        self.selector = selector.strip()
        self.body = body.strip()
        self.pos = pos
        self.line = line
        self.props = {}
        for d in body.split(';'):
            d = d.strip()
            if ':' in d:
                p, v = d.split(':', 1)
                self.props[p.strip()] = v.strip()

rules = []
buf = ''
depth = 0
line = 1
i = 0
while i < len(css):
    c = css[i]
    if c == '/' and i+1 < len(css) and css[i+1] == '*':
        while i < len(css) and not (css[i] == '*' and i+1 < len(css) and css[i+1] == '/'):
            if css[i] == '\n': line += 1
            i += 1
        i += 2
        continue
    buf += c
    if c == '{': depth += 1
    elif c == '}':
        depth -= 1
        if depth == 0:
            bs = buf.find('{')
            if bs >= 0:
                sel = buf[:bs].strip()
                body = buf[bs+1:-1].strip()
                rules.append(Rule(sel, body, i, line))
            buf = ''
    elif c == '\n': line += 1
    i += 1

print(f'Total rules: {len(rules)}')

# Group by normalized selector
groups = defaultdict(list)
for r in rules:
    norm_sel = re.sub(r'\s+', ' ', r.selector)
    groups[norm_sel].append(r)

# Find GENUINE conflicts: same selector, same property, different value
# Exclude :root and @media blocks (they can have different content intentionally)
print('\n=== GENUINE CONFLICTS (same selector, same property, different value) ===')
print('(skipping :root and @media blocks)\n')

total_conflicts = 0
for sel, group in groups.items():
    if len(group) < 2:
        continue
    if sel.startswith(':root') or sel.startswith('@media'):
        continue
    
    # Build merged property map
    prop_values = {}
    for r in group:
        for p, v in r.props.items():
            if p in prop_values:
                prev_v = prop_values[p]
                # Normalize for comparison (remove !important, collapse spaces)
                v_norm = re.sub(r'\s+', ' ', v.replace(' !important', '')).strip()
                pv_norm = re.sub(r'\s+', ' ', prev_v.replace(' !important', '')).strip()
                if v_norm != pv_norm:
                    total_conflicts += 1
                    # Print context
                    s_display = sel[:80] + '...' if len(sel) > 80 else sel
                    print(f'  [{s_display}]')
                    # Find which rules have this property
                    for r2 in group:
                        if p in r2.props:
                            print(f'    Line {r2.line}: {p}: {r2.props[p]}')
                    print()
            else:
                prop_values[p] = v

print(f'Total genuine conflicts: {total_conflicts}')

# Now show the @media blocks count
media_blocks = [r for r in rules if r.selector.startswith('@media')]
media_by_query = defaultdict(list)
for r in media_blocks:
    media_by_query[r.selector].append(r)
print(f'\n@media blocks: {len(media_blocks)} total, {len(media_by_query)} unique queries')
for q, blocks in media_by_query.items():
    if len(blocks) > 1:
        print(f'  {q[:60]}: {len(blocks)} occurrences')

# Show :root blocks
root_blocks = [r for r in rules if r.selector == ':root']
print(f'\n:root blocks: {len(root_blocks)}')
for r in root_blocks:
    var_count = len(r.props)
    nav_vars = [p for p in r.props.keys() if 'nav' in p]
    print(f'  Line {r.line}: {var_count} vars, nav-related: {len(nav_vars)}')
