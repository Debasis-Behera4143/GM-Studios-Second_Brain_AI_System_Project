from sqlalchemy.orm import Session
from core.database import get_chroma
from core.config import settings
from ml.embeddings import create_embedding
from schemas.query import QueryRequest, QueryResponse, SourceNote
from models.models import Conversation, Note, User
import uuid
import time
import requests
from google import genai

SYSTEM_SOURCE_TYPES = {"system"}
SMALL_TALK_INPUTS = {
    "hi",
    "hello",
    "hey",
    "hii",
    "heyy",
    "good morning",
    "good afternoon",
    "good evening",
    "how are you",
    "who are you",
    "what can you do",
}
QUESTION_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "about",
    "can",
    "could",
    "do",
    "for",
    "from",
    "how",
    "i",
    "in",
    "is",
    "it",
    "me",
    "my",
    "of",
    "on",
    "please",
    "tell",
    "the",
    "to",
    "was",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "with",
}


def _build_fallback_answer(question: str, docs: list[str]) -> str:
    snippets = [doc.strip() for doc in docs if doc and doc.strip()]
    if not snippets:
        return (
            "I could not generate a full answer right now. "
            "If you want note-based answers, save a note about this topic first. "
            "For broader answers, configure the AI model on the server."
        )

    top_snippets = snippets[:3]
    if len(top_snippets) == 1:
        return f"Based on your saved notes: {top_snippets[0]}"

    joined = "\n\n".join(f"- {snippet}" for snippet in top_snippets)
    return (
        f"Based on your saved notes, here is the closest information for "
        f"\"{question}\":\n\n{joined}"
    )


def _normalize_text(text: str) -> str:
    return " ".join((text or "").strip().lower().split())


def _is_small_talk(question: str) -> bool:
    normalized = _normalize_text(question)
    return normalized in SMALL_TALK_INPUTS


def _small_talk_answer(question: str) -> str:
    normalized = _normalize_text(question)
    if normalized in {"hi", "hello", "hey", "hii", "heyy"}:
        return "Hello! I am your Second Brain. Ask me about your saved notes, or save a new note with the plus button."
    if normalized == "how are you":
        return "I am ready to help. Ask me a question about your notes, or save something new and I will use it later."
    if normalized == "who are you":
        return "I am your Second Brain assistant. I can save notes, search them, and answer questions from what you have stored."
    if normalized == "what can you do":
        return "I can save your notes, retrieve the most relevant ones, and answer questions using what you have stored."
    return "Hello! Ask me something specific, and I will do my best to answer from your saved notes."


def _has_meaningful_match(question: str, docs: list[str]) -> bool:
    normalized_question = _normalize_text(question)
    if not normalized_question or not docs:
        return False

    query_terms = {
        term
        for term in normalized_question.split()
        if len(term) > 2 and term not in QUESTION_STOPWORDS
    }
    if not query_terms:
        return False

    for doc in docs:
        normalized_doc = _normalize_text(doc)
        overlap_terms = [term for term in query_terms if term in normalized_doc]
        overlap = len(overlap_terms)
        overlap_ratio = overlap / max(len(query_terms), 1)

        # A single shared generic word like "capital" should not force the
        # answer to be grounded in notes. We only trust retrieval when a note
        # matches multiple meaningful terms or most of a short query.
        if overlap >= 2 or overlap_ratio >= 0.6:
            return True
    return False


def _normalize_query_results(results: dict) -> tuple[list[str], list[str], list[float]]:
    docs = results.get("documents", [[]])
    ids = results.get("ids", [[]])
    distances = results.get("distances", [[]])

    normalized_docs = docs[0] if docs and isinstance(docs[0], list) else []
    normalized_ids = ids[0] if ids and isinstance(ids[0], list) else []
    normalized_distances = distances[0] if distances and isinstance(distances[0], list) else []

    return normalized_docs, normalized_ids, normalized_distances


def _retrieve_from_chroma(user_id: uuid.UUID, query_vector: list[float]) -> tuple[list[str], list[str], list[float]]:
    chroma = get_chroma()
    collection = chroma.get_or_create_collection("notes_collection")

    # First, try the strict per-user filter used by the app today.
    try:
        results = collection.query(
            query_embeddings=[query_vector],
            n_results=5,
            where={"user_id": str(user_id)}
        )
        docs, ids, distances = _normalize_query_results(results)
        if docs:
            return docs, ids, distances
    except Exception as exc:
        print(f"Strict Chroma query failed: {exc}")

    # Some older indexed notes may be missing metadata. Fall back to a wider query
    # and then keep only the rows that belong to the current user by note id.
    try:
        results = collection.query(
            query_embeddings=[query_vector],
            n_results=15
        )
        docs, ids, distances = _normalize_query_results(results)
        if ids:
            return docs, ids, distances
    except Exception as exc:
        print(f"Relaxed Chroma query failed: {exc}")

    return [], [], []


