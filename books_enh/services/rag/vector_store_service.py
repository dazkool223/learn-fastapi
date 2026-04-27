"""
Supabase pgvector Vector Store
──────────────────────────────
Concrete :class:`~services.rag.protocols.VectorStore` implementation
backed by Supabase pgvector through LangChain's ``SupabaseVectorStore``.

Design notes
------------
* The underlying ``SupabaseVectorStore`` is built **once** and cached on
  the instance – previously a fresh wrapper was instantiated on every
  call which is wasteful (each one allocates a LangChain runtime, etc.).
* The Supabase ``Client`` is **injected** (typically via
  :class:`SupabaseStorageService.client`) so the application authenticates
  with Supabase exactly once instead of duplicating ``create_client``
  calls in every Supabase-backed service.
* All I/O is wrapped in error handling that surfaces a domain-level
  ``RAGIngestionException`` / ``RAGQueryException`` – the orchestration
  layer no longer has to guess where a failure came from.
"""
import json
import logging
from typing import Optional

from langchain_core.documents import Document
from langchain_community.vectorstores import SupabaseVectorStore
from supabase import Client

from core.config import settings
from core.exceptions import RAGIngestionException, RAGQueryException
from services.rag.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class SupabaseVectorStoreService:
    """
    Implements :class:`services.rag.protocols.VectorStore` against
    Supabase pgvector.
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        client: Client,
    ) -> None:
        self._client: Client = client
        self._embedding_service = embedding_service
        self._table_name = settings.VECTOR_TABLE_NAME
        self._query_function = settings.VECTOR_QUERY_FUNCTION
        # Cache: SupabaseVectorStore is a thin stateless wrapper but
        # constructing it allocates LangChain runtime objects, so we
        # keep a single instance per service.
        self._store: SupabaseVectorStore | None = None

    # -- helpers -------------------------------------------------------

    def _get_store(self) -> SupabaseVectorStore:
        if self._store is None:
            self._store = SupabaseVectorStore(
                client=self._client,
                embedding=self._embedding_service.embeddings,
                table_name=self._table_name,
                query_name=self._query_function,
            )
        return self._store

    # -- write ---------------------------------------------------------

    def add_documents(
        self,
        documents: list[Document],
        batch_size: int = 100,
    ) -> int:
        """
        Embed and insert *documents* into the vector store in batches.

        NOTE: ``SupabaseVectorStore.add_documents`` performs INSERTs with
        freshly generated UUIDs – it does *not* upsert by metadata. That
        is why callers must explicitly :meth:`delete_by_book_id` before
        re-ingesting an existing book; otherwise old chunks remain in
        place alongside the new ones and pollute retrieval results.
        """
        store = self._get_store()
        total_added = 0

        try:
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
        except Exception as exc:
            logger.exception("Vector store insert failed")
            raise RAGIngestionException(
                f"Failed to store embeddings: {exc}"
            ) from exc

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
        """
        try:
            store = self._get_store()
            return store.similarity_search_with_relevance_scores(
                query=query,
                k=top_k,
                filter=filter or {},
            )
        except Exception as exc:
            logger.exception("Vector similarity search failed")
            raise RAGQueryException(
                f"Vector store query failed: {exc}"
            ) from exc

    # -- delete --------------------------------------------------------

    def delete_by_book_id(self, book_id: int) -> None:
        """Remove every chunk that belongs to *book_id*."""
        try:
            self._client.table(self._table_name).delete().filter(
                "metadata", "cs", json.dumps({"book_id": book_id}),
            ).execute()
            logger.info("Deleted all chunks for book %d", book_id)
        except Exception as exc:
            logger.exception("Vector store delete failed")
            raise RAGIngestionException(
                f"Failed to delete chunks for book {book_id}: {exc}"
            ) from exc
