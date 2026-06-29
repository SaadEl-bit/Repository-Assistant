import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from indexer import load_model
from critical_analysis import run_critical_analysis
from llm_config import REPO_PATH

print("=" * 50)
print("Phase 4 Validation: Critical Analysis Test")
print("=" * 50)

print("\n--- Running critical analysis ---")
chunks = run_critical_analysis(REPO_PATH)

print(f"\nTotal critical chunks: {len(chunks)}")
for chunk in chunks:
    cat = chunk.metadata.get('critical_category', '?')
    preview = chunk.content[:150].replace('\n', ' | ')
    print(f"\n  [{cat}] {preview}...")

print("\n--- Testing RAG query on critical zones ---")
from rag_chain import build_qa_chain

qa = build_qa_chain(REPO_PATH)
test_questions = [
    "Quels sont les fichiers sensibles dans le projet ?",
    "Quelles sont les fonctions complexes ?",
]

for q in test_questions:
    print(f"\nQ: {q}")
    try:
        result = qa.invoke({"question": q})
        answer = result.get("answer", "")
        sources = result.get("source_documents", [])
        print(f"R: {answer[:300]}")
        print(f"Sources: {len(sources)} document(s)")
        for s in sources:
            meta = s.metadata
            print(f"  - {meta.get('source', '?')} (type={meta.get('type', '?')})")
    except Exception as e:
        print(f"Error: {e}")

print("\n--- Test complete ---")
