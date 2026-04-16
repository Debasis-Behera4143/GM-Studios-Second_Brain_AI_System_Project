import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.auth import get_current_user_id
from core.database import get_db, get_chroma
from ml.embeddings import create_embedding
from models.models import Note
from schemas.resurface import ResurfaceResponse, ResurfaceSuggestion

router = APIRouter()


@router.get("/resurface", response_model=ResurfaceResponse)
def get_resurfacing_suggestions(
    db: Session = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    seven_days_ago = datetime.utcnow() - timedelta(days=7)

    recent_notes = (
        db.query(Note)
        .filter(Note.user_id == user_id, Note.created_at >= seven_days_ago, Note.source_type != "system")
        .order_by(Note.created_at.desc())
        .limit(8)
        .all()
    )

    if not recent_notes:
        return ResurfaceResponse(suggestions=[])

    topic_seed = "\n".join(note.content for note in recent_notes if note.content)
    query_vector = create_embedding(topic_seed)

    chroma = get_chroma()
    collection = chroma.get_or_create_collection("notes_collection")
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=20,
        where={"user_id": str(user_id)},
    )

    ids = results.get("ids", [[]])
    docs = results.get("documents", [[]])
    note_ids = ids[0] if ids and isinstance(ids[0], list) else []
    contents = docs[0] if docs and isinstance(docs[0], list) else []

    if not note_ids:
        return ResurfaceResponse(suggestions=[])

    old_note_ids = {
        str(note_id)
        for (note_id,) in (
            db.query(Note.id)
            .filter(
                Note.user_id == user_id,
                Note.id.in_(note_ids),
                Note.created_at < seven_days_ago,
                Note.source_type != "system",
            )
            .all()
        )
    }

    suggestions = []
    for note_id, content in zip(note_ids, contents):
        if note_id not in old_note_ids:
            continue
        snippet = (content or "").strip()
        if not snippet:
            continue
        suggestions.append(
            ResurfaceSuggestion(
                id=note_id,
                content=snippet[:260],
            )
        )
        if len(suggestions) == 5:
            break

    return ResurfaceResponse(suggestions=suggestions)
