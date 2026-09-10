import os
import sys

root = os.path.dirname(os.path.abspath(__file__))
skip_dirs = {'.git', 'tests', '__pycache__', 'node_modules', '.pytest_cache', 'dist', '.vscode', 'build', '.idea'}
valid_exts = {'.py', '.ts', '.tsx', '.js', '.jsx', '.html', '.css', '.scss', '.sql', '.yaml', '.yml', '.md'}

counts = {}
total_lines = 0
total_files = 0

for dirpath, dirs, files in os.walk(root):
    dirs[:] = [d for d in dirs if d not in skip_dirs]
    rel = os.path.relpath(dirpath, root)
    if rel == '.':
        top = 'root'
    else:
        top = rel.split(os.sep)[0]
    
    for f in files:
        ext = os.path.splitext(f)[1].lower()
        if ext in valid_exts:
            fpath = os.path.join(dirpath, f)
            try:
                with open(fpath, 'r', encoding='utf-8', errors='ignore') as fp:
                    lines = sum(1 for _ in fp)
                counts[top] = counts.get(top, 0) + lines
                total_lines += lines
                total_files += 1
            except Exception:
                pass

print("=== LOC BREAKDOWN ===")
for folder, cnt in sorted(counts.items(), key=lambda x: -x[1]):
    print(f"{folder:30s}: {cnt:>8,} lines")
print("---------------------------------------------")
print(f"TOTAL PROD LOC: {total_lines:,} across {total_files} files")
print(f"TARGET:         500,000")
print(f"GAP TO TARGET:  {max(0, 500000 - total_lines):,}")
