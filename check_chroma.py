import chromadb
from chromadb.config import Settings

client = chromadb.HttpClient(host='localhost', port=8000)
try:
    collection = client.get_collection("notes_collection")
    count = collection.count()
    print(f"Total notes in ChromaDB: {count}")
    if count > 0:
        results = collection.get(limit=5)
        print("Sample data:", results)
except Exception as e:
    print(f"Error connecting or getting collection: {e}")
