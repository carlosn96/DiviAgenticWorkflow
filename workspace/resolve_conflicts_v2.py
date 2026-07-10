import re
from collections import OrderedDict

path = 'DAW_bundle/site/lopezvelarde/brand/assets/css/brand.css'
with open(path, 'r', encoding='utf-8') as f:
    css = f.read()

# Parse ALL rules preserving order, extracting key metadata
class RuleNode:
    def __init__(self, selector, body, raw_text, index, is_root=False, is_media=False, is_keyframe=False):
        self.selector = selector.strip()
        self.norm_sel = re.sub(r'\s+', ' ', self.selector)
        self.body = body
        self.raw_text = raw_text
        self.index = index
        self.is_root = is_root
        self.is_media = is_media
        self.is_keyframe = is_keyframe
        self.props = self._parse_props()
    
    def _parse_props(self):
        props = OrderedDict()
        for d in self.body.split(';'):
            d = d.strip()
            if ':' in d:
                p, v = d.split(':', 1)
                props[p.strip()] = v.strip()
        return props

rules = []
buf = ''
depth = 0
idx = 0
i = 0
while i < len(css):
    c = css[i]
    if c == '/' and i+1 < len(css) and css[i+1] == '*':
        while i < len(css) and not (css[i] == '*' and i+1 < len(css) and css[i+1] == '/'):
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
                is_root = sel == ':root'
                is_media = sel.startswith('@media')
                is_keyframe = sel.startswith('@keyframes')
                rules.append(RuleNode(sel, body, buf, idx, is_root, is_media, is_keyframe))
                idx += 1
            buf = ''

# Separate special rules from regular rules
special_rules = [r for r in rules if r.is_root or r.is_media or r.is_keyframe]
regular_rules = [r for r in rules if not r.is_root and not r.is_media and not r.is_keyframe]

print(f'Total: {len(rules)} | Regular: {len(regular_rules)} | Special: {len(special_rules)}')

# For regular rules: scan REVERSE, keep only last occurrence of each selector
seen_selectors = set()
kept_regular = []
for r in reversed(regular_rules):
    if r.norm_sel not in seen_selectors:
        seen_selectors.add(r.norm_sel)
        # Also dedupe properties within the rule (last value wins)
        deduped_props = OrderedDict()
        for p, v in r.props.items():
            deduped_props[p] = v
        kept_regular.append((r, deduped_props))

# Restore original order (we scanned reverse)
kept_regular.reverse()

print(f'Regular dedup: {len(regular_rules)} -> {len(kept_regular)}')

# Dedupe :root blocks: merge all into one, deduping by property name (last wins)
root_rules = [r for r in special_rules if r.is_root]
all_root_props = OrderedDict()
for r in root_rules:
    for p, v in r.props.items():
        all_root_props[p] = v

# Dedupe @media and @keyframes: keep all, but dedupe props within each
# Actually, @media and @keyframes might have different sub-rules; just keep them as-is

# But we also need to dedupe media blocks that are EXACT duplicates of each other
# e.g., two @media (max-width:767px) with the same inner content
media_rules = [r for r in special_rules if r.is_media]
keyframe_rules = [r for r in special_rules if r.is_keyframe]

# Dedupe media: keep unique (normalized body)
seen_media = {}
deduped_media = []
for r in media_rules:
    norm_body = re.sub(r'\s+', ' ', r.body).strip()
    key = (r.norm_sel, norm_body)
    # But we need to merge props within each media rule's sub-rules
    # For now, just keep unique
    if key not in seen_media:
        seen_media[key] = True
        deduped_media.append(r)

# Same for keyframes
seen_kf = set()
deduped_kf = []
for r in keyframe_rules:
    norm_body = re.sub(r'\s+', ' ', r.body).strip()
    key = (r.norm_sel, norm_body)
    if key not in seen_kf:
        seen_kf.add(key)
        deduped_kf.append(r)

# Rebuild CSS preserving original order of sections
# We need to interleave kept rules in original order
# Best approach: rebuild from scratch, grouping by section
# Simple approach: just concatenate: root + regular + media + keyframes

root_body = ';\n  '.join([f'{p}: {v}' for p, v in all_root_props.items()])
root_css = f':root {{\n  {root_body};\n}}'

regular_css_parts = []
for r, props in kept_regular:
    body = ';\n  '.join([f'{p}: {v}' for p, v in props.items()])
    regular_css_parts.append(f'{r.selector} {{\n  {body};\n}}')

media_css_parts = []
for r in deduped_media:
    media_css_parts.append(r.raw_text)

kf_css_parts = []
for r in deduped_kf:
    kf_css_parts.append(r.raw_text)

# Interleave in original-like order: root, then regular, then @media, then @keyframes
# But preserve relative order within each category by using original indices
all_regular_indices = {r.index for r in regular_rules}
all_media_indices = {r.index for r in media_rules}
all_kf_indices = {r.index for r in keyframe_rules}

# Build combined CSS tracking original order
# Use the kept nodes with their original indices
combined_parts = []

# Generate root first
combined_parts.append(root_css)

# Then everything else in original order (skipping root)
# Build lookup for kept regular, media, and keyframe by normalized key
kept_regular_by_sel = {(r.selector, tuple(props.items())): True for r, props in kept_regular}
# Actually, simpler: just use the kept lists in order

# Build final CSS section by section
# Use the original index ordering
all_kept = []
for r in kept_regular:
    # Build raw text for this kept rule
    _, props = [x for x in kept_regular if x[0] is r][0]
    body = ';\n  '.join([f'{p}: {v}' for p, v in props.items()])
    all_kept.append((r.index, f'{r.selector} {{\n  {body};\n}}'))

for r in deduped_media:
    all_kept.append((r.index, r.raw_text))

for r in deduped_kf:
    all_kept.append((r.index, r.raw_text))

all_kept.sort(key=lambda x: x[0])

final_css = root_css + '\n\n' + '\n\n'.join([x[1] for x in all_kept])

# Write
with open(path, 'w', encoding='utf-8') as f:
    f.write(final_css)

print(f'\n=== RESULT ===')
print(f'Size: {len(final_css)} chars')
print(f'Lines: {final_css.count(chr(10))+1}')
print(f':root blocks: {final_css.count(":root {")}')
print(f'/: {final_css.count(":")}')
checks = ['sp5-btn-back', 'NOTICIAS PAGE', 'SOCIAL FEEDS', 'SOBREESCRITURAS', 'scene-404',
           'sp5-card:hover', 'sp5-glass', 'sp5-plan-info', 'sp5-sidebar-title', 'sp5-plan-grid-inner',
           'sp5-footer-title', 'sp5-footer-list a']
for ck in checks:
    print(f'  {ck}: {ck in final_css}')
