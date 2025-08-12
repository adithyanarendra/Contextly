from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
import os
import uuid
from ..database import get_db
from ..models import Document, Chunk
from ..utils import (
    save_upload_file,
    extract_text_from_pdf,
    extract_text_from_docx,
    extract_text_from_txt,
    chunk_text,
)
from ..config import UPLOAD_DIR, CHUNK_SIZE

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("/")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    filename = f"{uuid.uuid4().hex}_{file.filename}"
    path = os.path.join(UPLOAD_DIR, filename)
    # save
    save_upload_file(file, path)

    # extract
    lower = file.filename.lower()
    if lower.endswith(".pdf"):
        text = extract_text_from_pdf(path)
    elif lower.endswith(".docx"):
        text = extract_text_from_docx(path)
    elif lower.endswith(".txt"):
        text = extract_text_from_txt(path)
    else:
        # try best-effort for other types
        text = extract_text_from_txt(path)
    
    # print("EXTRACTED TEXT SAMPLE:")
    # print(text[:1000])

    if not text or len(text.strip()) == 0:
        raise HTTPException(status_code=400, detail="No text found in uploaded file.")

    # create Document entry
    doc = Document(filename=file.filename, original_path=path)
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # chunk and store chunks
    chunks = chunk_text(text, chunk_size_words=CHUNK_SIZE)
    chunk_objs = []
    for i, c in enumerate(chunks):
        chunk_obj = Chunk(document_id=doc.id, text=c, position=i)
        db.add(chunk_obj)
        chunk_objs.append(chunk_obj)

    db.commit()

    return {"document_id": doc.id, "filename": file.filename, "chunks": len(chunks)}
