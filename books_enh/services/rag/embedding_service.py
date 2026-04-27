"""
Embedding Service
─────────────────
Backend-agnostic factory around any LangChain ``Embeddings`` implementation.

The concrete provider is selected via ``settings.EMBEDDING_PROVIDER``
(e.g. ``openai``, ``huggingface``, ``cohere``).  Adding a new provider is
a one-line change in :func:`_build_embeddings` — the rest of the RAG
pipeline talks to the abstract ``Embeddings`` interface and is unaffected.
"""
import logging

from pydantic import SecretStr
from langchain_core.embeddings import Embeddings

from core.config import settings
from core.exceptions import EmbeddingConfigurationException

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Thin, reusable wrapper around the configured embedding model."""

    def __init__(
        self,
        embeddings: Embeddings | None = None,
    ) -> None:
        # Allow callers (tests, alternate providers) to inject a ready
        # Embeddings instance; otherwise build one from settings.
        self._embeddings: Embeddings = embeddings or self._build_embeddings()
        logger.info(
            "EmbeddingService initialised  provider=%s  model=%s",
            settings.EMBEDDING_PROVIDER,
            settings.EMBEDDING_MODEL,
        )

    # -- factory -------------------------------------------------------

    @staticmethod
    def _build_embeddings() -> Embeddings:
        provider = (settings.EMBEDDING_PROVIDER or "openai").lower()
        api_key = settings.EMBEDDING_API_KEY or settings.LLM_API_KEY

        if provider == "openai":
            if not api_key:
                raise EmbeddingConfigurationException(
                    "No embedding API key configured. "
                    "Set EMBEDDING_API_KEY or LLM_API_KEY in .env"
                )
            from langchain_openai import OpenAIEmbeddings
            return OpenAIEmbeddings(
                model=settings.EMBEDDING_MODEL,
                api_key=SecretStr(api_key),
                base_url=settings.EMBEDDING_BASE_URL,
                dimensions=settings.EMBEDDING_DIMENSIONS,
            )

        if provider == "huggingface":
            try:
                from langchain_huggingface import HuggingFaceEmbeddings
            except ImportError as exc:
                raise EmbeddingConfigurationException(
                    "langchain-huggingface is not installed"
                ) from exc
            return HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL)

        raise EmbeddingConfigurationException(
            f"Unsupported EMBEDDING_PROVIDER: {provider!r}"
        )

    # -- public helpers ------------------------------------------------

    @property
    def embeddings(self) -> Embeddings:
        """Return the underlying LangChain Embeddings instance."""
        return self._embeddings

    def embed_query(self, text: str) -> list[float]:
        """Embed a single search query."""
        return self._embeddings.embed_query(text)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of document texts."""
        return self._embeddings.embed_documents(texts)
