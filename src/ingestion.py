import ast
import json
import os
import re
from dataclasses import dataclass, field
from src.config import EXCLUDE_DIR_PARTS, EXCLUDE_FILE_PARTS, INCLUDE_EXTENSIONS
from pathlib import Path
from typing import List, Optional


@dataclass
class Chunk:
    id: str
    content: str
    metadata: dict = field(default_factory=dict)


def _sanitize_id(name: str) -> str:
    return re.sub(r'[^a-zA-Z0-9_]', '_', name)


def _make_id(source: str, ctype: str, name: str, line: int) -> str:
    src = _sanitize_id(source.replace('\\', '/'))
    nm = _sanitize_id(name)
    return f"{src}_{ctype}_{nm}_{line}"


# ---------------------------------------------------------------------------
# Python AST parser (Step 1.3)
# ---------------------------------------------------------------------------

def parse_python_file(file_path: Path) -> List[Chunk]:
    source_rel = str(file_path).replace('\\', '/')
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        source = f.read()

    try:
        tree = ast.parse(source, filename=str(file_path))
    except SyntaxError:
        return []

    chunks = []
    source_lines = source.splitlines()

    # Collect import lines
    import_lines = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            import_lines.append(node.lineno)

    if import_lines:
        import_chunk = '\n'.join(
            source_lines[import_lines[0] - 1:import_lines[-1]]
        )
        import_chunk = import_chunk.strip()
        if len(import_chunk) >= 50:
            chunks.append(Chunk(
                id=_make_id(source_rel, 'imports', 'all', import_lines[0]),
                content=import_chunk,
                metadata={
                    'source': source_rel,
                    'type': 'imports',
                    'name': 'all_imports',
                    'lines_start': import_lines[0],
                    'lines_end': import_lines[-1],
                    'language': 'python'
                }
            ))

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            start = node.lineno
            end = getattr(node, 'end_lineno', start)
            content = '\n'.join(source_lines[start - 1:end])
            content = content.strip()
            if len(content) >= 50:
                chunks.append(Chunk(
                    id=_make_id(source_rel, 'function', node.name, start),
                    content=content,
                    metadata={
                        'source': source_rel,
                        'type': 'function',
                        'name': node.name,
                        'lines_start': start,
                        'lines_end': end,
                        'language': 'python',
                        'docstring': ast.get_docstring(node) or ''
                    }
                ))

        elif isinstance(node, ast.ClassDef):
            start = node.lineno
            end = getattr(node, 'end_lineno', start)
            content = '\n'.join(source_lines[start - 1:end])
            content = content.strip()
            if len(content) >= 50:
                methods = [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                chunks.append(Chunk(
                    id=_make_id(source_rel, 'class', node.name, start),
                    content=content,
                    metadata={
                        'source': source_rel,
                        'type': 'class',
                        'name': node.name,
                        'lines_start': start,
                        'lines_end': end,
                        'language': 'python',
                        'methods': ','.join(methods) if methods else '',
                        'docstring': ast.get_docstring(node) or ''
                    }
                ))

    return chunks


# ---------------------------------------------------------------------------
# Markdown parser (Step 1.4)
# ---------------------------------------------------------------------------

def _split_markdown_sections(text: str) -> List[tuple]:
    sections = []
    lines = text.splitlines()
    current_title = "header"
    current_lines = []
    start_line = 1

    for i, line in enumerate(lines, 1):
        if re.match(r'^##+\s', line):
            if current_lines:
                sections.append((current_title, current_lines, start_line, i - 1))
            current_title = line.strip('# ').strip()
            current_lines = [line]
            start_line = i
        else:
            current_lines.append(line)

    if current_lines:
        sections.append((current_title, current_lines, start_line, len(lines)))

    return sections


def parse_markdown_file(file_path: Path) -> List[Chunk]:
    source_rel = str(file_path).replace('\\', '/')
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        text = f.read()

    if not text.strip():
        return []

    sections = _split_markdown_sections(text)
    chunks = []
    for title, lines, start, end in sections:
        content = '\n'.join(lines).strip()
        if len(content) < 50:
            continue
        chunks.append(Chunk(
            id=_make_id(source_rel, 'section', title, start),
            content=content,
            metadata={
                'source': source_rel,
                'type': 'documentation',
                'section': title,
                'lines_start': start,
                'lines_end': end,
                'language': 'markdown'
            }
        ))

    if not chunks:
        content = text.strip()
        if len(content) >= 50:
            chunks.append(Chunk(
                id=_make_id(source_rel, 'doc', 'full', 1),
                content=content,
                metadata={
                    'source': source_rel,
                    'type': 'documentation',
                    'section': 'full',
                    'lines_start': 1,
                    'lines_end': len(text.splitlines()),
                    'language': 'markdown'
                }
            ))

    return chunks


# ---------------------------------------------------------------------------
# Config file parser — JSON / YAML / TOML (Step 1.5)
# ---------------------------------------------------------------------------

def parse_config_file(file_path: Path) -> List[Chunk]:
    source_rel = str(file_path).replace('\\', '/')
    ext = file_path.suffix.lower()
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read().strip()

    if not content or len(content) < 50:
        return []

    fmt = ext.lstrip('.')
    return [Chunk(
        id=_make_id(source_rel, 'config', file_path.stem, 1),
        content=content,
        metadata={
            'source': source_rel,
            'type': 'config',
            'name': file_path.stem,
            'lines_start': 1,
            'lines_end': len(content.splitlines()),
            'language': 'config',
            'format': fmt
        }
    )]


# ---------------------------------------------------------------------------
# JS / TS frontend parser (Step 1.3 bis — text-based)
# ---------------------------------------------------------------------------

def parse_frontend_file(file_path: Path) -> List[Chunk]:
    source_rel = str(file_path).replace('\\', '/')
    ext = file_path.suffix.lower()

    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read().strip()

    if not content or len(content) < 50:
        return []

    lines = content.splitlines()
    return [Chunk(
        id=_make_id(source_rel, 'frontend', file_path.stem, 1),
        content=content,
        metadata={
            'source': source_rel,
            'type': 'frontend',
            'name': file_path.stem,
            'lines_start': 1,
            'lines_end': len(lines),
            'language': ext.lstrip('.')
        }
    )]


# ---------------------------------------------------------------------------
# Orchestrator — choose parser by extension (Step 1.6)
# ---------------------------------------------------------------------------

def parse_file(file_path: Path) -> List[Chunk]:
    ext = file_path.suffix.lower()
    if ext == '.py':
        return parse_python_file(file_path)
    elif ext == '.md':
        return parse_markdown_file(file_path)
    elif ext in ('.json', '.yaml', '.yml', '.toml'):
        return parse_config_file(file_path)
    elif ext in ('.js', '.jsx', '.ts', '.tsx', '.css'):
        return parse_frontend_file(file_path)
    return []


# ---------------------------------------------------------------------------
# Repository tree extraction (Step 1.7)
# ---------------------------------------------------------------------------

def extract_repo_tree(repo_path: Path) -> Chunk:
    lines = []
    repo_root = repo_path.resolve()
    lines.append(f"{repo_root.name}/")

    def _should_show_dir(dirname: str) -> bool:
        return dirname not in EXCLUDE_DIR_PARTS and not dirname.startswith('.')

    def _should_show_file(filename: str) -> bool:
        if filename in EXCLUDE_FILE_PARTS:
            return False
        ext = Path(filename).suffix.lower()
        return ext in INCLUDE_EXTENSIONS or ext == ''

    for dirpath, dirnames, filenames in os.walk(repo_root):
        dirnames[:] = [d for d in dirnames if _should_show_dir(d)]
        rel_dir = Path(dirpath).relative_to(repo_root)
        depth = len(rel_dir.parts)

        if depth == 0:
            indent = ""
            prefix = ""
        else:
            indent = "│   " * (depth - 1)
            prefix = "├── "

        dir_name = rel_dir.name if depth > 0 else ""
        if depth > 0:
            lines.append(f"{indent}{prefix}{dir_name}/")

        show_files = [f for f in sorted(filenames) if _should_show_file(f)]
        for i, fname in enumerate(show_files):
            child_prefix = "└── " if i == len(show_files) - 1 else "├── "
            lines.append(f"{indent}{'│   ' if depth > 0 else ''}{child_prefix}{fname}")

    content = '\n'.join(lines)
    return Chunk(
        id=_make_id('repo', 'architecture', 'tree', 0),
        content=content,
        metadata={
            'source': str(repo_root),
            'type': 'architecture',
            'name': 'repository_tree',
            'lines_start': 1,
            'lines_end': len(lines),
        }
    )


def build_chunks(repo_path: Path, files: List[Path]) -> List[Chunk]:
    all_chunks = []
    tree_chunk = extract_repo_tree(repo_path)
    all_chunks.append(tree_chunk)
    for f in files:
        chunks = parse_file(f)
        all_chunks.extend(chunks)
    print(f"Total chunks generated: {len(all_chunks)}")
    return all_chunks
