"""
Vector Store Service
────────────────────
Manages the Supabase pgvector-backed vector store through LangChain's
``SupabaseVectorStore``.

Responsibilities:
* Batch-insert document chunks with their embeddings.
* Similarity search with optional JSONB metadata filtering.
* Delete all chunks belonging to a specific book (re-ingestion).
"""
import json
import logging
from typing import Optional

from langchain_core.documents import Document
from langchain_community.vectorstores import SupabaseVectorStore
from supabase import create_client, Client

from core.config import settings
from services.rag.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class VectorStoreService:
    """All vector-store I/O in one place."""

    def __init__(self, embedding_service: EmbeddingService) -> None:
        self._client: Client = create_client(
            settings.STORAGE_URL,
            settings.STORAGE_ACCOUNT_SECRET,
        )
        self._embedding_service = embedding_service
        self._table_name = settings.VECTOR_TABLE_NAME
        self._query_function = settings.VECTOR_QUERY_FUNCTION

    # -- helpers -------------------------------------------------------

    def _get_store(self) -> SupabaseVectorStore:
        return SupabaseVectorStore(
            client=self._client,
            embedding=self._embedding_service.embeddings,
            table_name=self._table_name,
            query_name=self._query_function,
        )

    # -- write ---------------------------------------------------------

    def add_documents(
        self,
        documents: list[Document],
        batch_size: int = 100,
    ) -> int:
        """
        Embed and upsert *documents* into the vector store.

        Processing is done in batches of *batch_size* to respect
        embedding API rate limits and Supabase payload limits.
        Returns the total number of chunks stored.
        """
        store = self._get_store()
        total_added = 0

        for i in range(0, len(documents), batch_size):
            batch = documents[i : i + batch_size]
            store.add_documents(batch)
            total_added += len(batch)
            logger.info(
                "Stored batch %d: %d / %d chunks",
                i // batch_size + 1,
                total_added,
                len(documents),
            )

        return total_added

    # -- read ----------------------------------------------------------

    def similarity_search(
        self,
        query: str,
        top_k: int = 5,
        filter: Optional[dict] = None,
    ) -> list[tuple[Document, float]]:
        """
        Embed *query* and return the *top_k* most similar chunks
        together with their cosine-similarity scores.

        *filter* is a JSONB containment filter, e.g.
        ``{"book_id": 42}`` restricts results to that book.
        """
        store = self._get_store()
        return store.similarity_search_with_relevance_scores(
            query=query,
            k=top_k,
            filter=filter or {},
        )

    # -- delete --------------------------------------------------------

    def delete_by_book_id(self, book_id: int) -> None:
        """Remove every chunk that belongs to *book_id*."""
        self._client.table(self._table_name).delete().filter(
            "metadata", "cs", json.dumps({"book_id": book_id}),
        ).execute()
        logger.info("Deleted all chunks for book %d", book_id)
