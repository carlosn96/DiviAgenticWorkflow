import re
from collections import defaultdict

path = 'DAW_bundle/site/lopezvelarde/brand/assets/css/brand.css'
with open(path, 'r', encoding='utf-8') as f:
    css = f.read()

# Find LAST occurrence of critical selectors
targets = [
    'body:not(.et-fb) .sp5-navbar.et_pb_section',
    '.sp5-card:hover',
    '.sp5-footer-title',
    '.sp5-plan-info',
    '.sp5-sidebar-title',
    '.sp5-plan-grid-inner',
    '.sp5-footer-list a',
    '.sp5-glass',
    'body #page-container .sp5-navbar .sp5-btn-primary.et_pb_button',
    '.sp5-navbar .et_mobile_menu .menu-item-has-children > a',
]

for t in targets:
    idx = css.rfind(t)
    if idx >= 0:
        brace = css.find('{', idx)
        close = css.find('}', brace)
        block = css[idx:close+1]
        lines = block.split('\n')
        if len(lines) > 15:
            block = '\n'.join(lines[:13]) + '\n  ...'
        print(f'=== {t} ===')
        print(block)
        print()
    else:
        print(f'MISSING: {t}')
        print()

# Check remaining conflicts
def parse_rules(css_text):
    rules = []
    buf = ''
    depth = 0
    for c in css_text:
        buf += c
        if c == '{': depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                bs = buf.find('{')
                if bs >= 0:
                    sel = buf[:bs].strip()
                    body = buf[bs+1:-1].strip()
                    norm_sel = re.sub(r'\s+', ' ', sel)
                    rules.append((norm_sel, body))
                buf = ''
    return rules

rules = parse_rules(css)
prop_sets = defaultdict(lambda: defaultdict(list))
conflicts = []

for norm_sel, body in rules:
    if norm_sel.startswith(':root') or norm_sel.startswith('@media') or norm_sel.startswith('@keyframes'):
        continue
    for d in body.split(';'):
        d = d.strip()
        if ':' in d:
            p, v = d.split(':', 1)
            p, v = p.strip(), v.strip()
            v_norm = re.sub(r'\s+', ' ', v.replace(' !important', '')).strip()
            for prev_v in prop_sets[norm_sel][p]:
                pv_norm = re.sub(r'\s+', ' ', prev_v.replace(' !important', '')).strip()
                if v_norm != pv_norm:
                    s = norm_sel[:60]
                    conflicts.append((s, p, prev_v, v))
            prop_sets[norm_sel][p].append(v)

if conflicts:
    print(f'\n=== {len(conflicts)} REMAINING CONFLICTS ===')
    for s, p, v1, v2 in conflicts[:10]:
        print(f'  [{s}] {p}: "{v1}" vs "{v2}"')
    if len(conflicts) > 10:
        print(f'  ... and {len(conflicts)-10} more')
else:
    print('\n=== NO CONFLICTS REMAINING ===')

print(f'\nTotal rules: {len(rules)}')
print(f'Size: {len(css)} chars')
