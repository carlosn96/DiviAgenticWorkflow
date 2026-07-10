import subprocess, re, json, os

r = subprocess.run(['.\\wp.bat', 'option', 'get', 'et_divi'], capture_output=True, text=True, cwd='C:\\Users\\Departamento WEB\\Local Sites\\lopezvelarde')
keys = re.findall(r"'([^']+)' =>", r.stdout)
design_keys = [k for k in sorted(keys) if any(t in k.lower() for t in 
    ['color','font','button','header','footer','link','bg_','text_','border','accent','radius','logo','primary_nav','secondary_nav'])]
for k in design_keys:
    print(k)
