from sqlalchemy.orm import Session
from schemas.notes import NoteCreate
from models.models import Note, Tag, User
from core.database import get_chroma
from ml.nlp import extract_tags
from ml.embeddings import create_embedding
import uuid
import asyncio
import re
from io import BytesIO

import requests
from bs4 import BeautifulSoup

try:
    from pypdf import PdfReader
except Exception:  # pragma: no cover - optional dependency fallback
    PdfReader = None

try:
    from PIL import Image
    import pytesseract
except Exception:  # pragma: no cover - optional dependency fallback
    Image = None
    pytesseract = None


def _ensure_user(db: Session, user_uuid: uuid.UUID) -> User:
    existing_user = db.query(User).filter(User.id == user_uuid).first()
    if existing_user:
        return existing_user

    user = User(
        id=user_uuid,
        email=f"{user_uuid}@local.secondbrain"
    )
    db.add(user)
    db.flush()
    return user


def _extract_url_text(url: str) -> str:
    response = requests.get(url, timeout=12)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = " ".join(soup.get_text(separator=" ").split())
    return text[:4000]


def _generate_summary(content: str) -> str:
    if len(content) < 500:
        return ""

    sentences = re.split(r"(?<=[.!?])\s+", content.strip())
    if not sentences:
        return ""

    summary = " ".join(sentences[:3]).strip()
    return summary[:500]


def extract_text_from_file(filename: str, raw_bytes: bytes) -> str:
    lower_name = (filename or "uploaded_file").lower()

    if lower_name.endswith(".pdf"):
        if PdfReader is None:
            raise ValueError("PDF ingestion requires pypdf.")
        reader = PdfReader(BytesIO(raw_bytes))
        text_chunks: list[str] = []
        for page in reader.pages:
            page_text = page.extract_text() or ""
            if page_text.strip():
                text_chunks.append(page_text.strip())
        text = "\n\n".join(text_chunks).strip()
        if not text:
            raise ValueError("No readable text found in PDF.")
        return text[:4000]

    if lower_name.endswith((".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif")):
        if Image is None or pytesseract is None:
            raise ValueError("Image OCR requires pillow and pytesseract.")
        image = Image.open(BytesIO(raw_bytes))
        text = pytesseract.image_to_string(image).strip()
        if not text:
            raise ValueError("No readable text found in image.")
        return text[:4000]

    # Fallback to UTF-8 text files
    try:
        text = raw_bytes.decode("utf-8", errors="ignore").strip()
    except Exception as exc:
        raise ValueError(f"Unable to decode uploaded file: {exc}") from exc

    if not text:
        raise ValueError("Uploaded file is empty or unreadable.")
    return text[:4000]

async def process_ingestion(db: Session, note_in: NoteCreate, user_uuid: uuid.UUID) -> Note:
    cleaned_content = note_in.content.strip()
    metadata_json = dict(note_in.metadata_json or {})

    if note_in.source_type.lower() == "url":
        metadata_json.setdefault("source_url", cleaned_content)
        try:
            extracted = _extract_url_text(cleaned_content)
            if extracted:
                cleaned_content = extracted
        except Exception as exc:
            raise ValueError(f"Unable to extract URL content: {exc}") from exc

    generated_summary = _generate_summary(cleaned_content)
    loop = asyncio.get_event_loop()
    
    # 1. Clean Text & Extract tags (offloaded)
    extracted_tag_strings = await loop.run_in_executor(None, extract_tags, cleaned_content)
    
    # Process Tags in Postgres
    tag_objects = []
    for t_name in extracted_tag_strings:
        tag = db.query(Tag).filter(Tag.name == t_name).first()
        if not tag:
            tag = Tag(name=t_name)
            db.add(tag)
        tag_objects.append(tag)
    
    # 2. Add to DB
    _ensure_user(db, user_uuid)
    
    db_note = Note(
        user_id=user_uuid,
        content=cleaned_content,
        summary=generated_summary,
        source_type=note_in.source_type,
        metadata_json=metadata_json,
        tags=tag_objects
    )
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    
    # 3. Create Vector Embedding & Save to VectorDB (offloaded)
    vector = await loop.run_in_executor(None, create_embedding, cleaned_content)
    
    chroma = get_chroma()
    collection = chroma.get_or_create_collection(name="notes_collection")
    collection.add(
        ids=[str(db_note.id)],
        embeddings=[vector],
        documents=[cleaned_content],
        metadatas=[{"user_id": str(user_uuid), "source": note_in.source_type}]
    )
    
    return db_note
