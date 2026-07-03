"""Validate all section JSON files for correct Spanish characters."""
import os, json, unicodedata

dst = 'DAW_bundle/site/sanpablo/references/Semana biblica/sections'
out = []

files = sorted(f for f in os.listdir(dst) if f.endswith('-pro.json'))
for fname in files:
    fpath = os.path.join(dst, fname)
    with open(fpath, 'rb') as f:
        raw = f.read()
    
    # Check for FFFD bytes
    fffd_count = raw.count(b'\xef\xbf\xbd')
    
    # Check for invalid UTF-8
    try:
        raw.decode('utf-8')
        valid_utf8 = True
    except:
        valid_utf8 = False
    
    # Check JSON validity
    try:
        json.loads(raw.decode('utf-8'))
        valid_json = True
    except json.JSONDecodeError as e:
        valid_json = False
        json_error = str(e)
    
    out.append(f'\n{fname}:')
    if not valid_utf8:
        out.append(f'  INVALID UTF-8')
    if not valid_json:
        out.append(f'  INVALID JSON: {json_error}')
    if fffd_count > 0:
        out.append(f'  WARNING: {fffd_count} FFFD replacement characters')
    
    # Parse and check non-ASCII chars
    if valid_utf8 and valid_json:
        data = json.loads(raw.decode('utf-8'))
        issues = []
        
        def check_string(s, path=''):
            if not isinstance(s, str):
                return
            for i, ch in enumerate(s):
                cp = ord(ch)
                if cp > 127:
                    # Valid Spanish chars
                    if cp == 0xFFFD:
                        issues.append(f'{path}: U+FFFD found')
                    elif cp == 0x201C or cp == 0x201D:
                        continue  # curly quotes - valid
                    elif cp >= 0x00C0 and cp <= 0x00FF:
                        continue  # Latin-1 supplement - valid
                    elif cp >= 0x0100:
                        pass  # Beyond Latin-1, check if known valid
                        # Em dash, en dash, etc
                        if cp in [0x2013, 0x2014, 0x2026, 0x00AB, 0x00BB]:
                            continue
                        uname = unicodedata.name(ch, '?')
                        issues.append(f'{path}: char U+{cp:04X} ({uname}) at pos {i}')
        
        def traverse(obj, path=''):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    traverse(v, f'{path}.{k}' if path else k)
            elif isinstance(obj, list):
                for i, v in enumerate(obj):
                    traverse(v, f'{path}[{i}]')
            elif isinstance(obj, str):
                check_string(obj, path)
        
        traverse(data)
        
        if issues:
            out.append(f'  ISSUES:')
            for issue in issues[:10]:
                out.append(f'    {issue}')
            if len(issues) > 10:
                out.append(f'    ... and {len(issues)-10} more')
        else:
            out.append(f'  ALL OK')

report = '\n'.join(out)
report_path = os.path.join(dst, '..', 'validation_report.txt')
with open(report_path, 'w', encoding='utf-8') as f:
    f.write(report)
print(f'Validation report written to {report_path}')
print(report)
