import re
from collections import defaultdict

path = 'DAW_bundle/site/lopezvelarde/brand/assets/css/brand.css'
with open(path, 'r', encoding='utf-8') as f:
    css = f.read()

# Parse all rules with their selectors and declarations
class Rule:
    def __init__(self, selector, declarations, line_num):
        self.selector = selector.strip()
        self.declarations = declarations.strip()
        self.line_num = line_num
        self.props = self._parse_props()
    
    def _parse_props(self):
        props = {}
        for decl in self.declarations.split(';'):
            decl = decl.strip()
            if ':' in decl:
                prop, val = decl.split(':', 1)
                props[prop.strip()] = val.strip()
        return props

# Parse CSS
rules = []
i = 0
line_num = 1
buf = ''
depth = 0
selector = ''

while i < len(css):
    c = css[i]
    # Skip comments
    if c == '/' and i+1 < len(css) and css[i+1] == '*':
        # Count newlines in comment
        j = i
        while j < len(css) and not (css[j] == '*' and j+1 < len(css) and css[j+1] == '/'):
            if css[j] == '\n': line_num += 1
            j += 1
        i = j + 2
        continue
    
    if c == '{':
        if depth == 0:
            selector = buf.strip()
        depth += 1
        buf += c
    elif c == '}':
        depth -= 1
        buf += c
        if depth == 0:
            # Extract declarations from between { and }
            brace_start = buf.find('{')
            if brace_start >= 0:
                decls = buf[brace_start+1:-1].strip()
                if selector and decls:
                    rules.append(Rule(selector, decls, line_num))
            buf = ''
    elif c == '\n':
        line_num += 1
        buf += c
    else:
        buf += c
    i += 1

print(f'=== CONFLICT ANALYSIS ===')
print(f'Total rules parsed: {len(rules)}')
print()

# 1. Find rules with same selector but conflicting property values
print('--- 1. SAME SELECTOR, CONFLICTING VALUES ---')
selector_groups = defaultdict(list)
for r in rules:
    norm_sel = re.sub(r'\s+', ' ', r.selector)
    selector_groups[norm_sel].append(r)

conflict_count = 0
for sel, group in selector_groups.items():
    if len(group) < 2:
        continue
    # Compare all pairs
    for i in range(len(group)):
        for j in range(i+1, len(group)):
            a, b = group[i], group[j]
            for prop, val_a in a.props.items():
                val_b = b.props.get(prop)
                if val_b and val_a != val_b:
                    conflict_count += 1
                    print(f'\n  Selector: {sel[:80]}...' if len(sel) > 80 else f'\n  Selector: {sel}')
                    print(f'    Line {a.line_num}: {prop}: {val_a}')
                    print(f'    Line {b.line_num}: {prop}: {val_b}')

print(f'\nTotal selector conflicts: {conflict_count}')
print()

# 2. Find specificity conflicts (more specific vs less specific for same element)
print('--- 2. SPECIFICITY CONFLICTS (same property, different specificity) ---')
# Group by "base" - the last part of the selector (the element/class being styled)
# E.g., .sp5-card and .sp5-card:hover are related
prop_groups = defaultdict(list)
for r in rules:
    base_sel = re.sub(r'\s+', ' ', r.selector)
    # Extract the last class/tag in the selector
    for prop, val in r.props.items():
        prop_groups[(base_sel, prop)].append((r, val))

# 3. Find !important conflicts
print('--- 3. !IMPORTANT INCONSISTENCIES ---')
important_rules = defaultdict(list)
non_important = defaultdict(list)
for r in rules:
    for prop, val in r.props.items():
        if '!important' in val:
            important_rules[(r.selector, prop)].append((r, val))
        else:
            non_important[(r.selector, prop)].append((r, val))

# Find the same property used both with and without !important on the same selector
imp_conflicts = 0
for (sel, prop), imp_list in important_rules.items():
    norm_sel = re.sub(r'\s+', ' ', sel)
    for r, val in imp_list:
        key = (norm_sel, prop)
        if key in non_important:
            imp_conflicts += 1
            val_clean = val.replace(' !important', '').strip()
            for r2, val2 in non_important[key]:
                val2_clean = val2.strip()
                if val_clean != val2_clean:
                    print(f'\n  !important conflict for {norm_sel[:80]}')
                    print(f'    Line {r.line_num}: {prop}: {val}')
                    print(f'    Line {r2.line_num}: {prop}: {val2}')
                break

print(f'\nTotal !important conflicts: {imp_conflicts}')
print()

# 4. Find duplicate properties within same rule (inline conflict)
print('--- 4. INLINE CONFLICTS (same property twice in one rule) ---')
inline_conflicts = 0
for r in rules:
    seen = {}
    for prop in list(r.props.keys()):
        if prop in seen:
            inline_conflicts += 1
            print(f'\n  Line {r.line_num}: {r.selector[:60]}...')
            print(f'    {prop}: {seen[prop]} (first)')
            print(f'    {prop}: {r.props[prop]} (second)')
        seen[prop] = r.props[prop]

print(f'\nTotal inline conflicts: {inline_conflicts}')
print()

# 5. Check for nav-color vs background conflicts on same elements
print('--- 5. SEMANTIC CONFLICTS (color/background mismatches) ---')
# Check if same selector sets both color and background that might clash
# (e.g., sp5-btn with red text on red background)
semantic_conflicts = 0
for sel, group in selector_groups.items():
    combined = {}
    for r in group:
        for prop, val in r.props.items():
            combined[prop] = val
    if 'color' in combined and 'background' in combined:
        c = combined['color'].replace(' !important', '').strip()
        b = combined['background'].replace(' !important', '').strip()
        # Check if same color on both
        if c == b:
            semantic_conflicts += 1
            print(f'\n  Same color/bg: {sel[:60]}')
            print(f'    color: {c}')
            print(f'    background: {b}')

print(f'\nTotal semantic conflicts: {semantic_conflicts}')
print()

# Summary
print('=== SUMMARY ===')
print(f'Selector conflicts: {conflict_count}')
print(f'!important conflicts: {imp_conflicts}')
print(f'Inline conflicts: {inline_conflicts}')
print(f'Semantic conflicts: {semantic_conflicts}')
