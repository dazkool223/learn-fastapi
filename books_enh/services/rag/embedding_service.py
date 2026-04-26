"""
Embedding Service
─────────────────
Wraps ``langchain_openai.OpenAIEmbeddings`` and exposes helpers used
by both the ingestion pipeline (embed_documents) and the query path
(embed_query).

The service reads its configuration from ``core.config.settings``:
- EMBEDDING_API_KEY  (falls back to LLM_API_KEY)
- EMBEDDING_MODEL    (default: text-embedding-3-small)
- EMBEDDING_BASE_URL (default: https://api.openai.com/v1)
- EMBEDDING_DIMENSIONS (default: 1536)
"""
import logging

from pydantic import SecretStr
from langchain_openai import OpenAIEmbeddings

from core.config import settings
from core.exceptions import EmbeddingConfigurationException

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Thin, reusable wrapper around the embedding model."""

    def __init__(self) -> None:
        api_key = settings.EMBEDDING_API_KEY or settings.LLM_API_KEY
        if not api_key:
            raise EmbeddingConfigurationException(
                "No embedding API key configured. "
                "Set EMBEDDING_API_KEY or LLM_API_KEY in .env"
            )

        self._embeddings = OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            api_key=SecretStr(api_key),
            base_url=settings.EMBEDDING_BASE_URL,
            dimensions=settings.EMBEDDING_DIMENSIONS,
        )
        logger.info(
            "EmbeddingService initialised  model=%s  dims=%d",
            settings.EMBEDDING_MODEL,
            settings.EMBEDDING_DIMENSIONS,
        )

    # -- public helpers ------------------------------------------------

    @property
    def embeddings(self) -> OpenAIEmbeddings:
        """Return the underlying LangChain Embeddings instance."""
        return self._embeddings

    def embed_query(self, text: str) -> list[float]:
        """Embed a single search query."""
        return self._embeddings.embed_query(text)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of document texts."""
        return self._embeddings.embed_documents(texts)
