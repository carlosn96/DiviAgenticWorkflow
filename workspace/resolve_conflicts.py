import re
from collections import OrderedDict

path = 'DAW_bundle/site/lopezvelarde/brand/assets/css/brand.css'
with open(path, 'r', encoding='utf-8') as f:
    css = f.read()

# Parse CSS keeping full rule text and position
class CssRule:
    def __init__(self, selector, full_text, line_num):
        self.selector = selector.strip()
        self.full_text = full_text
        self.line_num = line_num
        self.declarations = self._parse_declarations()
    
    def _parse_declarations(self):
        brace_start = self.full_text.find('{')
        brace_end = self.full_text.rfind('}')
        body = self.full_text[brace_start+1:brace_end].strip()
        decls = OrderedDict()
        for d in body.split(';'):
            d = d.strip()
            if ':' in d:
                p, v = d.split(':', 1)
                decls[p.strip()] = v.strip()
        return decls

rules = []
line_num = 1
buf = ''
depth = 0

i = 0
while i < len(css):
    c = css[i]
    if c == '/' and i+1 < len(css) and css[i+1] == '*':
        while i < len(css) and not (css[i] == '*' and i+1 < len(css) and css[i+1] == '/'):
            if css[i] == '\n': line_num += 1
            i += 1
        i += 2
        continue
    buf += c
    if c == '{': depth += 1
    elif c == '}':
        depth -= 1
        if depth == 0:
            brace_start = buf.find('{')
            if brace_start >= 0:
                sel = buf[:brace_start].strip()
                rules.append(CssRule(sel, buf, line_num))
            buf = ''
    elif c == '\n': line_num += 1
    i += 1

print(f'Total rules: {len(rules)}')

# Strategy: For each unique selector, keep the LAST rule (wins by cascade)
# But FIRST merge declarations from all rules for that selector, with later values winning
from collections import defaultdict

selector_rules = defaultdict(list)
for r in rules:
    norm_sel = re.sub(r'\s+', ' ', r.selector)
    selector_rules[norm_sel].append(r)

merged_rules = []
conflicts_removed = 0

for sel, rule_list in selector_rules.items():
    if len(rule_list) == 1:
        merged_rules.append(rule_list[0].full_text)
        continue
    
    # Merge: later values win
    merged = OrderedDict()
    for r in rule_list:
        for p, v in r.declarations.items():
            if p in merged:
                conflicts_removed += 1
            merged[p] = v
    
    # Rebuild rule text
    body = ';\n  '.join([f'{p}: {v}' for p, v in merged.items()])
    # Use the last rule's full_text as template for position
    last_rule = rule_list[-1].full_text
    brace_start = last_rule.find('{')
    brace_end = last_rule.rfind('}')
    
    # Rebuild using original indentation
    indent = '  '
    new_rule = f'{sel} {{\n{indent}{body};\n}}'
    merged_rules.append(new_rule)

print(f'Conflicts resolved (properties overridden): {conflicts_removed}')
print(f'Merged rules: {len(merged_rules)}')

# Also track how many entire rules were removed (duplicate selectors)
removed_rules = sum(len(v) - 1 for v in selector_rules.values())
print(f'Duplicate selector blocks collapsed: {removed_rules}')

# Rebuild CSS preserving order by first occurrence of each selector
seen = {}
ordered_rules = []
deduped_blocks = 0

for r in rules:
    norm_sel = re.sub(r'\s+', ' ', r.selector)
    if norm_sel not in seen:
        seen[norm_sel] = True
        ordered_rules.append(r.full_text)
    else:
        deduped_blocks += 1

print(f'Order-preserving dedup: {deduped_blocks} blocks removed')

# Now build the conflict-resolved version
# Re-parse ordered_rules to get selectors in order, then merge
ordered_selectors = []
seen2 = {}
for rt in ordered_rules:
    brace_start = rt.find('{')
    sel = rt[:brace_start].strip()
    norm_sel = re.sub(r'\s+', ' ', sel)
    if norm_sel not in seen2:
        seen2[norm_sel] = True
        ordered_selectors.append(norm_sel)

# Build final CSS with merged values
final_parts = []
for sel in ordered_selectors:
    rule_list = selector_rules[sel]
    merged = OrderedDict()
    for r in rule_list:
        for p, v in r.declarations.items():
            merged[p] = v
    
    body_parts = [f'  {p}: {v};' for p, v in merged.items()]
    final_parts.append(f'{sel} {{\n' + '\n'.join(body_parts) + '\n}')

# Add the header from the original
header_end = css.find(':root')
header = css[:header_end] if header_end > 0 else '/* Brand CSS */\n\n'

new_css = header + '\n\n'.join(final_parts)

out_path = 'DAW_bundle/site/lopezvelarde/brand/assets/css/brand.css'
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(new_css)

print(f'\n=== RESULT ===')
print(f'Size: {len(new_css)} chars ({len(css)} original)')
print(f'Lines: {new_css.count(chr(10))+1}')
print(f':root blocks: {new_css.count(":root {")}')

# Verify all sections present
checks = ['sp5-btn-back', 'NOTICIAS PAGE', 'SOCIAL FEEDS', 'SOBREESCRITURAS', 'scene-404']
for ck in checks:
    print(f'  {ck}: {ck in new_css}')

# Check no remaining conflicts
from collections import defaultdict
final_rules = []
buf = ''
depth = 0
for c in new_css:
    buf += c
    if c == '{': depth += 1
    elif c == '}':
        depth -= 1
        if depth == 0:
            bs = buf.find('{')
            if bs >= 0:
                final_rules.append((buf[:bs].strip(), buf[bs+1:-1].strip()))
            buf = ''

conflicts = 0
sel_props = defaultdict(dict)
for sel, body in final_rules:
    norm_sel = re.sub(r'\s+', ' ', sel)
    for d in body.split(';'):
        d = d.strip()
        if ':' in d:
            p, v = d.split(':', 1)
            p, v = p.strip(), v.strip()
            if p in sel_props[norm_sel] and sel_props[norm_sel][p] != v:
                conflicts += 1
            sel_props[norm_sel][p] = v

print(f'Remaining conflicts: {conflicts}')
