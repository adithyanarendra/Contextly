from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..database import get_db
from ..qa_model import QASystem
from ..models import QAHistory
from typing import Optional

router = APIRouter(prefix="/ask", tags=["ask"])


class AskRequest(BaseModel):
    question: str
    top_k: Optional[int] = 3  # number of chunks to retrieve
    # doc_id optional (not implemented per-doc retrieval for simplicity; can be extended)


@router.post("/")
def ask(req: AskRequest, db: Session = Depends(get_db)):
    if not req.question or req.question.strip() == "":
        raise HTTPException(status_code=400, detail="Question must be provided.")
    qa = QASystem(db)
    result = qa.answer(req.question, top_k=req.top_k)

    # Save to QA history
    source_ids = ",".join(str(s["chunk_id"]) for s in result.get("sources", []))
    qa_rec = QAHistory(
        question=req.question,
        answer=result.get("answer", ""),
        source_chunk_ids=source_ids,
    )
    db.add(qa_rec)
    db.commit()
    db.refresh(qa_rec)

    response = {
        "qa_id": qa_rec.id,
        "question": req.question,
        "answer": result.get("answer"),
        "score": result.get("score"),
        "sources": result.get("sources"),
    }
    return response
