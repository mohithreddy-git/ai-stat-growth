from __future__ import annotations

import hashlib
import math
import re
import uuid
import zipfile
import zlib
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import DocumentChunk, UploadedDocument

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".txt"}
ALLOWED_MIME_TYPES = {
    "application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation", "text/plain", "application/octet-stream",
}


def _safe_filename(name: str | None) -> str:
    candidate = Path(name or "upload.txt").name
    candidate = re.sub(r"[^A-Za-z0-9._ -]", "_", candidate).strip(" .")
    if not candidate or Path(candidate).suffix.lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=415, detail="Supported files are PDF, DOCX, PPTX, and TXT")
    return candidate


def _xml_text(blob: bytes) -> str:
    root = ElementTree.fromstring(blob)
    return " ".join(node.text.strip() for node in root.iter() if node.text and node.text.strip())


def _extract_pdf(blob: bytes) -> list[tuple[str, int | None, int | None, str | None]]:
    try:
        from pypdf import PdfReader  # type: ignore
        pages = []
        for index, page in enumerate(PdfReader(blob).pages, 1):
            text = (page.extract_text() or "").strip()
            if text:
                pages.append((text, index, None, None))
        return pages
    except Exception:
        pass
    # Lightweight fallback for simple text PDFs: decode literal strings from
    # uncompressed or Flate-compressed content streams without external costs.
    streams = re.findall(rb"stream\r?\n(.*?)\r?\nendstream", blob, re.S)
    text_parts: list[str] = []
    for stream in streams:
        candidates = [stream]
        try:
            candidates.insert(0, zlib.decompress(stream))
        except zlib.error:
            pass
        for candidate in candidates:
            literals = re.findall(rb"\(((?:\\.|[^\\)])*)\)", candidate)
            if literals:
                text_parts.extend(item.decode("latin-1", errors="ignore") for item in literals)
                break
    raw = "\n".join(text_parts) if text_parts else blob.decode("latin-1", errors="ignore")
    raw = re.sub(r"[^\x09\x0a\x0d\x20-\x7e]+", " ", raw)
    return [(raw, 1, None, None)] if raw.strip() else []


def extract_pages(path: Path, content_type: str) -> list[tuple[str, int | None, int | None, str | None]]:
    extension = path.suffix.lower()
    blob = path.read_bytes()
    if extension == ".txt":
        return [(blob.decode("utf-8", errors="replace"), None, None, None)]
    if extension == ".pdf":
        return _extract_pdf(blob)
    if extension == ".docx":
        with zipfile.ZipFile(path) as archive:
            xml = archive.read("word/document.xml")
        return [(_xml_text(xml), None, None, "Document")]
    if extension == ".pptx":
        pages = []
        with zipfile.ZipFile(path) as archive:
            slide_names = sorted((name for name in archive.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)), key=lambda name: int(re.search(r"(\d+)", name).group(1)))
            for index, name in enumerate(slide_names, 1):
                pages.append((_xml_text(archive.read(name)), None, index, f"Slide {index}"))
        return pages
    raise HTTPException(status_code=415, detail="Unsupported document type")


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


EMBEDDING_DIMENSIONS = 96


def deterministic_embedding(text: str, dimensions: int = EMBEDDING_DIMENSIONS) -> list[float]:
    """Create a stable local embedding without an API or heavyweight runtime.

    This is a vector-store seam for the prototype: production can replace it
    with an approved embedding model while keeping chunk metadata and retrieval
    contracts unchanged.
    """
    vector = [0.0] * dimensions
    for token in re.findall(r"[a-z0-9]{2,}", text.casefold()):
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % dimensions
        sign = 1.0 if digest[4] & 1 else -1.0
        vector[index] += sign
    magnitude = math.sqrt(sum(value * value for value in vector))
    return [round(value / magnitude, 6) for value in vector] if magnitude else vector


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right:
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    return dot / (left_norm * right_norm) if left_norm and right_norm else 0.0


def chunk_pages(pages: Iterable[tuple[str, int | None, int | None, str | None]], max_chars: int = 900) -> list[dict]:
    chunks: list[dict] = []
    for text, page_number, slide_number, section in pages:
        clean = _clean(text)
        if not clean:
            continue
        words = clean.split()
        current: list[str] = []
        size = 0
        for word in words:
            if current and size + len(word) + 1 > max_chars:
                chunks.append({"text": " ".join(current), "page_number": page_number, "slide_number": slide_number, "section": section})
                current = []; size = 0
            current.append(word); size += len(word) + (1 if current else 0)
        if current:
            chunks.append({"text": " ".join(current), "page_number": page_number, "slide_number": slide_number, "section": section})
    return chunks


