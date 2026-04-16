from functools import lru_cache

try:
    import whisper
except Exception:  # pragma: no cover - optional dependency fallback
    whisper = None

@lru_cache(maxsize=1)
def get_whisper_model():
    if whisper is None:
        return None
    return whisper.load_model("base")


def is_voice_available() -> bool:
    return get_whisper_model() is not None

def transcribe_audio(file_path: str) -> str:
    """Uses Whisper to transcribe an audio file to text."""
    model = get_whisper_model()
    if model is None:
        raise RuntimeError("Voice transcription is unavailable because Whisper is not installed.")
    result = model.transcribe(file_path)
    return result["text"]
