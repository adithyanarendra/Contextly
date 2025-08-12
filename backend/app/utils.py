import os
import re
import pdfplumber
from docx import Document as DocxDocument
from .config import UPLOAD_DIR, CHUNK_SIZE
from typing import List

os.makedirs(UPLOAD_DIR, exist_ok=True)


def save_upload_file(upload_file, destination_path: str):
    with open(destination_path, "wb") as f:
        f.write(upload_file.file.read())
    return destination_path


def extract_text_from_pdf(path: str) -> str:
    text_parts = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text_parts.append(t)
    return "\n".join(text_parts)


def extract_text_from_docx(path: str) -> str:
    doc = DocxDocument(path)
    paragraphs = [p.text for p in doc.paragraphs if p.text]
    return "\n".join(paragraphs)


def extract_text_from_txt(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def sanitize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def chunk_text(text: str, chunk_size_words: int = CHUNK_SIZE) -> List[str]:
    """Simple chunk by words. Returns list of text chunks."""
    text = sanitize_whitespace(text)
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size_words):
        chunk = " ".join(words[i : i + chunk_size_words])
        chunks.append(chunk)
    return chunks
