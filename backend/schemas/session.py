from pydantic import BaseModel


class SessionResponse(BaseModel):
    session_token: str
    expires_in: int
