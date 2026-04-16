import asyncio
from datetime import datetime, timedelta
from core.database import SessionLocal, get_chroma
from models.models import Note, User
from services.query_service import call_llm

async def resurface_job():
    # Let the API come online before any background LLM work begins.
    await asyncio.sleep(60)
    while True:
        try:
            print("Running scheduled resurfacing job...")
            db = SessionLocal()
            run_resurfacing_for_all(db)
            db.close()
        except Exception as e:
            print(f"Resurfacing failure: {e}")
        
        # Run once a day (24 hours)
        await asyncio.sleep(86400)

def run_resurfacing_for_all(db):
    users = db.query(User).all()
    for user in users:
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_notes = db.query(Note).filter(Note.user_id == user.id, Note.created_at >= seven_days_ago).all()
        
        if not recent_notes:
            continue
            
        recent_texts = "\n- ".join([n.content for n in recent_notes])
        summary_prompt = f"Analyze the following recent notes and identify 3 core topics:\n{recent_texts}\nOutput only the topics."
        
        topics = call_llm(summary_prompt, "topics extraction", [])
        
        # Use simple Chroma similarity search with the extracted topics to find *older* notes
        from ml.embeddings import create_embedding
        vector = create_embedding(topics)
        
        chroma = get_chroma()
        collection = chroma.get_or_create_collection("notes_collection")
        
        # We search Chroma, but filter notes older than 7 days using metadata? 
        # For simplicity, just get top K and ignore recent ones in user logic
        results = collection.query(
            query_embeddings=[vector],
            n_results=5,
            where={"user_id": str(user.id)}
        )
        
        # Ideally, we send an email to user or save "Daily Digest" to DB here.
        docs = results.get('documents', [[]])[0]
        
        digest_prompt = f"Given the user's current interests:\n{topics}\nAnd their old notes:\n{docs}\nWrite a short daily digest resurfacing these ideas."
        digest = call_llm(digest_prompt, "daily digest generation", docs)
        
        # Storing summary back into DB as a system note.
        system_note = Note(
            user_id=user.id,
            content=f"Daily Digest:\n{digest}",
            source_type="system"
        )
        db.add(system_note)
        db.commit()
    
