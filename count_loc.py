import os

exts = {'.py', '.ts', '.tsx', '.js', '.jsx', '.css', '.html', '.sql', '.proto', '.yaml', '.yml'}
skip_dirs = {'.venv', 'node_modules', 'dist', 'build', '.git', '.system_generated', '__pycache__'}

counts = {}
phase_counts = {}

for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in skip_dirs]
    rel_dir = os.path.relpath(root, '.')
    top_dir = rel_dir.split(os.sep)[0] if rel_dir != '.' else 'root'

    for f in files:
        ext = os.path.splitext(f)[1]
        if ext in exts or f == 'Dockerfile':
            key = ext if ext else 'Dockerfile'
            path = os.path.join(root, f)
            try:
                with open(path, encoding='utf-8', errors='ignore') as fp:
                    lines = sum(1 for _ in fp)

                counts[key] = counts.get(key, {'files': 0, 'lines': 0})
                counts[key]['files'] += 1
                counts[key]['lines'] += lines

                phase_counts[top_dir] = phase_counts.get(top_dir, {'files': 0, 'lines': 0})
                phase_counts[top_dir]['files'] += 1
                phase_counts[top_dir]['lines'] += lines
            except Exception:
                pass

print("=" * 50)
print("UDT-X PLATFORM - CODEBASE METRICS (LOC)")
print("=" * 50)
print(f"{'Extension':<15} {'Files':<10} {'Lines of Code':>15}")
print("-" * 50)
total_files = 0
total_lines = 0
for k, v in sorted(counts.items(), key=lambda x: x[1]['lines'], reverse=True):
    print(f"{k:<15} {v['files']:^10} {v['lines']:>15,}")
    total_files += v['files']
    total_lines += v['lines']
print("-" * 50)
print(f"{'TOTAL':<15} {total_files:^10} {total_lines:>15,}")
print("\n" + "=" * 50)
print("LOC BREAKDOWN BY SUBSYSTEM / PHASE")
print("=" * 50)
print(f"{'Directory/Phase':<25} {'Files':<10} {'Lines':>12}")
print("-" * 50)
for k, v in sorted(phase_counts.items(), key=lambda x: x[1]['lines'], reverse=True):
    print(f"{k:<25} {v['files']:^10} {v['lines']:>12,}")
print("-" * 50)
