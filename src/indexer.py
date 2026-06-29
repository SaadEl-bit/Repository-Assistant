import time
from pathlib import Path
from typing import List

import chromadb
from sentence_transformers import SentenceTransformer

from config import discover_files
from ingestion import build_chunks, Chunk

CHROMA_DB_DIR = Path(__file__).resolve().parent.parent / "chroma_db"
COLLECTION_NAME = "rafiki_chunks"
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
BATCH_SIZE = 100


def load_model():
    print(f"Loading embedding model: {EMBEDDING_MODEL}...")
    t0 = time.time()
    model = SentenceTransformer(EMBEDDING_MODEL)
    dim = model.get_sentence_embedding_dimension()
    print(f"  Done in {time.time() - t0:.1f}s | Dimensions: {dim}")
    return model


def get_collection(client: chromadb.PersistentClient, dim: int):
    existing = [c.name for c in client.list_collections()]
    if COLLECTION_NAME in existing:
        print(f"Collection '{COLLECTION_NAME}' already exists. Reusing.")
        return client.get_collection(COLLECTION_NAME)
    return client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )


def index_chunks(chunks: List[Chunk], model, collection):
    total = len(chunks)
    for i in range(0, total, BATCH_SIZE):
        batch = chunks[i:i + BATCH_SIZE]
        texts = [c.content for c in batch]
        ids = [c.id for c in batch]
        metadatas = [c.metadata for c in batch]

        t0 = time.time()
        embeddings = model.encode(texts, show_progress_bar=False).tolist()
        encode_time = time.time() - t0

        collection.add(
            ids=ids,
            documents=texts,
            metadatas=metadatas,
            embeddings=embeddings,
        )

        batch_num = i // BATCH_SIZE + 1
        total_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE
        print(f"  Batch {batch_num}/{total_batches} ({len(batch)} chunks) "
              f"encoded in {encode_time:.1f}s")

    print(f"Indexing complete. Total in collection: {collection.count()}")


def build_index(repo_path: Path, force_rebuild: bool = False):
    files = discover_files(repo_path)
    chunks = build_chunks(repo_path, files)
    print(f"Chunks to index: {len(chunks)}")

    model = load_model()
    dim = model.get_sentence_embedding_dimension()

    client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))

    if force_rebuild:
        try:
            client.delete_collection(COLLECTION_NAME)
            print("Previous collection deleted (force_rebuild).")
        except Exception:
            pass

    collection = get_collection(client, dim)
    existing = collection.count()

    if existing > 0 and not force_rebuild:
        print(f"Collection already has {existing} documents. "
              f"Use force_rebuild=True to re-index.")
        return collection, model, chunks

    index_chunks(chunks, model, collection)
    return collection, model, chunks


if __name__ == "__main__":
    from llm_config import REPO_PATH
    build_index(REPO_PATH, force_rebuild=True)
