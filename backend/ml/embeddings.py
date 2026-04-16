import hashlib
from functools import lru_cache

try:
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover - optional dependency fallback
    SentenceTransformer = None

FALLBACK_DIMENSION = 384

@lru_cache(maxsize=1)
def get_embedder_model():
    if SentenceTransformer is None:
        return None
    return SentenceTransformer('all-MiniLM-L6-v2')


def _fallback_embedding(text: str) -> list[float]:
    vector = [0.0] * FALLBACK_DIMENSION
    for token in text.lower().split():
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        for idx, byte in enumerate(digest):
            vector[idx % FALLBACK_DIMENSION] += byte / 255.0

    magnitude = sum(value * value for value in vector) ** 0.5
    if magnitude:
        vector = [value / magnitude for value in vector]
    return vector

def create_embedding(text: str) -> list[float]:
    """Generates a list of floats representing the embedding of the input text."""
    model = get_embedder_model()
    if model is None:
        return _fallback_embedding(text)

    try:
        embeddings = model.encode(text)
        return embeddings.tolist()
    except Exception:
        return _fallback_embedding(text)
