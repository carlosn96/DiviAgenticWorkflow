"""
Final CSS cleaner: recursive parser, full conflict resolution, proper @media handling.
"""
import re
from collections import OrderedDict

path_in = 'DAW_bundle/site/lopezvelarde/brand/assets/css/brand.css'
with open(path_in, 'r', encoding='utf-8') as f:
    css = f.read()

# Step 1: Preserve comments during parse, reinsert them after
comments_map = {}
comment_counter = [0]

def preserve_comments(text):
    result = []
    i = 0
    while i < len(text):
        if text[i:i+2] == '/*':
            end = text.find('*/', i+2)
            if end < 0:
                break
            comment = text[i:end+2]
            marker = f'__CMT{comment_counter[0]}__'
            comments_map[marker] = comment
            comment_counter[0] += 1
            result.append(marker)
            i = end + 2
        else:
            result.append(text[i])
            i += 1
    return ''.join(result)

def restore_comments(text):
    for marker, comment in comments_map.items():
        text = text.replace(marker, comment)
    return text

css = preserve_comments(css)

# Step 2: Recursive CSS parser
def parse_css(text, start=0):
    """Parse CSS rules at the current nesting level. Returns list of (selector, body_or_children, is_at_rule)."""
    rules = []
    i = start
    buf = ''
    in_string = False
    string_char = None
    
    while i < len(text):
        c = text[i]
        
        # Handle strings (skip over them)
        if in_string:
            buf += c
            if c == '\\' and i+1 < len(text):
                buf += text[i+1]
                i += 2
                continue
            if c == string_char:
                in_string = False
            i += 1
            continue
        
        if c in '"\'':
            in_string = True
            string_char = c
            buf += c
            i += 1
            continue
        
        # Handle comments (already stripped but just in case)
        if c == '/' and i+1 < len(text) and text[i+1] == '*':
            i += 2
            continue
        
        if c == '{':
            # Start of a rule block
            selector = buf.strip()
            buf = ''
            depth = 1
            body = ''
            while i+1 < len(text) and depth > 0:
                i += 1
                if text[i] == '{': depth += 1
                elif text[i] == '}': depth -= 1
                if depth > 0:
                    body += text[i]
            
            # Determine if this is an @-rule (media, keyframes, etc.)
            is_at_rule = selector.startswith('@')
            
            if is_at_rule:
                # Don't parse children for @-rules yet
                rules.append(('@rule', selector, body))
            else:
                # Parse declarations
                props = OrderedDict()
                for decl in body.split(';'):
                    decl = decl.strip()
                    if ':' in decl:
                        p, v = decl.split(':', 1)
                        props[p.strip()] = v.strip()
                rules.append(('rule', selector, props))
            
            buf = ''
        elif c == '}':
            # Should not happen at top level
            break
        else:
            buf += c
        i += 1
    
    return rules

rules = parse_css(css)
print(f'Total rules: {len(rules)}')

# Separate by type
root_props_list = []
at_rules_list = []
regular_list = []

for rtype, selector, data in rules:
    if selector == ':root':
        root_props_list.append(data)
    elif rtype == '@rule':
        at_rules_list.append((selector, data))
    else:
        regular_list.append((selector, data))

# Merge all :root blocks
merged_root = OrderedDict()
for props in root_props_list:
    for p, v in props.items():
        merged_root[p] = v
print(f':root: {len(root_props_list)} blocks -> {len(merged_root)} vars')

# For @-rules: parse children and merge too
def process_at_rule_body(body):
    """Parse and merge rules inside an @-rule body."""
    inner_rules = parse_css(body)
    merged = {}
    for rtype, sel, data in inner_rules:
        if rtype == 'rule':
            # Parse properties from body string (it's already parsed into OrderedDict)
            if sel not in merged:
                merged[sel] = OrderedDict()
            for p, v in data.items():
                merged[sel][p] = v
        # If there are nested @-rules inside, we'd need recursion
        # but for our CSS that shouldn't happen
    # Rebuild body
    parts = []
    for sel, props in merged.items():
        body = '; '.join([f'{p}:{v}' for p, v in props.items()])
        parts.append(f'{sel} {{{body}}}')
    return ''.join(parts)

