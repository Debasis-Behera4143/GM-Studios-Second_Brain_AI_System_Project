from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from core.database import Base, engine
import models.models # force load models
import asyncio
from jobs.resurfacing import resurface_job

# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.PROJECT_NAME)

@app.on_event("startup")
async def startup_event():
    if settings.ENABLE_RESURFACING_JOB:
        asyncio.create_task(resurface_job())

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Session-Token"],
)

@app.get("/health")
def health_check():
    return {"status": "ok"}

from api.ingest import router as ingest_router
from api.query import router as query_router
from api.session import router as session_router
from api.voice import router as voice_router
from api.resurface import router as resurface_router

app.include_router(session_router, prefix="/api", tags=["session"])
app.include_router(ingest_router, prefix="/api", tags=["ingest"])
app.include_router(query_router, prefix="/api", tags=["query"])
app.include_router(voice_router, prefix="/api", tags=["voice"])
app.include_router(resurface_router, prefix="/api", tags=["resurface"])
