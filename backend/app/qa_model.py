import re
from typing import List, Optional, Tuple

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session
from transformers import pipeline

from .models import Chunk

# Load QA pipeline once lazily
_qa_pipeline = None

_qa_pipeline = None


def get_qa_pipeline():
    global _qa_pipeline
    if _qa_pipeline is None:
        _qa_pipeline = pipeline(
            "question-answering", model="deepset/roberta-base-squad2"
        )
    return _qa_pipeline


class Retriever:
    def __init__(self, db: Session):
        self.db = db
        self.embedding_model = SentenceTransformer("multi-qa-MiniLM-L6-cos-v1")
        self.chunks: List[Chunk] = []
        self.texts: List[str] = []
        self.ids: List[int] = []
        self.embeddings = None

        self._build_index()

    def _build_index(self):
        q = self.db.query(Chunk).all()
        self.chunks = q
        self.texts = [c.text for c in self.chunks]
        self.ids = [c.id for c in self.chunks]
        if not self.texts:
            self.embeddings = None
            return
        self.embeddings = self.embedding_model.encode(self.texts)

    def retrieve(
        self, question: str, top_k: int = 8, document_ids: Optional[List[int]] = None
    ) -> List[Tuple[Chunk, float]]:
        if self.embeddings is None:
            return []

        if document_ids:
            filtered = [
                (c, e)
                for c, e in zip(self.chunks, self.embeddings)
                if c.document_id in document_ids
            ]
            if not filtered:
                return []
            chunks, emb_list = zip(*filtered)
        else:
            chunks, emb_list = self.chunks, self.embeddings

        q_emb = self.embedding_model.encode([question])
        scores = cosine_similarity(q_emb, emb_list)[0]

        q_keywords = set(question.lower().split())
        boosted_scores = []
        for chunk, score in zip(chunks, scores):
            bonus = 0.05 * sum(1 for kw in q_keywords if kw in chunk.text.lower())
            boosted_scores.append(score + bonus)

        top_idx = np.argsort(boosted_scores)[-top_k:][::-1]
        return [(chunks[i], float(boosted_scores[i])) for i in top_idx]


class QASystem:
    def __init__(self, db: Session):
        self.db = db
        self.retriever = Retriever(db)
        self.qa = get_qa_pipeline()

    def _number_fallback(self, question: str, context: str) -> Optional[str]:
        """
        Extract number patterns from context:
        - Single values (0.209 kg)
        - Two values (1920 x 1080 px)
        - Three values (87.5 x 75 x 41.3 mm)
        - Ranges (20 Hz – 20 kHz)
        Prioritize units mentioned in the question.
        """
        units = [
            "kg",
            "g",
            "lbs",
            "lb",
            "mm",
            "cm",
            "m",
            "hz",
            "khz",
            "mhz",
            "ghz",
            "px",
            "in",
            "”",
            "mah",
            "v",
            "w",
            "hours",
            "minutes",
            "seconds",
        ]
        units_pattern = "|".join(units)

        patterns = [
            rf"\d+(?:\.\d+)?\s*x\s*\d+(?:\.\d+)?\s*x\s*\d+(?:\.\d+)?\s*(?:{units_pattern})",  # triple
            rf"\d+(?:\.\d+)?\s*x\s*\d+(?:\.\d+)?\s*(?:{units_pattern})",  # double
            rf"\d+(?:\.\d+)?\s*(?:{units_pattern})\s*[-–]\s*\d+(?:\.\d+)?\s*(?:{units_pattern})",  # range
            rf"\d+(?:\.\d+)?\s*(?:{units_pattern})",  # single
        ]

        matches = []
        for pattern in patterns:
            matches.extend(re.finditer(pattern, context, re.IGNORECASE))

        if not matches:
            return None

        # If question mentions a specific unit, prioritize closest match to that unit
        q_keywords = [kw for kw in units if kw in question.lower()]
        if q_keywords:
            best_match = None
            best_distance = float("inf")
            for m in matches:
                for kw in q_keywords:
                    idx_kw = context.lower().find(kw)
                    idx_num = m.start()
                    dist = abs(idx_num - idx_kw)
                    if dist < best_distance:
                        best_distance = dist
                        best_match = m.group(0)
            if best_match:
                return best_match

        # Otherwise, return the first match in priority order (triples > doubles > ranges > singles)
        return matches[0].group(0)

    def answer(
        self, question: str, top_k: int = 3, document_ids: Optional[List[int]] = None
    ) -> dict:
        retrieved = self.retriever.retrieve(
            question, top_k=max(top_k * 2, 8), document_ids=document_ids
        )
        if not retrieved:
            return {"answer": "", "sources": [], "score": 0.0}

        best = {"answer": "", "score": 0.0, "chunk_id": None, "context": ""}
        for chunk, sim in retrieved:
            try:
                res = self.qa(question=question, context=chunk.text)
            except Exception:
                continue

            ans_score = float(res.get("score", 0.0))
            combined_score = ans_score * 0.7 + sim * 0.3

            if not res.get("answer") or res["answer"].strip() == "" or ans_score < 0.4:
                num_ans = self._number_fallback(question, chunk.text)
                if num_ans:
                    res["answer"] = num_ans
                    combined_score = max(combined_score, 0.95)

            if combined_score > best["score"]:
                best = {
                    "answer": res.get("answer", ""),
                    "score": combined_score,
                    "chunk_id": chunk.id,
                    "context": chunk.text[:1000],
                }

        sources = [{"chunk_id": c.id, "score": s} for c, s in retrieved]
        return {
            "answer": best["answer"],
            "sources": sources,
            "score": best["score"],
            "context": best["context"],
        }
