from pathlib import Path
from typing import List

SENSITIVE_PATTERNS = [
    '.env', '.env.local', '.env.production',
    'secrets.json', '*.key', '*.pem',
    'config.prod.py', 'settings.prod.py',
    '__pycache__', 'node_modules',
    '.git', '.github',
    'venv/', 'env/', '.venv/',
    '*.pyc', '*.log', '*.tmp',
    'chroma_db/', 'chroma_db_cache/',
    'chromadb.zip',
]

INCLUDE_EXTENSIONS = {'.py', '.md', '.json', '.yaml', '.yml', '.toml', '.js', '.jsx', '.ts', '.tsx', '.css'}

EXCLUDE_DIR_PARTS = [
    '__pycache__', '.git', 'node_modules', '.venv', 'venv', 'env',
    '.next', 'chroma_db_cache', 'chromadb', '.cache',
    'output',
]

EXCLUDE_FILE_PARTS = [
    'package-lock.json', 'package.json',
]


def should_index(file_path: Path, repo_root: Path) -> bool:
    rel = str(file_path.relative_to(repo_root)).replace('\\', '/')
    for pat in EXCLUDE_DIR_PARTS:
        if '/' + pat + '/' in rel or rel.startswith(pat + '/') or rel == pat:
            return False
    for pat in EXCLUDE_FILE_PARTS:
        if file_path.name == pat:
            return False
    if file_path.suffix.lower() not in INCLUDE_EXTENSIONS:
        return False
    if rel.startswith('.'):
        return False
    return True


def discover_files(repo_path: Path) -> List[Path]:
    files = []
    excluded = 0
    total = 0
    for f in repo_path.rglob('*'):
        if not f.is_file():
            continue
        total += 1
        if should_index(f, repo_path):
            files.append(f)
        else:
            excluded += 1
    print(f"Discover : {len(files)} files to index, {excluded} excluded (of {total} total)")
    return sorted(files)
