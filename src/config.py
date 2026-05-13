import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # LLM
    GROQ_API_KEY: str
    CONTEXT_MODEL: str = "llama-3.1-8b-instant"
    AGENT_MODEL: str = "llama-3.3-70b-versatile"

    # Qdrant
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_COLLECTION: str = "accounting_kb"

    # Models
    DENSE_MODEL: str = "BAAI/bge-small-en-v1.5"
    SPARSE_MODEL: str = "Qdrant/bm25"

    # Retrieval
    HYBRID_TOP_K: int = 20
    RERANK_TOP_K: int = 5
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50

settings = Settings()
