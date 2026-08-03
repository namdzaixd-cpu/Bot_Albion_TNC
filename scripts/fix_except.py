import os, glob, re

def fix_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    changed = False
    for i, line in enumerate(lines):
        if re.search(r'^\s*except Exception:\s*$', line):
            indent = len(line) - len(line.lstrip())
            lines[i] = ' ' * indent + 'except Exception as e:\n' + ' ' * (indent + 4) + 'print(f"[Error] {e}")\n'
            changed = True
            
    if changed:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print(f'Fixed {filepath}')

for root, _, files in os.walk('bot'):
    for file in files:
        if file.endswith('.py'):
            fix_file(os.path.join(root, file))
