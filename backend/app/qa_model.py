from transformers import pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Tuple
from .models import Chunk
from sqlalchemy.orm import Session
import numpy as np

# Load QA pipeline once lazily
_qa_pipeline = None


def get_qa_pipeline():
    global _qa_pipeline
    if _qa_pipeline is None:
        # small extractive model suitable for CPU
        _qa_pipeline = pipeline(
            "question-answering", model="distilbert-base-cased-distilled-squad"
        )
    return _qa_pipeline


class Retriever:
    def __init__(self, db: Session):
        self.db = db
        self.chunks = []  # list of Chunk objects
        self.texts = []  # list of chunk.text
        self.ids = []  # list of chunk.id
        self.vectorizer = None
        self.tfidf_matrix = None
        self._build_index()

    def _build_index(self):
        # load all chunks from DB
        q = self.db.query(Chunk).all()
        self.chunks = q
        self.texts = [c.text for c in self.chunks]
        self.ids = [c.id for c in self.chunks]
        if len(self.texts) == 0:
            self.vectorizer = None
            self.tfidf_matrix = None
            return
        self.vectorizer = TfidfVectorizer(stop_words="english", max_features=20000)
        self.tfidf_matrix = self.vectorizer.fit_transform(self.texts)

    def retrieve(self, question: str, top_k: int = 3) -> List[Tuple[Chunk, float]]:
        if self.vectorizer is None or self.tfidf_matrix is None:
            return []
        q_vec = self.vectorizer.transform([question])
        scores = cosine_similarity(q_vec, self.tfidf_matrix)[0]
        # get top_k indices
        top_idx = np.argsort(scores)[-top_k:][::-1]
        results = []
        for idx in top_idx:
            results.append((self.chunks[idx], float(scores[idx])))
        return results


class QASystem:
    def __init__(self, db: Session):
        self.db = db
        self.retriever = Retriever(db)
        self.qa = get_qa_pipeline()

    def answer(self, question: str, top_k: int = 3) -> dict:
        retrieved = self.retriever.retrieve(question, top_k=top_k)
        if not retrieved:
            return {"answer": "", "sources": [], "score": 0.0}

        # For each retrieved chunk, ask the QA model and keep highest score
        best = {"answer": "", "score": 0.0, "chunk_id": None, "context": ""}
        for chunk, sim in retrieved:
            try:
                res = self.qa(question=question, context=chunk.text)
            except Exception:
                continue
            ans_score = float(res.get("score", 0.0))
            # combine model confidence with retrieval similarity as a simple heuristic
            combined_score = ans_score * 0.7 + sim * 0.3
            if combined_score > best["score"]:
                best = {
                    "answer": res.get("answer", ""),
                    "score": combined_score,
                    "chunk_id": chunk.id,
                    "context": chunk.text[:1000],  # trimmed context
                }
        # Prepare sources list (all retrieved)
        sources = [{"chunk_id": c.id, "score": s} for c, s in retrieved]
        return {
            "answer": best["answer"],
            "sources": sources,
            "score": best["score"],
            "context": best["context"],
        }
