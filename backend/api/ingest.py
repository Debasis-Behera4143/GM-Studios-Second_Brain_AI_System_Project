import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from core.auth import get_current_user_id
from core.database import get_db
from schemas.notes import NoteCreate, IngestResponse
from services.ingest_service import process_ingestion

router = APIRouter()

@router.post("/ingest", response_model=IngestResponse)
async def ingest_note(
    note_in: NoteCreate,
    db: Session = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    try:
        note = await process_ingestion(db=db, note_in=note_in, user_uuid=user_id)
        return IngestResponse(status="success", note_id=note.id, message="Note saved successfully.")
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid note payload.") from exc
    except Exception as exc:
        db.rollback()
        print(f"Ingest failure: {exc}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to save note right now.")
