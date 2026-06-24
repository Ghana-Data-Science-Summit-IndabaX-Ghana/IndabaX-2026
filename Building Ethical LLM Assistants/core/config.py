import os
from dotenv import load_dotenv

load_dotenv()

MOCK_MODE: bool = os.getenv("MOCK_MODE", "true").lower() in ("true", "1", "yes")
DEFAULT_PROVIDER: str = os.getenv("DEFAULT_PROVIDER", "anthropic")
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")

DEFAULT_RETRIEVER: str = os.getenv("DEFAULT_RETRIEVER", "keyword").lower()
CHROMA_DIR: str = os.getenv("CHROMA_DIR", ".chroma")
EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
