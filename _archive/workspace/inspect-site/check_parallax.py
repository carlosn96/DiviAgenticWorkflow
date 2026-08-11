"""Check how many parallax sections exist and their background images."""
import urllib.request
import re

resp = urllib.request.urlopen('http://lopezvelarde.local/inicio/', timeout=15)
html = resp.read().decode('utf-8', errors='replace')

print("=== All parallax backgrounds in the page ===")
for m in re.finditer(r'et-pb-parallax-background[^>]*>', html):
    print(f'  {m.group()[:200]}')

print("\n=== All parallax wrappers ===")
count = 0
for m in re.finditer(r'et-pb-parallax-wrapper', html):
    count += 1
print(f'  Total: {count} parallax wrappers')

print("\n=== Checking section background styles ===")
# Look for the section-specific inline CSS
idx = html.find('et_pb_section_0')
if idx >= 0:
    chunk = html[max(0,idx-500):idx+500]
    # Show any style attributes
    style_idx = chunk.find('style=')
    if style_idx >= 0:
        print(f'  Section has style attribute')
        print(f'  {chunk[style_idx:style_idx+200]}')
    else:
        print(f'  Section has NO style attribute (native CSS only)')
