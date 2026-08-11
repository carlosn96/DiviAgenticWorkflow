import re
from collections import OrderedDict

path = 'DAW_bundle/site/lopezvelarde/brand/assets/css/brand.css'
with open(path, 'r', encoding='utf-8') as f:
    css = f.read()

def parse_rules(css_text):
    """Parse CSS into list of (selector, body, is_root, is_media, is_keyframe)."""
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
                    is_root = sel == ':root'
                    is_media = sel.startswith('@media')
                    is_keyframe = sel.startswith('@keyframes')
                    rules.append((sel, body, is_root, is_media, is_keyframe))
                buf = ''
    return rules

rules = parse_rules(css)
print(f'Total rules: {len(rules)}')

def parse_props(body):
    props = OrderedDict()
    for d in body.split(';'):
        d = d.strip()
        if ':' in d:
            p, v = d.split(':', 1)
            props[p.strip()] = v.strip()
    return props

# Special rules: keep all unique root/media/keyframe blocks
root_bodies = []
media_blocks = {}  # body -> first occurrence
kf_blocks = {}
regular_blocks = []

for sel, body, is_root, is_media, is_kf in rules:
    norm_sel = re.sub(r'\s+', ' ', sel)
    norm_body = re.sub(r'\s+', ' ', body).strip()
    
    if is_root:
        root_bodies.append(body)
    elif is_media:
        key = (norm_sel, norm_body)
        if key not in media_blocks:
            media_blocks[key] = (sel, body)
    elif is_kf:
        key = (norm_sel, norm_body)
        if key not in kf_blocks:
            kf_blocks[key] = (sel, body)
    else:
        regular_blocks.append((norm_sel, sel, body))

# Merge all :root blocks into one
all_root_props = OrderedDict()
for body in root_bodies:
    props = parse_props(body)
    for p, v in props.items():
        all_root_props[p] = v

print(f':root: {len(root_bodies)} merged to 1 ({len(all_root_props)} vars)')
print(f'@media: {len(media_blocks)} unique')
print(f'@keyframes: {len(kf_blocks)} unique')
print(f'Regular: {len(regular_blocks)}')

# For regular rules: keep LAST occurrence (reverse scan)
seen = set()
kept = []
for norm_sel, sel, body in reversed(regular_blocks):
    if norm_sel not in seen:
        seen.add(norm_sel)
        # Dedupe properties within the body (last wins)
        props = parse_props(body)
        kept.append((sel, props))

kept.reverse()
print(f'Regular after dedup: {len(kept)}')

# Build output
root_body = ';\n  '.join([f'{p}: {v}' for p, v in all_root_props.items()])
out = f':root {{\n  {root_body};\n}}\n\n'

# Add regular rules
for sel, props in kept:
    body = ';\n  '.join([f'{p}: {v}' for p, v in props.items()])
    out += f'{sel} {{\n  {body};\n}}\n\n'

# Add @media blocks
for (norm_sel, _), (sel, body) in media_blocks.items():
    out += f'{sel} {{\n  {body}\n}}\n\n'

# Add @keyframes
for (norm_sel, _), (sel, body) in kf_blocks.items():
    out += f'{sel} {{\n  {body}\n}}\n\n'

# Verify all required content
checks = {
    'sp5-btn-back': False,
    'NOTICIAS PAGE': False,
    'SOCIAL FEEDS': False,
    'SOBREESCRITURAS': False,
    'scene-404': False,
    'sp5-card:hover': False,
    'sp5-footer-title': False,
    'sp5-footer-list a:hover': False,
    'sp5-display': False,
    'sp5-glass': False,
    'body:not(.et-fb) .sp5-navbar.et_pb_section': False,
}

for ck in checks:
    checks[ck] = ck in out

print(f'\n=== RESULT ===')
print(f'Size: {len(out)} chars ({len(css)} original)')
print(f'Lines: {out.count(chr(10))+1}')
print(f':root blocks: {out.count(":root {")}')

for ck, found in checks.items():
    print(f'  {ck}: {"OK" if found else "MISSING!"}')

# Check for remaining conflicts
with open(path, 'w', encoding='utf-8') as f:
    f.write(out)

print(f'\nWritten to {path}')
