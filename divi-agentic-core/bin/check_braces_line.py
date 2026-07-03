import re
import sys

path = sys.argv[1]
with open(path, 'r') as f:
    text = f.read()

# Strip single and double quoted strings crudely
clean = re.sub(r"'[^']*'", "''", text)
clean = re.sub(r'"[^"]*"', '""', clean)

open_c = clean.count('{')
close_c = clean.count('}')
print('open', open_c, 'close', close_c, 'diff', open_c - close_c)

# Line-by-line balance to localize
balance = 0
for i, line in enumerate(text.split('\n'), 1):
    # strip quoted strings
    line_clean = re.sub(r"'[^']*'", "''", line)
    line_clean = re.sub(r'"[^"]*"', '""', line_clean)
    open_l = line_clean.count('{')
    close_l = line_clean.count('}')
    balance += open_l - close_l
    if open_l != close_l:
        print(f'line {i}: +{open_l} -{close_l} balance {balance}')

print('final balance', balance)
