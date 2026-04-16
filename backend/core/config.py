from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]

class Settings(BaseSettings):
    PROJECT_NAME: str = "Second Brain AI API"
    API_V1_STR: str = "/api"
    DATABASE_URL: str = "postgresql+psycopg2://admin:password@localhost:5432/secondbrain"
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8000
    OLLAMA_BASE_URL: str = "http://localhost:11434" # Assuming local ollama
    GEMINI_API_KEY: str | None = None
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GROQ_API_KEY: str | None = None
    GROQ_MODEL: str = "llama-3.1-8b-instant"
    FIREWORKS_API_KEY: str | None = None
    FIREWORKS_MODEL: str = "accounts/fireworks/models/llama-v3p1-8b-instruct"
    ALLOW_GENERAL_ANSWER_WITHOUT_NOTES: bool = True
    ENABLE_RESURFACING_JOB: bool = False
    SECRET_KEY: str = Field(
        default="change-this-in-production-second-brain-secret",
        min_length=32,
    )
    SESSION_TTL_SECONDS: int = 60 * 60 * 24 * 30
    CORS_ALLOWED_ORIGINS: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:3001"]
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
    )

    @field_validator("CORS_ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, list):
            return value
        return _split_csv(value)

settings = Settings()
