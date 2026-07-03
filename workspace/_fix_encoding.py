"""Restore damaged UTF-8 Spanish characters in section JSON files."""
import os, json

dst = 'DAW_bundle/site/sanpablo/references/Semana biblica/sections'

# Map each corrupted file to the (path, old_substring, new_substring) fixes
fixes = {
    # cta-final: InscrFFFDbete ahora -> Inscríbete ahora
    'cta-final-pro.json': [
        ('button_text', 'Inscr\ufffdbete ahora', 'Inscríbete ahora'),
    ],
    
    # faq: multiple Spanish accented chars corrupted
    'faq-pro.json': [
        # escrFFFDenos -> escríbenos
        ('content', 'escr\ufffdenos a', 'escríbenos a'),
        # FFFDA quiFFFn estFFFD -> ¿A quién está
        ('content', '\ufffdA qui\ufffdn est\ufffd', '¿A quién está'),
        # BFFFDbplica -> Bíblica
        ('content', 'B\ufffdblica', 'Bíblica'),
        # pFFFDbplico -> público
        ('content', 'p\ufffdblico', 'público'),
        # teologFFFD a -> teología
        ('content', 'teolog\ufffda', 'teología'),
        # FFFDLos -> ¿Los
        ('content', '\ufffdLos ponentes', '¿Los ponentes'),
        # FFFDQuFFFD -> ¿Qué
        ('content', '\ufffdQu\ufffd', '¿Qué'),
        # otros asistentes
        ('content', 'asistentes\ufffd', 'asistentes?'),
    ],
    
    # program: 17:30 FFFD?? 19:00 -> 17:30 — 19:00 (em dash)
    'program-pro.json': [
        ('content', '\ufffd\ufffd\ufffd', '\u2014'),
    ],
    
    # register: participación, confirmación, Librería, Bíblica, ¡Registro, Lun - Vie —
    'register-pro.json': [
        ('content', 'participaci\ufffd\ufffd\ufffdn', 'participación'),
        ('content', '\ufffd\ufffd\ufffdRegistro', '\u00a1Registro'),
        ('content', 'B\ufffd\ufffd\ufffdblica', 'Bíblica'),
        ('content', 'confirmaci\ufffd\ufffd\ufffdn', 'confirmación'),
        ('content', 'Librer\ufffd\ufffd\ufffda', 'Librería'),
        ('content', 'Vie \ufffd\ufffd\ufffd 17:30', 'Vie — 17:30'),
    ],
    
    # tema-central: quotation marks and special chars
    'tema-central-pro.json': [
        ('content', '\ufffd\ufffdT\u00fa eres', '\u201cT\u00fa eres'),
        ('content', 'Pedro\ufffd\ufffd\ufffd.', 'Pedro\u201d,'),
        ('content', '\ufffd\ufffd\ufffd/span>', '\u201d</span>'),
    ],
    
    # testimonials: BíbFlica, transformFFF, María, José, etc
    'testimonials-pro.json': [
        # "La Semana Bíblica transformó
        ('content', 'Semana B\ufffdblica transform\ufffd', 'Semana Bíblica transformó'),
        # María Rodríguez
        ('content', 'Mar\ufffda Rodr\ufffdguez', 'María Rodríguez'),
        # estos días de estudio y oración
        ('content', 'd\ufffdas de estudio y oraci\ufffdn', 'días de estudio y oración'),
        # José Luis Hernández
        ('content', 'Jos\ufffd Luis Hern\ufffdndez', 'José Luis Hernández'),
        # quotes
        ('content', '\ufffdLa Semana', '\u201cLa Semana'),
    ],
}

for fname, file_fixes in fixes.items():
    fpath = os.path.join(dst, fname)
    with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
        text = f.read()
    
    data = json.loads(text)
    
    def apply_fix(obj, path_prefix=''):
        if isinstance(obj, str):
            for (match_path, old, new) in file_fixes:
                # Check if this string is at the right path
                # We use a simple suffix match for brevity
                if path_prefix.endswith(match_path) or '.' + match_path in path_prefix:
                    if old in obj:
                        obj = obj.replace(old, new)
                        print(f'  FIXED: {path_prefix}')
            return obj
        elif isinstance(obj, dict):
            return {k: apply_fix(v, f'{path_prefix}.{k}' if path_prefix else k) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [apply_fix(v, f'{path_prefix}[{i}]') for i, v in enumerate(obj)]
        return obj
    
    print(f'\n=== {fname} ===')
    data = apply_fix(data)
    
    with open(fpath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f'  Written: {fpath}')

print('\nDone!')
