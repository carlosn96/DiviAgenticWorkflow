"""
Final conflict resolver.
Strategy: For each selector, merge ALL occurrences, keeping last value per property.
- :root blocks: merge into one (different vars accumulate; same vars keep last value)
- @media/@keyframes: keep all unique blocks (don't merge across blocks)
- Regular selectors: merge ALL occurrences, last value per property wins
"""
import re
from collections import OrderedDict, defaultdict

path = 'DAW_bundle/site/lopezvelarde/brand/assets/css/brand.css'
with open(path, 'r', encoding='utf-8') as f:
    css = f.read()

def parse_props(body):
    props = OrderedDict()
    for d in body.split(';'):
        d = d.strip()
        if ':' in d:
            p, v = d.split(':', 1)
            props[p.strip()] = v.strip()
    return props

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
                    rules.append((sel, body))
                buf = ''
    return rules

# Parse all top-level rules
all_rules = parse_rules(css)
print(f'Total top-level rules: {len(all_rules)}')

# Separate by type
root_rules = []
media_rules = []
kf_rules = []
regular = []

for sel, body in all_rules:
    if sel == ':root':
        root_rules.append(body)
    elif sel.startswith('@media'):
        media_rules.append((sel, body))
    elif sel.startswith('@keyframes'):
        kf_rules.append((sel, body))
    else:
        regular.append((sel, body))

# Merge all :root into one (last value per property wins)
all_root = OrderedDict()
for body in root_rules:
    for p, v in parse_props(body).items():
        all_root[p] = v

print(f':root: {len(root_rules)} blocks merged -> {len(all_root)} vars')

# Dedupe media blocks (exact match on normalized selector + body)
seen = set()
deduped_media = []
for sel, body in media_rules:
    norm_sel = re.sub(r'\s+', ' ', sel)
    norm_body = re.sub(r'\s+', ' ', body).strip()
    key = (norm_sel, norm_body)
    if key not in seen:
        seen.add(key)
        deduped_media.append((sel, body))

# Dedupe keyframes
seen_kf = set()
deduped_kf = []
for sel, body in kf_rules:
    norm_sel = re.sub(r'\s+', ' ', sel)
    norm_body = re.sub(r'\s+', ' ', body).strip()
    key = (norm_sel, norm_body)
    if key not in seen_kf:
        seen_kf.add(key)
        deduped_kf.append((sel, body))

print(f'@media: {len(media_rules)} -> {len(deduped_media)} unique')

# For regular rules: merge ALL occurrences, last value per property wins
merged = OrderedDict()
for sel, body in regular:
    norm_sel = re.sub(r'\s+', ' ', sel)
    if norm_sel not in merged:
        merged[norm_sel] = (sel, OrderedDict())
    _, props = merged[norm_sel]
    for p, v in parse_props(body).items():
        props[p] = v

print(f'Regular: {len(regular)} occurrences -> {len(merged)} unique selectors (merged)')

# Rebuild CSS
out = ':root {\n'
for p, v in all_root.items():
    out += f'  {p}: {v};\n'
out += '}\n\n'

for norm_sel, (orig_sel, props) in merged.items():
    out += f'{orig_sel} {{\n'
    for p, v in props.items():
        out += f'  {p}: {v};\n'
    out += '}\n\n'

for sel, body in deduped_media:
    out += f'{sel} {{\n  {body}\n}}\n\n'

for sel, body in deduped_kf:
    out += f'{sel} {{\n  {body}\n}}\n\n'

# Verify
with open(path, 'w', encoding='utf-8') as f:
    f.write(out)

# Quick checks
print(f'\n=== RESULT ===')
print(f'Size: {len(out)} chars (from {len(css)})')
print(f'Lines: {out.count(chr(10))+1}')

# Check navbar has full properties
target = 'body:not(.et-fb) .sp5-navbar.et_pb_section'
idx = out.find(target)
if idx >= 0:
    brace = out.find('{', idx)
    close = out.find('}', brace)
    block = out[idx:close+1]
    print(f'\nNAVBAR ({out[brace+1:close].count(";")} props):')
    for line in block.split('\n'):
        print(f'  {line}')
