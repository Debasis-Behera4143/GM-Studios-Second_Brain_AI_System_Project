import base64
import hashlib
import hmac
import json
import time
import uuid

from fastapi import Header, HTTPException, status

from core.config import settings


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def _b64decode(raw: str) -> bytes:
    padding = "=" * (-len(raw) % 4)
    return base64.urlsafe_b64decode(raw + padding)


def create_session_token(user_id: uuid.UUID) -> str:
    payload = {
        "user_id": str(user_id),
        "iat": int(time.time()),
        "exp": int(time.time()) + settings.SESSION_TTL_SECONDS,
    }
    payload_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    payload_part = _b64encode(payload_bytes)
    signature = hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        payload_part.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return f"{payload_part}.{_b64encode(signature)}"


def verify_session_token(token: str) -> uuid.UUID:
    try:
        payload_part, signature_part = token.split(".", 1)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session token.") from exc

    expected_signature = hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        payload_part.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    actual_signature = _b64decode(signature_part)
    if not hmac.compare_digest(expected_signature, actual_signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session token.")

    try:
        payload = json.loads(_b64decode(payload_part))
        user_id = uuid.UUID(payload["user_id"])
        exp = int(payload["exp"])
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session token.") from exc

    if exp < int(time.time()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired.")

    return user_id


def get_current_user_id(x_session_token: str | None = Header(None, alias="X-Session-Token")) -> uuid.UUID:
    if not x_session_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing session token.")
    return verify_session_token(x_session_token)
