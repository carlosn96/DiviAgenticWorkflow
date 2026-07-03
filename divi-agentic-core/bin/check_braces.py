import re
import sys

path = sys.argv[1] if len(sys.argv) > 1 else 'class-layout-engine.php'
with open(path, 'r') as f:
    text = f.read()

lines = text.split('\n')
stack = []
for i, line in enumerate(lines, 1):
    cleaned = re.sub(r"'[^']*'{|}[^']*'", '', line)
    cleaned = re.sub(r'\"[^\"]*\"{|}[^\"]*\"', '', cleaned)
    for ch in cleaned:
        if ch == '{':
            stack.append(i)
        elif ch == '}':
            if stack:
                stack.pop()
            else:
                print('Extra } line', i)

print('depth', len(stack), 'last opens', stack[-5:])
