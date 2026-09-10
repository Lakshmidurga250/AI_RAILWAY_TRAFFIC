import os
import zipfile

root = os.path.dirname(os.path.abspath(__file__))
zip_path = os.path.join(root, "AI_Railway_Traffic.zip")

print("Building AI_Railway_Traffic.zip including .git directory...")

skip_dirs = {'__pycache__', 'node_modules', '.pytest_cache', 'dist', '.vscode', 'build', '.idea', 'htmlcov'}
skip_files = {'.env', '.env.local', '.env.development', '.env.production', '.coverage'}

with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for f in files:
            if f.endswith('.zip') or f in skip_files:
                continue
            if f.startswith('.env') and f != 'example.env':
                continue
            full_path = os.path.join(dirpath, f)
            rel_path = os.path.relpath(full_path, root)
            zf.write(full_path, rel_path)

print(f"Successfully generated: {zip_path} (Size: {os.path.getsize(zip_path) / (1024*1024):.2f} MB)")
