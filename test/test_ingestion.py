import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from config import discover_files
from ingestion import build_chunks, Chunk
from llm_config import REPO_PATH

files = discover_files(REPO_PATH)
chunks = build_chunks(REPO_PATH, files)

types: dict[str, int] = {}
for c in chunks:
    t = c.metadata.get('type', '?')
    types[t] = types.get(t, 0) + 1

print()
print('=' * 50)
print(f"Files found:      {len(files)}")
print(f"Chunks generated: {len(chunks)}")
print('=' * 50)
print()

print("Chunks by type:")
for t, n in sorted(types.items(), key=lambda x: -x[1]):
    print(f"  {t:20s} -> {n}")

print()
print("--- 3 sample chunks ---")
for i, c in enumerate(chunks[:3]):
    print()
    print(f"Chunk #{i+1}")
    print(f"  ID:       {c.id[:80]}")
    print(f"  Type:     {c.metadata.get('type', '?')}")
    print(f"  Source:   {c.metadata.get('source', '?')}")
    print(f"  Lines:    {c.metadata.get('lines_start', '?')}-{c.metadata.get('lines_end', '?')}")
    print(f"  Content:  {c.content[:100]}...")
