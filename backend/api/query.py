import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from core.auth import get_current_user_id
from core.database import get_db
from schemas.query import QueryRequest, QueryResponse
from services.query_service import generate_rag_response

router = APIRouter()

@router.post("/query", response_model=QueryResponse)
def query_notes(
    request: QueryRequest,
    db: Session = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    try:
        return generate_rag_response(db, user_id, request)
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        print(f"Query failure: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to answer that question right now.",
        )
