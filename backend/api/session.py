import uuid

from fastapi import APIRouter

from core.auth import create_session_token
from core.config import settings
from schemas.session import SessionResponse

router = APIRouter()


@router.post("/session", response_model=SessionResponse)
def create_session() -> SessionResponse:
    user_id = uuid.uuid4()
    return SessionResponse(
        session_token=create_session_token(user_id),
        expires_in=settings.SESSION_TTL_SECONDS,
    )
