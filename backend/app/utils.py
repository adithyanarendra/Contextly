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


def clean_text(text: str) -> str:
    """Remove weird characters, collapse whitespace, normalize colons/numbers."""
    text = re.sub(r"\n+", "\n", text)  # collapse multiple newlines
    text = re.sub(r" {2,}", " ", text)  # collapse multiple spaces
    text = re.sub(r"[^\w\s.,:/()%-]", "", text)  # remove stray symbols
    return text.strip()


def extract_text_from_pdf(path: str) -> str:
    text_parts = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text_parts.append(t)
    return clean_text("\n".join(text_parts))


def extract_text_from_docx(path: str) -> str:
    doc = DocxDocument(path)
    paragraphs = [p.text for p in doc.paragraphs if p.text]
    return clean_text("\n".join(paragraphs))


def extract_text_from_txt(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return clean_text(f.read())


def sanitize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def chunk_text(
    text: str, chunk_size_words: int = CHUNK_SIZE, overlap: int = 20
) -> List[str]:
    """
    Pure regex-based chunking.
    Splits into sentence-like chunks and keeps overlap to preserve context.
    """
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", text)

    chunks = []
    current = []
    count = 0

    for sentence in sentences:
        words = sentence.split()
        if count + len(words) > chunk_size_words:
            chunks.append(" ".join(current))
            current = current[-overlap:]  # keep overlap
            count = len(current)
        current.extend(words)
        count += len(words)

    if current:
        chunks.append(" ".join(current))

    return chunks
