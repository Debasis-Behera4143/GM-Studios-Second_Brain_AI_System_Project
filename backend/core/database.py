from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from core.config import settings
import chromadb

# PostgreSQL connection optimizations
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ChromaDB
chroma_client = chromadb.HttpClient(host=settings.CHROMA_HOST, port=settings.CHROMA_PORT)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_chroma():
    return chroma_client
