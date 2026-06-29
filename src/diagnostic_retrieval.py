"""Diagnostic: why does the RAG chain always return the same sources?"""
import sys, time, os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

os.environ["PYTHONIOENCODING"] = "utf-8"

import chromadb
from sentence_transformers import SentenceTransformer

from indexer import CHROMA_DB_DIR, COLLECTION_NAME
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

import warnings
warnings.filterwarnings("ignore")

print("=" * 60)
print("DIAGNOSTIC RETRIEVAL COMPLET")
print("=" * 60)

chroma_dir = str(CHROMA_DB_DIR)
client = chromadb.PersistentClient(path=chroma_dir)
collection = client.get_collection(COLLECTION_NAME)
total = collection.count()
print(f"\nCollection: {total} documents\n")

test_queries = [
    "Ou se trouve le module d'authentification ?",
    "Comment fonctionne la gestion des etudiants ?",
    "Qu'est-ce que Rafiki ?",
    "Quel temps fait-il aujourd'hui ?",
]

hf_emb = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

st_model = SentenceTransformer("all-MiniLM-L6-v2")

# ----------------------------------------------------------------
# Test A : Direct ChromaDB python client (SentenceTransformer)
# ----------------------------------------------------------------
print("--- TEST A : ChromaDB direct (SentenceTransformer) ---")
for q in test_queries:
    emb = st_model.encode(q).tolist()
    results = collection.query(query_embeddings=[emb], n_results=5)
    items = []
    for doc, meta, dist in zip(results['documents'][0], results['metadatas'][0], results['distances'][0]):
        items.append((meta.get('source','?'), meta.get('lines_start','?'), meta.get('lines_end','?'), dist))
    print(f"  Q: {q[:40]}")
    for src, ls, le, d in items:
        print(f"    [dist={d:.4f}] {src} (lignes {ls}-{le})")

# ----------------------------------------------------------------
# Test B : LangChain Chroma wrapper -> similarity_search_with_score
# ----------------------------------------------------------------
print("\n--- TEST B : LangChain Chroma wrapper ---")
vectorstore = Chroma(client=client, collection_name=COLLECTION_NAME, embedding_function=hf_emb)
for q in test_queries:
    docs = vectorstore.similarity_search_with_score(q, k=5)
    print(f"  Q: {q[:40]}")
    for doc, score in docs:
        src = doc.metadata.get('source','?')
        ls = doc.metadata.get('lines_start','?')
        le = doc.metadata.get('lines_end','?')
        print(f"    [score={score:.4f}] {src} (lignes {ls}-{le})")

# ----------------------------------------------------------------
# Test C : Full ConversationalRetrievalChain
# ----------------------------------------------------------------
print("\n--- TEST C : Chaene complete ConversationalRetrievalChain ---")
from langchain_classic.chains import ConversationalRetrievalChain
from langchain_classic.memory import ConversationBufferMemory
from langchain_core.prompts import PromptTemplate

PROMPT_TMPL = """CONTEXTE :
{context}

QUESTION : {question}

REPONSE DETAILLEE ET SOURCEE :"""

prompt = PromptTemplate(template=PROMPT_TMPL, input_variables=["context", "question"])
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True, output_key="answer")
retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

from llm_config import get_llm
llm = get_llm()

qa_chain = ConversationalRetrievalChain.from_llm(
    llm=llm,
    retriever=retriever,
    memory=memory,
    return_source_documents=True,
    combine_docs_chain_kwargs={"prompt": prompt},
)

for q in test_queries:
    print(f"\n  Q: {q[:50]}")
    result = qa_chain.invoke({"question": q})
    print(f"  Answer starts: {result['answer'][:80]}...")
    for doc in result.get("source_documents", []):
        src = doc.metadata.get('source','?')
        ls = doc.metadata.get('lines_start','?')
        le = doc.metadata.get('lines_end','?')
        print(f"    {src} (lignes {ls}-{le})")

print("\n" + "=" * 60)
print("DIAGNOSTIC TERMINE")
print("=" * 60)
