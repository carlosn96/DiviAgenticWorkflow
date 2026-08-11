import urllib.request, re
r = urllib.request.urlopen('http://lopezvelarde.local/inicio/', timeout=15)
h = r.read().decode('utf-8', errors='replace')

print('=== All CSS stylesheet links ===')
for m in re.finditer(r'href="([^"]*\.css[^"]*)"', h):
    url = m.group(1)
    if 'font' in url.lower() or 'google' in url.lower():
        print(f'  FONT: {url[:200]}')
    else:
        print(f'  {url[:200]}')

print()
print('=== Any @import or @font-face in page ===')
for m in re.finditer(r'(@import[^;]+;|@font-face[^}]+})', h):
    print(f'  {m.group()[:200]}')

print()
print('=== CSS variables ===')
for m in re.finditer(r'(?:--display|--ui|et_global_heading_font|et_global_body_font)\s*:[^;]+;', h):
    print(f'  {m.group().strip()}')

print()
print('=== Any script with font loading ===')
for m in re.finditer(r'<script[^>]*>.*?</script>', h, re.DOTALL):
    s = m.group()
    if 'font' in s.lower() or 'webfont' in s.lower():
        print(f'  Script ({len(s)} chars)')

print()
print('=== Dynamic CSS for page 19 ===')
for m in re.finditer(r'href="([^"]*19[^"]*\.css[^"]*)"', h):
    print(f'  {m.group(1)[:200]}')
