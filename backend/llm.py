import requests

def generate_answer(context, query):
    prompt = f"""
You are a helpful AI assistant.

Answer ONLY using the context below.
If the answer is not in the context, say: "I don't have that in my notes."

Context:
{context}

Question:
{query}
"""

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "mistral:latest",
            "prompt": prompt,
            "stream": False
        }
    )

    return response.json()["response"]