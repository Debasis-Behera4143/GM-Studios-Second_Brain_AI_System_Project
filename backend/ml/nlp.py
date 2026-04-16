import re
from functools import lru_cache

try:
    import spacy
except Exception:  # pragma: no cover - optional dependency fallback
    spacy = None

FALLBACK_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has",
    "he", "in", "is", "it", "its", "of", "on", "that", "the", "to", "was",
    "were", "will", "with", "this", "these", "those", "i", "you", "we",
}

@lru_cache(maxsize=1)
def get_nlp_model():
    if spacy is None:
        return None
    try:
        return spacy.load("en_core_web_sm")
    except OSError:
        return None


def _fallback_extract_tags(text: str) -> list[str]:
    words = re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", text.lower())
    seen: list[str] = []
    for word in words:
        if word in FALLBACK_STOPWORDS or word.isdigit():
            continue
        if word not in seen:
            seen.append(word)
    return seen[:10]

def extract_tags(text: str) -> list[str]:
    """Extract named entities and convert them to tags."""
    nlp = get_nlp_model()
    if nlp is None:
        return _fallback_extract_tags(text)

    doc = nlp(text)
    tags = set()
    for ent in doc.ents:
        if ent.label_ in ["PERSON", "ORG", "GPE", "PRODUCT", "EVENT", "WORK_OF_ART", "LOC", "FAC"]:
            tags.add(ent.text.lower())
    
    # Extract some meaningful noun chunks
    for chunk in doc.noun_chunks:
        if len(chunk.text.split()) <= 2 and not chunk.root.is_stop:
            tags.add(chunk.root.text.lower())
            
    extracted = list(tags)[:10]
    return extracted or _fallback_extract_tags(text)
