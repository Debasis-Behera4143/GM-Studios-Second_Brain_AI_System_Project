from core.database import SessionLocal, get_chroma
from models.models import Note
from ml.embeddings import create_embedding

def sync():
    db = SessionLocal()
    notes = db.query(Note).all()
    print(f"Found {len(notes)} notes in Postgres.")
    
    if not notes:
        print("No notes to sync.")
        return
        
    chroma = get_chroma()
    collection = chroma.get_or_create_collection("notes_collection")
    
    for note in notes:
        try:
            vector = create_embedding(note.content)
            collection.add(
                embeddings=[vector],
                documents=[note.content],
                metadatas=[{"user_id": str(note.user_id), "source_type": note.source_type or "system"}],
                ids=[str(note.id)]
            )
            print(f"Synced note {note.id}")
        except Exception as e:
            print(f"Failed to sync note {note.id}: {e}")
            
if __name__ == "__main__":
    sync()
