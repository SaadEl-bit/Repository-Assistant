from pathlib import Path
from typing import List, Optional, Tuple

from sentence_transformers import CrossEncoder

CROSS_ENCODER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
CROSS_ENCODER_THRESHOLD = 0.0  # logit score: > 0 = relevant, < 0 = not relevant


class CrossEncoderScorer:
    def __init__(self, model_name: str = CROSS_ENCODER_MODEL):
        print(f"Loading cross-encoder: {model_name}")
        self.model = CrossEncoder(model_name)
        print("Cross-encoder ready.")

    def score_pairs(self, query: str, documents: List[str]) -> List[float]:
        pairs = [[query, doc] for doc in documents]
        scores = self.model.predict(pairs)
        return scores.tolist() if hasattr(scores, 'tolist') else list(scores)

    def filter_documents(self, query: str, documents: List, threshold: float = CROSS_ENCODER_THRESHOLD) -> List[Tuple]:
        texts = []
        original_docs = []
        for doc in documents:
            page_content = getattr(doc, 'page_content', None) or (doc[0] if isinstance(doc, tuple) else str(doc))
            texts.append(page_content)
            original_docs.append(doc)

        if not texts:
            return []

        scores = self.score_pairs(query, texts)
        filtered = []
        for doc, score in zip(original_docs, scores):
            if score >= threshold:
                filtered.append((doc, score))
        return filtered


_scorer_instance: Optional[CrossEncoderScorer] = None


def get_scorer() -> CrossEncoderScorer:
    global _scorer_instance
    if _scorer_instance is None:
        _scorer_instance = CrossEncoderScorer()
    return _scorer_instance


if __name__ == "__main__":
    scorer = get_scorer()
    q = "Ou se trouve le module authentification ?"
    docs = [
        "Le module authentification se trouve dans src/auth/",
        "La couleur du ciel est bleue",
    ]
    results = scorer.filter_documents(q, docs)
    print(f"Query: {q}")
    for doc, score in results:
        print(f"  score={score:.4f}  {doc}")
