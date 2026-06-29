import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r"H:\Study\Projects\Assistant Repsitory\Repository-Assistant")

from pathlib import Path
from rag_chain import build_qa_chain

repo = Path(r"H:\Study\Projects\Assistant Repsitory\Rafiki")
qa = build_qa_chain(repo)

questions = [
    "Où est gérée l'authentification ?",
    "Quelle est la couleur du ciel ?",
]

for q in questions:
    print(f"\n{'='*60}")
    print(f"Q: {q}")
    print(f"{'='*60}")
    result = qa.invoke({"question": q})
    answer = result["answer"]
    sources = result.get("source_documents", [])

    print(f"A: {answer[:400]}")
    print()
    if sources:
        print(f"Sources ({len(sources)}):")
        for s in sources[:3]:
            meta = s.metadata
            print(f"  - {meta.get('source', '?')} (lignes {meta.get('lines_start', '?')}-{meta.get('lines_end', '?')})")
    else:
        print("(aucune source)")
    print()
