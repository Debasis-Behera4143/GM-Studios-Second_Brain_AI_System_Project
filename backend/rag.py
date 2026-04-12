import chromadb
from embeddings import get_embedding

client = chromadb.Client()
collection = client.get_or_create_collection(name="notes")

def add_note_to_vector(id, text):
    embedding = get_embedding(text)
    collection.add(
        ids=[str(id)],
        documents=[text],
        embeddings=[embedding]
    )

def query_notes(query, k=3):
    embedding = get_embedding(query)
    results = collection.query(
        query_embeddings=[embedding],
        n_results=k
    )
    return results["documents"][0]