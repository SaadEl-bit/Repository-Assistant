import json
import re
import sys
from pathlib import Path
from typing import List

from ingestion import Chunk, _make_id
from llm_config import REPO_PATH

SENSITIVE_KEYWORDS = [
    'password', 'secret', 'token', 'api_key', 'private_key',
    'api-key', 'secret_key', 'auth_token', 'credentials',
]
TOKEN_PATTERN = re.compile(r'[A-Za-z0-9_\-\.]{32,}')
URL_PATTERN = re.compile(r'https?://[^\s"\'\)]+')

COMPLEXITY_THRESHOLD = 10


# ---------------------------------------------------------------------------
# 4.1 — Sensitive file scan
# ---------------------------------------------------------------------------

_FILE_CACHE: dict = {}

def _get_indexed_files(repo_root: Path) -> List[Path]:
    key = str(repo_root)
    if key not in _FILE_CACHE:
        from config import discover_files
        _FILE_CACHE[key] = discover_files(repo_root)
    return _FILE_CACHE[key]


def scan_sensitive(repo_root: Path) -> List[Chunk]:
    findings = []
    files = _get_indexed_files(repo_root)

    for f in files:
        try:
            if f.stat().st_size > 1_000_000:
                continue
            content = f.read_text(encoding='utf-8', errors='replace')
        except Exception:
            continue
        rel = str(f.relative_to(repo_root))

        lines = content.splitlines()
        for i, line in enumerate(lines, 1):
            lower = line.lower()
            if any(kw in lower for kw in SENSITIVE_KEYWORDS):
                findings.append({
                    'file': rel,
                    'line': i,
                    'type': 'keyword_match',
                    'match': line.strip()[:100],
                })
            if TOKEN_PATTERN.search(line):
                findings.append({
                    'file': rel,
                    'line': i,
                    'type': 'token_pattern',
                    'match': line.strip()[:100],
                })
            if URL_PATTERN.search(line):
                findings.append({
                    'file': rel,
                    'line': i,
                    'type': 'url_pattern',
                    'match': line.strip()[:100],
                })

    content = json.dumps(findings, indent=2, ensure_ascii=False)
    print(f"Sensitive scan: {len(findings)} potential issues found")
    if not findings:
        content = json.dumps([{"message": "Aucun fichier sensible détecté"}], indent=2)

    return [Chunk(
        id=_make_id('critical_analysis', 'sensitive', 'scan', 1),
        content=content,
        metadata={
            'source': 'critical_analysis',
            'type': 'critical_analysis',
            'critical_category': 'sensitive',
            'name': 'sensitive_files_scan',
            'language': 'json',
        }
    )]


# ---------------------------------------------------------------------------
# 4.2 — Radon complexity analysis
# ---------------------------------------------------------------------------

def scan_complexity(repo_root: Path) -> List[Chunk]:
    try:
        from radon.complexity import cc_visit
    except ImportError:
        print("radon not installed, skipping complexity analysis")
        return []

    findings = {}
    files = _get_indexed_files(repo_root)
    py_files = [f for f in files if f.suffix == '.py']

    for f in sorted(py_files):
        rel = str(f.relative_to(repo_root))
        try:
            code = f.read_text(encoding='utf-8', errors='replace')
        except Exception:
            continue
        try:
            blocks = cc_visit(code)
            for b in blocks:
                if b.complexity > COMPLEXITY_THRESHOLD:
                    if rel not in findings:
                        findings[rel] = []
                    findings[rel].append({
                        'name': b.name,
                        'type': b.__class__.__name__,
                        'lineno': b.lineno,
                        'complexity': b.complexity,
                    })
        except Exception:
            continue

    result = []
    for filepath, items in sorted(findings.items()):
        for item in items:
            result.append(item)

    content = json.dumps(result, indent=2, ensure_ascii=False)
    print(f"Complexity scan: {len(result)} functions/classes with complexity > {COMPLEXITY_THRESHOLD}")

    if not result:
        message = f"Aucune fonction/classe avec complexite > {COMPLEXITY_THRESHOLD} detectee"
        content = json.dumps([{"message": message}], indent=2)

    return [Chunk(
        id=_make_id('critical_analysis', 'complexity', 'scan', 1),
        content=content,
        metadata={
            'source': 'critical_analysis',
            'type': 'critical_analysis',
            'critical_category': 'complexity',
            'name': 'complex_functions_scan',
            'language': 'json',
        }
    )]


# ---------------------------------------------------------------------------
# 4.3 — Untested modules detection
# ---------------------------------------------------------------------------

def scan_untested(repo_root: Path) -> List[Chunk]:
    src_modules = set()
    test_modules = set()

    files = _get_indexed_files(repo_root)
    for f in files:
        if f.suffix != '.py':
            continue
        rel = str(f.relative_to(repo_root))
        parts = Path(rel).parts
        if parts[0] == 'src':
            module = '.'.join(parts[1:])
            if module != '__init__.py' and not module.endswith('__init__.py'):
                src_modules.add(module)
        elif parts[0] == 'tests' or 'test' in parts:
            module = '.'.join(parts[1:])
            test_modules.add(module)

    untested = []
    for sm in sorted(src_modules):
        stem = Path(sm).stem
        has_test = any(stem in tm for tm in test_modules)
        if not has_test:
            untested.append(sm)

    content = json.dumps(untested, indent=2, ensure_ascii=False)
    print(f"Untested scan: {len(untested)} modules without tests")

    if not untested:
        content = json.dumps([{"message": "Tous les modules ont des tests correspondants"}], indent=2)

    return [Chunk(
        id=_make_id('critical_analysis', 'untested', 'scan', 1),
        content=content,
        metadata={
            'source': 'critical_analysis',
            'type': 'critical_analysis',
            'critical_category': 'untested',
            'name': 'untested_modules_scan',
            'language': 'json',
        }
    )]


# ---------------------------------------------------------------------------
# 4.4 — Run all and index into ChromaDB
# ---------------------------------------------------------------------------

def run_critical_analysis(repo_root: Path, collection=None, model=None):
    chunks = []
    chunks.extend(scan_sensitive(repo_root))
    chunks.extend(scan_complexity(repo_root))
    chunks.extend(scan_untested(repo_root))

    if collection is not None and model is not None:
        from indexer import index_chunks
        print(f"Indexing {len(chunks)} critical analysis chunks...")
        index_chunks(chunks, model, collection)
        print(f"Total in collection now: {collection.count()}")

    return chunks


if __name__ == "__main__":
    import chromadb
    from sentence_transformers import SentenceTransformer

    print("=" * 50)
    print("Critical Analysis of Rafiki Repository")
    print("=" * 50)
    print()

    chunks = run_critical_analysis(REPO_PATH)

    print()
    print("Results:")
    for c in chunks:
        print(f"\n  --- {c.metadata.get('critical_category', '?')} ---")
        print(f"  Content preview: {c.content[:200]}")