# Process @-rules: dedupe and merge
seen_at = {}
processed_at = []
for selector, body in at_rules_list:
    # Normalize for dedup
    norm_sel = re.sub(r'\s+', ' ', selector)
    
    # Process the body (merge internal rules)
    merged_body = process_at_rule_body(body)
    norm_body = re.sub(r'\s+', ' ', merged_body).strip()
    
    key = (norm_sel, norm_body)
    if key not in seen_at:
        seen_at[key] = True
        processed_at.append((selector, merged_body))

print(f'@-rules: {len(at_rules_list)} -> {len(processed_at)} unique')

# For regular rules: merge all occurrences, last value per property
regular_merged = OrderedDict()
for selector, props in regular_list:
    norm_sel = re.sub(r'\s+', ' ', selector)
    if norm_sel not in regular_merged:
        regular_merged[norm_sel] = (selector, OrderedDict())
    for p, v in props.items():
        regular_merged[norm_sel][1][p] = v

print(f'Regular: {len(regular_list)} -> {len(regular_merged)} merged')

# Build output
out = ':root {\n'
for p, v in merged_root.items():
    out += f'  {p}: {v};\n'
out += '}\n\n'

for norm_sel, (orig_sel, props) in regular_merged.items():
    out += f'{orig_sel} {{\n'
    for p, v in props.items():
        v = v.replace(';', '')  # remove trailing semicolons from body
        out += f'  {p}: {v};\n'
    out += '}\n\n'

for selector, body in processed_at:
    out += f'{selector} {{\n'
    # Format body with indentation  
    for line in body.split('}'):
        if line.strip():
            out += f'  {line.strip()}}}\n'
        else:
            out += '\n'

# Restore comments and write
out = restore_comments(out)
with open(path_in, 'w', encoding='utf-8') as f:
    f.write(out)

# Verify
print(f'\n=== RESULT ===')
print(f'Size: {len(out)} chars ({len(css)} original)')
print(f'Lines: {out.count(chr(10))+1}')
print(f':root blocks: {out.count(":root {")}')

# Check key sections
checks = ['sp5-btn-back', 'NOTICIAS PAGE', 'SOCIAL FEEDS', 'SOBREESCRITURAS', 'scene-404',
           'sp5-card:hover', 'sp5-glass', 'sp5-navbar', 'sp5-footer-title', '#page-container']
for ck in checks:
    if ck in out:
        print(f'  {ck}: OK')
    else:
        print(f'  {ck}: MISSING!')

# Count @media blocks  
import re as re2
media_count = len(re2.findall(r'@media\s*\(', out))
print(f'@media blocks: {media_count}')
print(f'@keyframes blocks: {len(re2.findall(r"@keyframes\s+", out))}')

# Check no remaining conflicts  
from collections import defaultdict
def scan_for_conflicts(text):
    r = parse_css(text)
    props = defaultdict(lambda: defaultdict(list))
    conflicts = 0
    for rtype, sel, data in r:
        if sel.startswith(':root') or sel.startswith('@'):
            continue
        if rtype == 'rule':
            norm_sel = re.sub(r'\s+', ' ', sel)
            for p, v in data.items():
                v_norm = re.sub(r'\s+', ' ', v.replace(' !important', '')).strip()
                for pv in props[norm_sel][p]:
                    pv_norm = re.sub(r'\s+', ' ', pv.replace(' !important', '')).strip()
                    if v_norm != pv_norm:
                        conflicts += 1
                props[norm_sel][p].append(v)
    return conflicts

remaining = scan_for_conflicts(out)
print(f'Remaining conflicts: {remaining}')
