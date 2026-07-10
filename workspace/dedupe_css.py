import re, os

base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
path = os.path.join(base, 'site', 'lopezvelarde', 'brand', 'assets', 'css', 'brand.css')

with open(path, 'r', encoding='utf-8-sig') as f:
    css = f.read()

# Parse CSS into rules
rules = []
buf = ''
depth = 0
i = 0
while i < len(css):
    c = css[i]
    if c == '/' and i+1 < len(css) and css[i+1] == '*':
        buf += '/*'
        i += 2
        while i < len(css):
            buf += css[i]
            if css[i] == '*' and i+1 < len(css) and css[i+1] == '/':
                buf += css[i+1]
                i += 1
                break
            i += 1
        i += 1
        continue
    buf += c
    if c == '{':
        depth += 1
    elif c == '}':
        depth -= 1
        if depth == 0:
            rules.append(buf)
            buf = ''
    i += 1

remaining = buf.strip()
if remaining:
    rules.append(remaining)

# Deduplicate
seen = {}
unique = []
dupes = 0
for rule in rules:
    norm = re.sub(r'\s+', ' ', rule).strip()
    norm = re.sub(r';\s*}', ';}', norm)
    if norm not in seen:
        seen[norm] = True
        unique.append(rule)
    else:
        dupes += 1

header = """/* ============================================================
   BRAND CSS - Lopez Velarde
   Source: Divi Theme Options Custom CSS - Deduplicated
   Generated: 2026-07-06
   ============================================================ */

"""

new_css = header + '\n'.join(unique)

out_path = os.path.join(base, 'site', 'lopezvelarde', 'brand', 'assets', 'css', 'brand-new.css')
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(new_css)

print(f"Original: {len(css)} bytes, {len(rules)} rules")
print(f"New: {len(new_css)} bytes, {len(unique)} unique rules, {dupes} duplicates removed")
print(f":root blocks: {new_css.count(':root {')}")
checks = ['sp5-btn-back', 'NOTICIAS PAGE', 'SOCIAL FEEDS', 'SOBREESCRITURAS', 'scene-404']
for ck in checks:
    print(f"  {ck}: {ck in new_css}")

# Quick dedup verification
rule_matches = re.findall(r'([.#a-zA-Z@][^{]*?)\s*\{', new_css)
sig_count = {}
dupe_check = 0
for m in rule_matches:
    sig = re.sub(r'\s+', ' ', m).strip()
    if len(sig) > 3:
        if sig in sig_count:
            dupe_check += 1
        else:
            sig_count[sig] = True
print(f"Remaining selector duplicates: {dupe_check}")

# BOM check
with open(out_path, 'rb') as f:
    first_bytes = f.read(3)
print(f"BOM: {first_bytes == b'\\xef\\xbb\\xbf'}")
