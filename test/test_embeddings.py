import sys, io
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from indexer import CHROMA_DB_DIR, COLLECTION_NAME, load_model
import chromadb

model = load_model()

client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))
collection = client.get_collection(COLLECTION_NAME)

print(f"Documents in collection: {collection.count()}\n")

query = "Comment fonctionne l'authentification ?"
print(f"Query: {query}\n")

query_emb = model.encode([query]).tolist()
results = collection.query(query_embeddings=query_emb, n_results=3)
for i, (doc, meta, dist) in enumerate(zip(
    results['documents'][0],
    results['metadatas'][0],
    results['distances'][0]
)):
    print(f"--- Result #{i+1} (distance: {dist:.4f}) ---")
    print(f"  Source: {meta.get('source', '?')}")
    print(f"  Type:   {meta.get('type', '?')} / {meta.get('name', meta.get('section', '?'))}")
    print(f"  Lines:  {meta.get('lines_start', '?')}-{meta.get('lines_end', '?')}")
    preview = doc[:150].encode('utf-8', errors='replace').decode('utf-8')
    print(f"  Text:   {preview}...\n")