def _retrieve_from_database(db: Session, user_id: uuid.UUID, request: QueryRequest) -> tuple[list[str], list[str], list[float]]:
    query_text = request.query.strip()
    if not query_text:
        return [], [], []

    notes = (
        db.query(Note)
        .filter(Note.user_id == user_id, ~Note.source_type.in_(SYSTEM_SOURCE_TYPES))
        .order_by(Note.created_at.desc())
        .all()
    )
    if not notes:
        return [], [], []

    query_terms = {term for term in query_text.lower().split() if term}

    ranked_notes: list[tuple[int, Note]] = []
    for note in notes:
        content = (note.content or "").lower()
        score = sum(1 for term in query_terms if term in content)
        if score > 0:
            ranked_notes.append((score, note))

    if not ranked_notes:
        ranked_notes = [(0, note) for note in notes[:5]]

    ranked_notes.sort(key=lambda item: (item[0], item[1].created_at), reverse=True)
    top_notes = [note for _, note in ranked_notes[:5]]

    docs = [note.content for note in top_notes]
    ids = [str(note.id) for note in top_notes]
    distances = [0.0 for _ in top_notes]
    return docs, ids, distances


def _filter_docs_for_user(db: Session, user_id: uuid.UUID, docs: list[str], ids: list[str], distances: list[float]) -> tuple[list[str], list[str], list[float]]:
    if not ids:
        return [], [], []

    allowed_note_ids = {
        str(note_id)
        for (note_id,) in (
            db.query(Note.id)
            .filter(
                Note.user_id == user_id,
                Note.id.in_(ids),
                ~Note.source_type.in_(SYSTEM_SOURCE_TYPES)
            )
            .all()
        )
    }

    filtered_docs: list[str] = []
    filtered_ids: list[str] = []
    filtered_distances: list[float] = []
    for doc_id, doc, distance in zip(ids, docs, distances):
        if doc_id in allowed_note_ids:
            filtered_ids.append(doc_id)
            filtered_docs.append(doc)
            filtered_distances.append(distance)

    return filtered_docs, filtered_ids, filtered_distances


def _distance_to_similarity(distance: float) -> float:
    if distance is None:
        return 0.0
    return round(1 / (1 + max(distance, 0.0)), 4)


def _build_notes_prompt(question: str, docs: list[str]) -> str:
    context = "\n---\n".join([f"Note {idx+1}: {doc}" for idx, doc in enumerate(docs)])
    return f"""
You are a helpful personal knowledge assistant.
Answer the user's question clearly using the notes below.
If the notes only partially answer the question, say what is supported by the notes and what is missing.
Do not invent facts that are not supported by the notes.

Notes:
{context}

User Question: {question}

Answer:
""".strip()


def _build_general_prompt(question: str) -> str:
    return f"""
You are a helpful assistant.
Answer the user's question naturally and clearly.
If it is a greeting or small talk, reply conversationally.
If the user asks for factual information, answer directly and briefly.

User Question: {question}

Answer:
""".strip()


def _ensure_user(db: Session, user_id: uuid.UUID) -> User:
    existing_user = db.query(User).filter(User.id == user_id).first()
    if existing_user:
        return existing_user

    user = User(
        id=user_id,
        email=f"{user_id}@local.secondbrain"
    )
    db.add(user)
    db.commit()
    return user

def generate_rag_response(db: Session, user_id: uuid.UUID, request: QueryRequest) -> QueryResponse:
    _ensure_user(db, user_id)
    if _is_small_talk(request.query):
        answer = _small_talk_answer(request.query)
        save_conversation(db, user_id, request.query, answer)
        return QueryResponse(answer=answer, sources=[])

    # 1. Embed query
    query_vector = create_embedding(request.query)

    # 2. Retrieve top-k from VectorDB, with graceful fallbacks for older/stale data.
    docs, ids, distances = _retrieve_from_chroma(user_id, query_vector)
    docs, ids, distances = _filter_docs_for_user(db, user_id, docs, ids, distances)

    if not docs:
        docs, ids, distances = _retrieve_from_database(db, user_id, request)

    if not docs:
        answer = call_llm(_build_general_prompt(request.query), request.query, [])
        save_conversation(db, user_id, request.query, answer)
        return QueryResponse(answer=answer, sources=[])

    has_meaningful_match = _has_meaningful_match(request.query, docs)

    # 3. Construct prompt
    llm_docs = docs if has_meaningful_match else []
    if has_meaningful_match:
        prompt = _build_notes_prompt(request.query, docs)
    else:
        prompt = _build_general_prompt(request.query)

    # 4. Generate answer with Gemini
    answer = call_llm(prompt, request.query, llm_docs)
    
    # 5. Connect Source objects
    sources = []
    if has_meaningful_match:
        for doc_id, doc_content, dist in zip(ids, docs, distances):
            sources.append(
                SourceNote(
                    id=doc_id,
                    content=doc_content,
                    similarity=_distance_to_similarity(dist)
                )
            )
        
    save_conversation(db, user_id, request.query, answer)
    
    return QueryResponse(answer=answer, sources=sources)

