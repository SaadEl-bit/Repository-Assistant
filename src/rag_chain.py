from pathlib import Path
from typing import List, Tuple

import chromadb
from langchain_classic.chains import ConversationalRetrievalChain
from langchain_classic.memory import ConversationBufferMemory
from langchain_core.prompts import PromptTemplate
from langchain_core.retrievers import BaseRetriever
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

from config import discover_files
from ingestion import build_chunks
from indexer import CHROMA_DB_DIR, COLLECTION_NAME, EMBEDDING_MODEL, index_chunks, load_model
from llm_config import get_llm

RELEVANCE_THRESHOLD = 0.80  # lenient: cross-encoder does the fine filtering
USE_CROSS_ENCODER = True
CROSS_ENCODER_K = 50  # retrieve more candidates for cross-encoder re-ranking

SYSTEM_PROMPT = """Tu es un assistant expert en analyse de repository logiciel.
Tu analyses le projet "Rafiki" (accompagnement scolaire 2ème année bac).

RÈGLES STRICTES :
1. Réponds UNIQUEMENT sur la base du CONTEXTE fourni ci-dessous.
2. Si le contexte ne permet pas de répondre, dis EXPLICITEMENT :
   "Je ne dispose pas d'informations suffisantes dans le repository pour répondre."
3. Cite TOUJOURS tes sources : nom du fichier et lignes concernées.
4. Ne fais aucune supposition hors du contexte.
5. Structure ta réponse de manière claire et technique.

CONTEXTE :
{context}

QUESTION : {question}

RÉPONSE DÉTAILLÉE ET SOURCÉE :"""


def _get_vectorstore():
    chroma_dir = str(CHROMA_DB_DIR)
    embedding_fn = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    persist_client = chromadb.PersistentClient(path=chroma_dir)
    return Chroma(
        client=persist_client,
        collection_name=COLLECTION_NAME,
        embedding_function=embedding_fn,
    )


def build_retriever(repo_path: Path, force_rebuild: bool = False):
    chroma_dir = str(CHROMA_DB_DIR)
    embedding_fn = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

    persist_client = chromadb.PersistentClient(path=chroma_dir)

    existing = [c.name for c in persist_client.list_collections()]
    if COLLECTION_NAME not in existing or force_rebuild:
        print("Building index first...")
        model = load_model()
        files = discover_files(repo_path)
        chunks = build_chunks(repo_path, files)

        if force_rebuild and COLLECTION_NAME in existing:
            persist_client.delete_collection(COLLECTION_NAME)

        collection = persist_client.create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )
        index_chunks(chunks, model, collection)

    vectorstore = Chroma(
        client=persist_client,
        collection_name=COLLECTION_NAME,
        embedding_function=embedding_fn,
    )
    return vectorstore.as_retriever(search_kwargs={"k": 5})


def check_relevance(results: List[Tuple]) -> bool:
    if not results:
        return False
    for doc, score in results:
        if score < RELEVANCE_THRESHOLD:
            return True
    return False


class RelevanceRetriever(BaseRetriever):
    """Wrapper that filters out irrelevant documents before passing to the chain.
    Optionally applies cross-encoder re-ranking as a second pass."""

    vectorstore: Chroma
    k: int = 5
    max_chars: int = 2000
    use_cross_encoder: bool = False

    class Config:
        arbitrary_types_allowed = True

    def _get_relevant_documents(self, query: str):
        docs_and_scores = self.vectorstore.similarity_search_with_score(query, k=self.k)
        filtered = []
        for doc, score in docs_and_scores:
            if score < RELEVANCE_THRESHOLD:
                if len(doc.page_content) > self.max_chars:
                    doc.page_content = doc.page_content[:self.max_chars]
                filtered.append(doc)

        if self.use_cross_encoder and filtered:
            try:
                from cross_encoder import get_scorer
                scorer = get_scorer()
                scored = scorer.filter_documents(query, filtered)
                filtered = [doc for doc, _ in scored]
            except Exception as e:
                print(f"Cross-encoder error (proceeding without): {e}")

        return filtered


def build_qa_chain(repo_path: Path, force_rebuild: bool = False):
    vectorstore = _get_vectorstore()
    retriever_k = CROSS_ENCODER_K if USE_CROSS_ENCODER else 3
    retriever = RelevanceRetriever(vectorstore=vectorstore, k=retriever_k, use_cross_encoder=USE_CROSS_ENCODER)

    prompt = PromptTemplate(
        template=SYSTEM_PROMPT,
        input_variables=["context", "question"],
    )

    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        output_key="answer",
    )

    llm = get_llm()

    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        return_source_documents=True,
        combine_docs_chain_kwargs={"prompt": prompt},
    )

    return qa_chain


if __name__ == "__main__":
    from llm_config import REPO_PATH
    qa = build_qa_chain(REPO_PATH)
    print("QA chain ready.")
