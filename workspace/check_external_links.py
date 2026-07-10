import re, glob, os

sections_dir = 'DAW_bundle/site/lopezvelarde/page-defs/sections'
for f in sorted(glob.glob(os.path.join(sections_dir, '*.json'))):
    with open(f, encoding='utf-8') as fh:
        content = fh.read()
    # In JSON, quotes are escaped as \"
    urls = re.findall(r'href=\\"(https?://[^\\"]+)\\"', content)
    for url in urls:
        fname = os.path.basename(f)
        # Find the </a> closest after this url
        after_url = content.split(url, 1)[1] if url in content else ''
        close_a = after_url.split('</a>', 1)[0] if '</a>' in after_url else after_url
        missing = []
        if 'target=\\"_blank\\"' not in close_a:
            missing.append('target')
        if 'rel=\\"noopener\\"' not in close_a:
            missing.append('rel')
        status = 'OK' if not missing else f'MISSING: {", ".join(missing)}'
        print(f'{fname}: {url[:60]} [{status}]')