def call_llm(prompt: str, question: str, docs: list[str]) -> str:
    # Provider selection order:
    # - Fireworks when explicitly configured
    # - Groq when explicitly configured
    # - Gemini as the legacy fallback
    # - A gsk_* value in GEMINI_API_KEY is treated as a Groq key for compatibility
    fireworks_api_key = settings.FIREWORKS_API_KEY
    if not fireworks_api_key and settings.FIREWORKS_API_KEY is None and settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.startswith("fw_"):
        fireworks_api_key = settings.GEMINI_API_KEY

    if fireworks_api_key:
        fireworks_answer = _call_fireworks_llm(fireworks_api_key, prompt)
        if fireworks_answer:
            return fireworks_answer

    groq_api_key = settings.GROQ_API_KEY
    if not groq_api_key and settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.startswith("gsk_"):
        groq_api_key = settings.GEMINI_API_KEY

    if groq_api_key:
        groq_answer = _call_groq_llm(groq_api_key, prompt)
        if groq_answer:
            return groq_answer

    if not settings.GEMINI_API_KEY:
        print("Warning: No LLM API key set. Using fallback.")
        return _build_fallback_answer(question, docs)

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    last_error = None

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt,
            )
            if response.text and response.text.strip():
                return response.text.strip()
        except Exception as exc:
            last_error = exc
            error_text = str(exc)
            print(f"Error calling Gemini on attempt {attempt + 1}: {error_text}")
            if "RESOURCE_EXHAUSTED" in error_text or "quota" in error_text.lower():
                break
            if attempt < 2:
                time.sleep(1.5 * (attempt + 1))

    if last_error:
        print(f"Gemini failed after retries: {last_error}")
    return _build_fallback_answer(question, docs)


def _call_groq_llm(api_key: str, prompt: str) -> str | None:
    last_error = None
    for attempt in range(3):
        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.GROQ_MODEL,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.2,
                },
                timeout=25,
            )

            if response.status_code >= 400:
                raise RuntimeError(f"HTTP {response.status_code}: {response.text[:500]}")

            payload = response.json()
            choices = payload.get("choices") or []
            if choices:
                content = choices[0].get("message", {}).get("content")
                if isinstance(content, str) and content.strip():
                    return content.strip()
        except Exception as exc:
            last_error = exc
            error_text = str(exc)
            print(f"Error calling Groq on attempt {attempt + 1}: {error_text}")
            if "429" in error_text or "quota" in error_text.lower() or "rate" in error_text.lower():
                break
            if attempt < 2:
                time.sleep(1.0 * (attempt + 1))

    if last_error:
        print(f"Groq failed after retries: {last_error}")
    return None


def _call_fireworks_llm(api_key: str, prompt: str) -> str | None:
    last_error = None
    for attempt in range(3):
        try:
            response = requests.post(
                "https://api.fireworks.ai/inference/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.FIREWORKS_MODEL,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.2,
                },
                timeout=25,
            )

            if response.status_code >= 400:
                raise RuntimeError(f"HTTP {response.status_code}: {response.text[:500]}")

            payload = response.json()
            choices = payload.get("choices") or []
            if choices:
                content = choices[0].get("message", {}).get("content")
                if isinstance(content, str) and content.strip():
                    return content.strip()
        except Exception as exc:
            last_error = exc
            error_text = str(exc)
            print(f"Error calling Fireworks on attempt {attempt + 1}: {error_text}")
            if "429" in error_text or "quota" in error_text.lower() or "rate" in error_text.lower():
                break
            if attempt < 2:
                time.sleep(1.0 * (attempt + 1))

    if last_error:
        print(f"Fireworks failed after retries: {last_error}")
    return None

def save_conversation(db: Session, user_id: uuid.UUID, query: str, response: str):
    try:
        convo = Conversation(user_id=user_id, query=query, response=response)
        db.add(convo)
        db.commit()
    except Exception:
        db.rollback()
