from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from db import SessionLocal, engine, Base
from models import Note
from rag import add_note_to_vector, query_notes
from llm import generate_answer
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

class NoteRequest(BaseModel):
    content: str

Base.metadata.create_all(bind=engine)

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all (for dev)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DB dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Add Note
@app.post("/add_note")
def add_note(note: NoteRequest, db: Session = Depends(get_db)):
    new_note = Note(content=note.content)
    db.add(new_note)
    db.commit()
    db.refresh(new_note)

    add_note_to_vector(new_note.id, note.content)

    return {"message": "Note added successfully"}


# Query
class QueryRequest(BaseModel):
    query: str
@app.post("/query")
def query(req: QueryRequest):
    docs = query_notes(req.query)
    context = "\n".join(docs)

    answer = generate_answer(context, req.query)

    return {
        "answer": answer,
        "sources": docs
    }