async def save_upload(db: Session, uploaded_by: int, upload: UploadFile) -> UploadedDocument:
    filename = _safe_filename(upload.filename)
    content_type = upload.content_type or "application/octet-stream"
    if content_type not in ALLOWED_MIME_TYPES and Path(filename).suffix.lower() != ".txt":
        raise HTTPException(status_code=415, detail="Unsupported document MIME type")
    max_bytes = get_settings().upload_max_mb * 1024 * 1024
    blob = await upload.read(max_bytes + 1)
    if len(blob) > max_bytes:
        raise HTTPException(status_code=413, detail=f"File exceeds the {get_settings().upload_max_mb} MB upload limit")
    upload_dir = Path(__file__).resolve().parents[2] / "data" / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    stored = upload_dir / f"{uuid.uuid4().hex}_{filename}"
    stored.write_bytes(blob)
    document = UploadedDocument(uploaded_by=uploaded_by, filename=filename, content_type=content_type, size_bytes=len(blob), status="uploaded", extracted_text_path=str(stored))
    db.add(document); db.commit(); db.refresh(document)
    return document


def process_document(db: Session, document_id: int) -> UploadedDocument:
    document = db.get(UploadedDocument, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    try:
        pages = extract_pages(Path(document.extracted_text_path or ""), document.content_type)
        chunks = chunk_pages(pages)
        if not chunks:
            raise ValueError("No extractable text found in document")
        db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document.id))
        for index, chunk in enumerate(chunks, 1):
            db.add(DocumentChunk(document_id=document.id, chunk_id=f"{document.id}:{index}", text=chunk["text"], page_number=chunk["page_number"], slide_number=chunk["slide_number"], section=chunk["section"], embedding_ref=f"local:{document.id}:{index}", embedding_json=deterministic_embedding(chunk["text"])))
        document.status = "processed"; document.processing_error = None
    except Exception as exc:
        document.status = "failed"; document.processing_error = str(exc)[:500]
        db.commit()
        raise HTTPException(status_code=422, detail=f"Document processing failed: {document.processing_error}") from exc
    db.commit(); db.refresh(document)
    return document


def list_documents(db: Session, user_id: int | None = None) -> list[dict]:
    query = select(UploadedDocument).order_by(UploadedDocument.id.desc())
    if user_id:
        query = query.where(UploadedDocument.uploaded_by == user_id)
    rows = db.scalars(query).all()
    return [{"id": row.id, "filename": row.filename, "content_type": row.content_type, "size_bytes": row.size_bytes, "status": row.status, "chunk_count": len(db.scalars(select(DocumentChunk).where(DocumentChunk.document_id == row.id)).all()), "processing_error": row.processing_error, "created_at": row.created_at} for row in rows]


def retrieve_chunks(db: Session, document_id: int, query: str, limit: int = 5) -> list[DocumentChunk]:
    """Retrieve relevant chunks and refuse zero-evidence matches.

    Lexical overlap keeps the deterministic prototype conservative for
    source-grounded answers. Stored local embeddings provide a semantic seam
    for paraphrased queries when their similarity is strong enough. A document
    question with neither signal returns no chunks instead of receiving a
    confident answer from an unrelated passage.
    """
    terms = {term.casefold() for term in re.findall(r"[A-Za-z0-9]{3,}", query)}
    query_embedding = deterministic_embedding(query)
    chunks = db.scalars(select(DocumentChunk).where(DocumentChunk.document_id == document_id)).all()
    scored: list[tuple[float, int, DocumentChunk]] = []
    for chunk in chunks:
        lexical = sum(1 for term in terms if term in chunk.text.casefold())
        stored_embedding = chunk.embedding_json if isinstance(chunk.embedding_json, list) else deterministic_embedding(chunk.text)
        semantic = max(0.0, cosine_similarity(query_embedding, stored_embedding))
        # Exact source terms are the strongest signal; semantic-only retrieval
        # is accepted only above a conservative threshold.
        if lexical == 0 and semantic < 0.25:
            continue
        scored.append((lexical * 2.0 + semantic, lexical, chunk))
    scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return [item[2] for item in scored[:limit]]
