import asyncio
import os
import tempfile
import uuid

from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, status
from sqlalchemy.orm import Session
from core.auth import get_current_user_id
from core.database import get_db
from schemas.notes import NoteCreate, IngestResponse
from services.ingest_service import process_ingestion
from ml.speech import is_voice_available, transcribe_audio

router = APIRouter()

@router.post("/voice", response_model=IngestResponse)
async def ingest_voice(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    if not is_voice_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Voice transcription is not enabled on this server.",
        )

    suffix = os.path.splitext(file.filename or "audio.wav")[1] or ".wav"
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    file_location = temp_file.name
    try:
        temp_file.write(await file.read())
        temp_file.close()

        loop = asyncio.get_event_loop()
        transcription = await loop.run_in_executor(None, transcribe_audio, file_location)
        note_in = NoteCreate(content=transcription, source_type="voice")
        note = await process_ingestion(db=db, note_in=note_in, user_uuid=user_id)

        return IngestResponse(status="success", note_id=note.id, message="Voice note saved successfully.")
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        print(f"Voice ingest failure: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to process voice upload right now.",
        )
    finally:
        if os.path.exists(file_location):
            os.remove(file_location)
